"""Tests for restaurant repository (Phase 1)."""

from pathlib import Path

import pandas as pd
import pytest

from src.data.repository import RestaurantRepository


@pytest.fixture
def parquet_path(tmp_path: Path) -> Path:
    df = pd.DataFrame(
        {
            "id": ["r_1", "r_2"],
            "name": ["A", "B"],
            "location": ["Bangalore", "Delhi"],
            "cuisine": ["Italian", "Chinese"],
            "rating": [4.5, 4.0],
            "cost": [500.0, None],
            "budget_band": ["low", "medium"],
        }
    )
    path = tmp_path / "restaurants.parquet"
    df.to_parquet(path, index=False)
    return path


def test_load_and_locations(parquet_path: Path):
    repo = RestaurantRepository()
    repo.load(parquet_path)
    assert repo.count() == 2
    assert repo.get_locations() == ["Bangalore", "Delhi"]
    assert repo.all()[0].cost == 500.0
    assert repo.all()[1].cost is None


def test_missing_file(tmp_path: Path):
    repo = RestaurantRepository()
    with pytest.raises(FileNotFoundError):
        repo.load(tmp_path / "missing.parquet")
