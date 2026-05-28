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
    ) -> FilterResult:
        cap = max_candidates if max_candidates is not None else self.max_candidates
        target_location = normalize_city(preferences.location)

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

        matched.sort(key=lambda r: r.rating, reverse=True)
        total_matched = len(matched)
        candidates = matched[:cap]

        filters_applied = {
            "location": target_location,
            "budget": preferences.budget,
            "cuisine": preferences.cuisine,
            "min_rating": preferences.min_rating,
        }

        logger.info(
            "Filter: %d matched, %d candidates (cap=%d) for location=%s",
            total_matched,
            len(candidates),
            cap,
            target_location,
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
