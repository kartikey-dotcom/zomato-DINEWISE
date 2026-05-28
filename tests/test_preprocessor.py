"""Tests for data preprocessing (Phase 1)."""

import pandas as pd
import pytest

from src.data.preprocessor import (
    assign_budget_bands,
    normalize_city,
    parse_cost,
    parse_rating,
    preprocess,
)


class TestNormalizeCity:
    def test_bengaluru_alias(self):
        assert normalize_city("Bengaluru") == "Bangalore"

    def test_case_insensitive(self):
        assert normalize_city("bangalore") == "Bangalore"

    def test_title_case_unknown(self):
        assert normalize_city("jaipur") == "Jaipur"

    def test_empty(self):
        assert normalize_city("") == ""
        assert normalize_city(None) == ""


class TestParseRating:
    def test_float(self):
        assert parse_rating(4.5) == 4.5

    def test_slash_format(self):
        assert parse_rating("4.1/5") == 4.1

    def test_invalid(self):
        assert parse_rating("-") is None
        assert parse_rating("NEW") is None

    def test_clamp_high(self):
        assert parse_rating(6.0) == 5.0


class TestParseCost:
    def test_integer_string(self):
        assert parse_cost("800") == 800.0

    def test_with_commas(self):
        assert parse_cost("1,200") == 1200.0

    def test_rupees_text(self):
        assert parse_cost("₹300 for two") == 300.0

    def test_invalid(self):
        assert parse_cost("-") is None
        assert parse_cost("") is None


class TestAssignBudgetBands:
    def test_three_tiers(self):
        costs = pd.Series([100, 200, 300, 400, 500, 600])
        bands = assign_budget_bands(costs)
        assert set(bands.unique()) <= {"low", "medium", "high"}

    def test_single_value_defaults_medium(self):
        costs = pd.Series([500, 500, 500])
        bands = assign_budget_bands(costs)
        assert (bands == "medium").all()


class TestPreprocess:
    @pytest.fixture
    def sample_raw(self) -> pd.DataFrame:
        rows = []
        cities = ["Bengaluru", "Delhi", "Mumbai", "Pune", "Hyderabad"]
        for i in range(12):
            rows.append(
                {
                    "name": f"Restaurant {i}" if i != 1 else "Cafe A",
                    "location": cities[i % len(cities)] if i != 2 else "Bengaluru",
                    "cuisine": "Italian" if i % 2 == 0 else "Chinese",
                    "rating": f"{3.5 + (i % 3) * 0.5}/5",
                    "cost": str(400 + i * 100),
                }
            )
        # Duplicate Cafe A in Bengaluru for dedupe test
        rows[1] = {
            "name": "Cafe A",
            "location": "Bengaluru",
            "cuisine": "Italian",
            "rating": "4.0/5",
            "cost": "600",
        }
        rows[0] = {
            "name": "Cafe A",
            "location": "Bengaluru",
            "cuisine": "Italian",
            "rating": "4.5/5",
            "cost": "500",
        }
        rows.append(
            {
                "name": "No City",
                "location": "",
                "cuisine": "Indian",
                "rating": "4.0/5",
                "cost": "300",
            }
        )
        return pd.DataFrame(rows)

    def test_required_columns_present(self, sample_raw):
        result = preprocess(sample_raw)
        assert list(result.columns) == [
            "id",
            "name",
            "location",
            "cuisine",
            "rating",
            "cost",
            "budget_band",
        ]

    def test_deduplication_keeps_higher_rating(self, sample_raw):
        result = preprocess(sample_raw)
        cafe = result[result["name"] == "Cafe A"]
        assert len(cafe) == 1
        assert cafe.iloc[0]["rating"] == 4.5
        assert cafe.iloc[0]["location"] == "Bangalore"

    def test_drops_missing_location(self, sample_raw):
        result = preprocess(sample_raw)
        assert "No City" not in result["name"].values

    def test_budget_band_values(self, sample_raw):
        result = preprocess(sample_raw)
        assert set(result["budget_band"].unique()) <= {"low", "medium", "high"}
