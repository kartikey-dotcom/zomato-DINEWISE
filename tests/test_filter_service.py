"""Tests for filter service (Phase 2)."""

import pytest

from src.models.preferences import UserPreferences
from src.models.restaurant import Restaurant
from src.services.filter_service import FilterService, to_candidate_dicts


def _restaurant(
    id: str,
    name: str,
    location: str,
    cuisine: str,
    rating: float,
    budget_band: str = "medium",
    cost: float | None = 500.0,
) -> Restaurant:
    return Restaurant(
        id=id,
        name=name,
        location=location,
        cuisine=cuisine,
        rating=rating,
        cost=cost,
        budget_band=budget_band,  # type: ignore[arg-type]
    )


@pytest.fixture
def sample_restaurants() -> list[Restaurant]:
    return [
        _restaurant("r1", "Italian Place", "Bangalore", "Italian, Pizza", 4.5, "medium"),
        _restaurant("r2", "Chinese Wok", "Bangalore", "Chinese", 4.2, "low"),
        _restaurant("r3", "Fine Dine", "Bangalore", "French", 4.8, "high"),
        _restaurant("r4", "Delhi Dhaba", "Delhi", "North Indian", 4.0, "low"),
        _restaurant("r5", "Low Rated", "Bangalore", "Italian", 3.0, "medium"),
        _restaurant("r6", "Bengaluru Cafe", "Bengaluru", "Cafe", 4.1, "medium"),
    ]


@pytest.fixture
def filter_service() -> FilterService:
    return FilterService(max_candidates=30)


class TestFilterService:
    def test_location_only(self, filter_service, sample_restaurants):
        prefs = UserPreferences(location="Bangalore", budget="medium", min_rating=0.0)
        result = filter_service.filter(prefs, sample_restaurants)
        names = {r.name for r in result.candidates}
        assert "Italian Place" in names
        assert "Delhi Dhaba" not in names
        assert "Bengaluru Cafe" in names  # alias match

    def test_location_and_min_rating(self, filter_service, sample_restaurants):
        prefs = UserPreferences(location="Bangalore", budget="medium", min_rating=4.0)
        result = filter_service.filter(prefs, sample_restaurants)
        assert all(r.rating >= 4.0 for r in result.candidates)
        assert "Low Rated" not in {r.name for r in result.candidates}

    def test_location_and_budget(self, filter_service, sample_restaurants):
        prefs = UserPreferences(location="Bangalore", budget="low", min_rating=0.0)
        result = filter_service.filter(prefs, sample_restaurants)
        assert all(r.budget_band == "low" for r in result.candidates)
        assert len(result.candidates) == 1
        assert result.candidates[0].name == "Chinese Wok"

    def test_cuisine_substring(self, filter_service, sample_restaurants):
        prefs = UserPreferences(
            location="Bangalore",
            budget="medium",
            cuisine="italian",
            min_rating=0.0,
        )
        result = filter_service.filter(prefs, sample_restaurants)
        names = {r.name for r in result.candidates}
        assert "Italian Place" in names
        assert "Fine Dine" not in names

    def test_no_matches(self, filter_service, sample_restaurants):
        prefs = UserPreferences(
            location="Bangalore",
            budget="high",
            cuisine="Ethiopian",
            min_rating=4.5,
        )
        result = filter_service.filter(prefs, sample_restaurants)
        assert result.candidates == []
        assert result.total_matched == 0

    def test_candidate_cap(self, sample_restaurants):
        service = FilterService(max_candidates=2)
        prefs = UserPreferences(location="Bangalore", budget="medium", min_rating=0.0)
        result = service.filter(prefs, sample_restaurants)
        assert len(result.candidates) == 2
        assert result.total_matched >= 2
        assert result.candidates[0].rating >= result.candidates[1].rating

    def test_rating_boundary_inclusive(self, filter_service, sample_restaurants):
        prefs = UserPreferences(location="Bangalore", budget="medium", min_rating=4.1)
        result = filter_service.filter(prefs, sample_restaurants)
        assert any(r.name == "Bengaluru Cafe" for r in result.candidates)

    def test_invalid_budget_rejected(self):
        with pytest.raises(Exception):
            UserPreferences(location="Delhi", budget="cheap")  # type: ignore[arg-type]

    def test_filters_applied_metadata(self, filter_service, sample_restaurants):
        prefs = UserPreferences(
            location="bengaluru",
            budget="medium",
            cuisine="Italian",
            min_rating=3.5,
        )
        result = filter_service.filter(prefs, sample_restaurants)
        assert result.filters_applied["location"] == "Bangalore"
        assert result.filters_applied["budget"] == "medium"
        assert result.filters_applied["cuisine"] == "Italian"


class TestToCandidateDicts:
    def test_shape(self, sample_restaurants):
        dicts = to_candidate_dicts(sample_restaurants[:2])
        assert len(dicts) == 2
        assert set(dicts[0].keys()) == {"id", "name", "location", "cuisine", "rating", "cost"}

    def test_deduplicates_ids(self):
        r = _restaurant("r1", "A", "Bangalore", "X", 4.0)
        dicts = to_candidate_dicts([r, r])
        assert len(dicts) == 1


class TestUserPreferences:
    def test_rejects_empty_location(self):
        with pytest.raises(ValueError, match="Location"):
            UserPreferences(location="  ", budget="medium")

    def test_normalizes_location(self):
        prefs = UserPreferences(location="bengaluru", budget="medium")
        assert prefs.location == "Bangalore"

    def test_blank_cuisine_becomes_none(self):
        prefs = UserPreferences(location="Delhi", budget="low", cuisine="  ")
        assert prefs.cuisine is None

    def test_clamps_min_rating(self):
        prefs = UserPreferences(location="Delhi", budget="low", min_rating=99.0)
        assert prefs.min_rating == 5.0
