"""Load and query processed restaurant data from local cache."""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from src.models.restaurant import Restaurant

logger = logging.getLogger(__name__)


def _record_to_restaurant(row: dict) -> Restaurant:
    if row.get("cost") is not None and pd.isna(row["cost"]):
        row = {**row, "cost": None}
    return Restaurant.model_validate(row)


class RestaurantRepository:
    """In-memory store of normalized restaurants loaded from parquet."""

    def __init__(self) -> None:
        self._restaurants: list[Restaurant] = []

    @property
    def is_loaded(self) -> bool:
        return len(self._restaurants) > 0

    def load(self, path: Path) -> None:
        """Read parquet and populate in-memory list."""
        if not path.exists():
            raise FileNotFoundError(
                f"Processed dataset not found at {path}. "
                "Run: python -m src.data.run_pipeline"
            )

        df = pd.read_parquet(path)
        required = {"id", "name", "location", "cuisine", "rating", "budget_band"}
        missing = required - set(df.columns)
        if missing:
            raise ValueError(f"Processed dataset missing columns: {missing}")

        records = df.to_dict("records")
        self._restaurants = [_record_to_restaurant(row) for row in records]
        logger.info("Loaded %d restaurants from %s", len(self._restaurants), path)

    def all(self) -> list[Restaurant]:
        return list(self._restaurants)

    def get_locations(self) -> list[str]:
        """Distinct cities for UI dropdown, sorted alphabetically."""
        locations = sorted({r.location for r in self._restaurants if r.location})
        return locations

    def count(self) -> int:
        return len(self._restaurants)
