"""Merge LLM rankings with restaurant records."""

from __future__ import annotations

from src.models.recommendation import RecommendationItem
from src.models.restaurant import Restaurant


def _format_cost(cost: float | None) -> str | float:
    if cost is None:
        return "Cost not available"
    return cost


def merge_recommendations(
    llm_items: list[dict],
    candidates: list[Restaurant],
) -> list[RecommendationItem]:
    """Join LLM id + explanation with candidate rows for full output contract."""
    by_id = {r.id: r for r in candidates}
    merged: list[RecommendationItem] = []

    for item in llm_items:
        rid = str(item.get("id", ""))
        restaurant = by_id.get(rid)
        if restaurant is None:
            continue
        explanation = (item.get("explanation") or "").strip()
        if not explanation:
            explanation = "Matches your preferences based on rating and filters."

        merged.append(
            RecommendationItem(
                rank=int(item.get("rank", len(merged) + 1)),
                name=restaurant.name,
                cuisine=restaurant.cuisine,
                rating=restaurant.rating,
                estimated_cost=_format_cost(restaurant.cost),
                explanation=explanation,
            )
        )

    return merged


def fallback_recommendations(
    candidates: list[Restaurant],
    top_n: int = 5,
) -> list[RecommendationItem]:
    """Rating-sorted fallback when LLM is unavailable."""
    sorted_candidates = sorted(candidates, key=lambda r: r.rating, reverse=True)[:top_n]
    message = (
        "Ranked by rating among restaurants matching your filters. "
        "AI explanations are temporarily unavailable."
    )
    return [
        RecommendationItem(
            rank=i,
            name=r.name,
            cuisine=r.cuisine,
            rating=r.rating,
            estimated_cost=_format_cost(r.cost),
            explanation=message,
        )
        for i, r in enumerate(sorted_candidates, start=1)
    ]
