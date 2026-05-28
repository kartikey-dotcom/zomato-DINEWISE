"""Tests for prompt builder."""

from src.models.preferences import UserPreferences
from src.models.restaurant import Restaurant
from src.services.prompt_builder import PromptBuilder


def _restaurant() -> Restaurant:
    return Restaurant(
        id="r1",
        name="Test Cafe",
        location="Bangalore",
        cuisine="Italian",
        rating=4.5,
        cost=500.0,
        budget_band="medium",
    )


def test_prompt_contains_constraints_and_candidates():
    prefs = UserPreferences(
        location="Bangalore",
        budget="medium",
        cuisine="Italian",
        min_rating=4.0,
        additional="family-friendly",
    )
    prompt = PromptBuilder(top_n=3).build(prefs, [_restaurant()])
    assert "Bangalore" in prompt
    assert "family-friendly" in prompt
    assert "CANDIDATES" in prompt
    assert "r1" in prompt
    assert "top 3" in prompt.lower()
    assert "JSON only" in prompt or "valid JSON" in prompt
