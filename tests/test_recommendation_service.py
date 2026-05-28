"""Tests for recommendation orchestrator."""

from unittest.mock import MagicMock

import pandas as pd
import pytest

from src.data.repository import RestaurantRepository
from src.models.preferences import UserPreferences
from src.models.restaurant import Restaurant
from src.services.filter_service import FilterService
from src.services.recommendation_service import RecommendationService


def _r(id: str, name: str, city: str, cuisine: str, rating: float, band: str = "medium") -> Restaurant:
    return Restaurant(
        id=id,
        name=name,
        location=city,
        cuisine=cuisine,
        rating=rating,
        cost=500.0,
        budget_band=band,  # type: ignore[arg-type]
    )


@pytest.fixture
def repo(tmp_path) -> RestaurantRepository:
    df = pd.DataFrame(
        [
            {
                "id": "r1",
                "name": "Italian Hub",
                "location": "Bangalore",
                "cuisine": "Italian",
                "rating": 4.5,
                "cost": 600.0,
                "budget_band": "medium",
            },
            {
                "id": "r2",
                "name": "Budget Bite",
                "location": "Bangalore",
                "cuisine": "Chinese",
                "rating": 4.0,
                "cost": 300.0,
                "budget_band": "low",
            },
        ]
    )
    path = tmp_path / "restaurants.parquet"
    df.to_parquet(path, index=False)
    repository = RestaurantRepository()
    repository.load(path)
    return repository


class TestRecommendationService:
    def test_empty_candidates_skips_llm(self, repo):
        llm = MagicMock()
        service = RecommendationService(
            repository=repo,
            filter_service=FilterService(),
            llm_client=llm,
            relax_if_empty=False,
        )
        prefs = UserPreferences(
            location="Bangalore",
            budget="high",
            cuisine="Ethiopian",
            min_rating=4.9,
        )
        response = service.get_recommendations(prefs)
        assert response.items == []
        assert "message" in response.metadata
        llm.complete.assert_not_called()

    def test_llm_success(self, repo):
        llm = MagicMock()
        llm.complete.return_value = """
        {
          "recommendations": [
            {"id": "r1", "rank": 1, "explanation": "Great Italian spot."}
          ],
          "summary": "Enjoy Italian in Bangalore."
        }
        """
        service = RecommendationService(
            repository=repo,
            filter_service=FilterService(),
            llm_client=llm,
        )
        prefs = UserPreferences(location="Bangalore", budget="medium", min_rating=4.0)
        response = service.get_recommendations(prefs)
        assert len(response.items) == 1
        assert response.items[0].name == "Italian Hub"
        assert response.items[0].explanation == "Great Italian spot."
        assert response.metadata["fallback"] is False

    def test_llm_failure_uses_fallback(self, repo):
        llm = MagicMock()
        llm.complete.side_effect = RuntimeError("API down")
        service = RecommendationService(
            repository=repo,
            filter_service=FilterService(),
            llm_client=llm,
        )
        prefs = UserPreferences(location="Bangalore", budget="medium", min_rating=4.0)
        response = service.get_recommendations(prefs)
        assert len(response.items) >= 1
        assert response.metadata["fallback"] is True

    def test_llm_parsing_failure_retries_once_and_succeeds(self, repo):
        llm = MagicMock()
        # First returns invalid JSON, second returns valid JSON
        llm.complete.side_effect = [
            "invalid raw text",
            """
            {
              "recommendations": [
                {"id": "r1", "rank": 1, "explanation": "Perfect match after retry."}
              ],
              "summary": "Retried successfully."
            }
            """
        ]
        service = RecommendationService(
            repository=repo,
            filter_service=FilterService(),
            llm_client=llm,
        )
        prefs = UserPreferences(location="Bangalore", budget="medium", min_rating=4.0)
        response = service.get_recommendations(prefs)

        assert llm.complete.call_count == 2
        # Verify first call and retry call with custom instructions
        calls = llm.complete.call_args_list
        assert "CRITICAL" in calls[1][0][0]
        
        assert len(response.items) == 1
        assert response.items[0].name == "Italian Hub"
        assert response.items[0].explanation == "Perfect match after retry."
        assert response.metadata["fallback"] is False

    def test_llm_parsing_failure_retries_once_and_fails_falls_back(self, repo):
        llm = MagicMock()
        # Both return invalid JSON
        llm.complete.side_effect = [
            "invalid raw text 1",
            "invalid raw text 2"
        ]
        service = RecommendationService(
            repository=repo,
            filter_service=FilterService(),
            llm_client=llm,
        )
        prefs = UserPreferences(location="Bangalore", budget="medium", min_rating=4.0)
        response = service.get_recommendations(prefs)

        assert llm.complete.call_count == 2
        assert len(response.items) >= 1
        assert response.metadata["fallback"] is True

