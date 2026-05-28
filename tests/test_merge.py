"""Tests for merge and fallback helpers."""

from src.models.restaurant import Restaurant
from src.services.merge import fallback_recommendations, merge_recommendations


def test_merge_recommendations():
    candidates = [
        Restaurant(
            id="r1",
            name="Cafe",
            location="Delhi",
            cuisine="Italian",
            rating=4.5,
            cost=800.0,
            budget_band="medium",
        )
    ]
    items = merge_recommendations(
        [{"id": "r1", "rank": 1, "explanation": "Perfect match."}],
        candidates,
    )
    assert items[0].name == "Cafe"
    assert items[0].estimated_cost == 800.0
    assert items[0].rank == 1


def test_fallback_recommendations():
    candidates = [
        Restaurant(
            id="r1",
            name="A",
            location="Delhi",
            cuisine="X",
            rating=3.0,
            budget_band="low",
        ),
        Restaurant(
            id="r2",
            name="B",
            location="Delhi",
            cuisine="Y",
            rating=5.0,
            budget_band="low",
        ),
    ]
    items = fallback_recommendations(candidates, top_n=1)
    assert len(items) == 1
    assert items[0].name == "B"
    assert "unavailable" in items[0].explanation.lower()
