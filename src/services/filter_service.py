"""Deterministic restaurant filtering and candidate preparation."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from src.data.preprocessor import normalize_city
from src.models.preferences import UserPreferences
from src.models.restaurant import Restaurant

logger = logging.getLogger(__name__)


@dataclass
class FilterResult:
    """Filtered candidates plus diagnostics for orchestration / metadata."""

    candidates: list[Restaurant]
    total_matched: int
    filters_applied: dict[str, str | float | None]


def to_candidate_dicts(restaurants: list[Restaurant]) -> list[dict]:
    """Serialize restaurants for LLM prompt embedding."""
    seen: set[str] = set()
    payload: list[dict] = []

    for restaurant in restaurants:
        if restaurant.id in seen:
            continue
        seen.add(restaurant.id)
        payload.append(
            {
                "id": restaurant.id,
                "name": restaurant.name,
                "location": restaurant.location,
                "cuisine": restaurant.cuisine,
                "rating": restaurant.rating,
                "cost": restaurant.cost,
            }
        )
    return payload


class FilterService:
    """Apply hard filters before LLM ranking."""

    def __init__(self, max_candidates: int = 30) -> None:
        self.max_candidates = max_candidates

    def filter(
        self,
        preferences: UserPreferences,
        restaurants: list[Restaurant],
        max_candidates: int | None = None,
        relax_if_empty: bool = False,
    ) -> FilterResult:
        cap = max_candidates if max_candidates is not None else self.max_candidates
        target_location = normalize_city(preferences.location)

        # Stage 1: Try strict matching
        matched: list[Restaurant] = []
        for restaurant in restaurants:
            if not self._matches_location(restaurant, target_location):
                continue
            if round(restaurant.rating, 2) < round(preferences.min_rating, 2):
                continue
            if not self._matches_cuisine(restaurant, preferences.cuisine):
                continue
            if restaurant.budget_band != preferences.budget:
                continue
            matched.append(restaurant)

        relaxed_message = None

        # Stage 2: Progressive Relaxation (only if relax_if_empty=True and we have < 2 matches)
        if relax_if_empty and len(matched) < 2:
            # 1. Try relaxing cuisine first (if set)
            if preferences.cuisine:
                cuisine_relaxed = []
                for restaurant in restaurants:
                    if not self._matches_location(restaurant, target_location):
                        continue
                    if round(restaurant.rating, 2) < round(preferences.min_rating, 2):
                        continue
                    if restaurant.budget_band != preferences.budget:
                        continue
                    cuisine_relaxed.append(restaurant)
                if len(cuisine_relaxed) >= 2:
                    matched = cuisine_relaxed
                    relaxed_message = f"No perfect matches for cuisine '{preferences.cuisine}'. Showing other cuisines in {target_location}."

            # 2. Try relaxing rating (drop rating constraint)
            if len(matched) < 2:
                rating_relaxed = []
                for restaurant in restaurants:
                    if not self._matches_location(restaurant, target_location):
                        continue
                    if not self._matches_cuisine(restaurant, preferences.cuisine):
                        continue
                    if restaurant.budget_band != preferences.budget:
                        continue
                    rating_relaxed.append(restaurant)
                if len(rating_relaxed) >= 2:
                    matched = rating_relaxed
                    relaxed_message = f"No matches rated >= {preferences.min_rating}★. Showing best available options in {target_location}."

            # 3. Try relaxing both rating and cuisine
            if len(matched) < 2:
                both_relaxed = []
                for restaurant in restaurants:
                    if not self._matches_location(restaurant, target_location):
                        continue
                    if restaurant.budget_band != preferences.budget:
                        continue
                    both_relaxed.append(restaurant)
                if len(both_relaxed) >= 2:
                    matched = both_relaxed
                    relaxed_message = f"Showing options in {target_location} with relaxed constraints."

            # 4. Absolute fallback: Return ALL restaurants in that location, sorted by rating desc
            if len(matched) < 2:
                all_in_location = [r for r in restaurants if self._matches_location(r, target_location)]
                if all_in_location:
                    matched = all_in_location
                    relaxed_message = f"Showing all available restaurants in {target_location} sorted by rating."

        matched.sort(key=lambda r: r.rating, reverse=True)
        total_matched = len(matched)
        candidates = matched[:cap]

        filters_applied = {
            "location": target_location,
            "budget": preferences.budget,
            "cuisine": preferences.cuisine,
            "min_rating": preferences.min_rating,
        }
        if relaxed_message:
            filters_applied["relaxed_message"] = relaxed_message

        logger.info(
            "Filter: %d matched, %d candidates (cap=%d) for location=%s (relaxed=%s)",
            total_matched,
            len(candidates),
            cap,
            target_location,
            relaxed_message is not None,
        )

        return FilterResult(
            candidates=candidates,
            total_matched=total_matched,
            filters_applied=filters_applied,
        )

    @staticmethod
    def _matches_location(restaurant: Restaurant, target_location: str) -> bool:
        return normalize_city(restaurant.location).lower() == target_location.lower()

    @staticmethod
    def _matches_cuisine(restaurant: Restaurant, cuisine: str | None) -> bool:
        if cuisine is None:
            return True
        return cuisine.lower() in restaurant.cuisine.lower()
