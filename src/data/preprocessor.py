"""Clean, normalize, and enrich restaurant records."""

from __future__ import annotations

import hashlib
import logging
import re
from typing import Literal

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

CITY_ALIASES: dict[str, str] = {
    "bengaluru": "Bangalore",
    "bangalore": "Bangalore",
    "banglore": "Bangalore",
    "new delhi": "Delhi",
    "delhi ncr": "Delhi",
    "delhi-ncr": "Delhi",
    "gurugram": "Gurgaon",
    "gurgaon": "Gurgaon",
    "mumbai": "Mumbai",
    "bombay": "Mumbai",
    "kolkata": "Kolkata",
    "calcutta": "Kolkata",
    "chennai": "Chennai",
    "madras": "Chennai",
    "hyderabad": "Hyderabad",
    "pune": "Pune",
    "noida": "Noida",
}

REQUIRED_COLUMNS = ["id", "name", "location", "cuisine", "rating", "cost", "budget_band"]
MIN_VALID_ROWS = 10


def normalize_city(value: object) -> str:
    """Normalize city name for consistent filtering."""
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return ""
    text = str(value).strip()
    if not text:
        return ""
    key = text.lower()
    if key in CITY_ALIASES:
        return CITY_ALIASES[key]
    return text.title()


def parse_rating(value: object) -> float | None:
    """Parse rating from formats like 4.5, '4.1/5', '4.5/5'."""
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return None
    text = str(value).strip()
    if not text or text in {"-", "NEW", "new", "NaN"}:
        return None
    match = re.search(r"(\d+(?:\.\d+)?)", text)
    if not match:
        return None
    rating = float(match.group(1))
    return max(0.0, min(5.0, rating))


def parse_cost(value: object) -> float | None:
    """Extract numeric cost from strings like '800', '1,200', '₹300 for two'."""
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return None
    if isinstance(value, (int, float)) and not (isinstance(value, float) and np.isnan(value)):
        cost = float(value)
        return cost if cost > 0 else None
    text = str(value).strip()
    if not text or text in {"-", "NaN"}:
        return None
    digits = re.sub(r"[^\d.]", "", text.replace(",", ""))
    if not digits:
        return None
    try:
        cost = float(digits)
    except ValueError:
        return None
    return cost if cost > 0 else None


def assign_budget_bands(costs: pd.Series) -> pd.Series:
    """Assign low/medium/high from 33rd and 66th percentiles of valid costs."""
    valid = costs.dropna()
    if valid.empty:
        logger.warning("No valid costs for budget bands; defaulting all to 'medium'.")
        return pd.Series(["medium"] * len(costs), index=costs.index)

    if valid.nunique() == 1:
        logger.warning("Zero cost variance; assigning all rows budget_band='medium'.")
        return pd.Series(["medium"] * len(costs), index=costs.index)

    t1, t2 = valid.quantile(0.33), valid.quantile(0.66)

    def band(cost: object) -> Literal["low", "medium", "high"]:
        if cost is None or (isinstance(cost, float) and np.isnan(cost)):
            return "medium"
        if cost <= t1:
            return "low"
        if cost <= t2:
            return "medium"
        return "high"

    return costs.map(band)


def _make_id(name: str, location: str, index: int) -> str:
    key = f"{name}|{location}".lower().encode()
    digest = hashlib.md5(key).hexdigest()[:10]
    return f"r_{digest}_{index}"


def preprocess(df: pd.DataFrame) -> pd.DataFrame:
    """
    Transform raw mapped DataFrame into normalized schema:
    id, name, location, cuisine, rating, cost, budget_band
    """
    work = df.copy()
    stats: dict[str, int] = {"dropped_invalid": 0, "duplicates_removed": 0}

    # Strings
    for col in ("name", "location", "cuisine"):
        if col in work.columns:
            work[col] = work[col].astype(str).str.strip()
            work[col] = work[col].replace({"nan": "", "None": ""})

    # Rating
    work["rating"] = work["rating"].map(parse_rating) if "rating" in work.columns else None
    before = len(work)
    work = work.dropna(subset=["rating"])
    stats["dropped_invalid"] += before - len(work)

    # Cost (optional)
    if "cost" in work.columns:
        work["cost"] = work["cost"].map(parse_cost)
    else:
        work["cost"] = None

    # Location
    if "location" in work.columns:
        work["location"] = work["location"].map(normalize_city)
    else:
        work["location"] = ""

    # Drop rows missing critical fields
    before = len(work)
    work = work[
        work["name"].astype(bool)
        & work["location"].astype(bool)
    ]
    stats["dropped_invalid"] += before - len(work)

    if "cuisine" not in work.columns:
        work["cuisine"] = ""
    work["cuisine"] = work["cuisine"].fillna("").astype(str)

    # Deduplicate name + location, keep highest rating
    before = len(work)
    work = work.sort_values("rating", ascending=False)
    work = work.drop_duplicates(subset=["name", "location"], keep="first")
    stats["duplicates_removed"] = before - len(work)

    # Budget bands
    work["budget_band"] = assign_budget_bands(work["cost"])

    # Stable IDs
    work = work.reset_index(drop=True)
    work["id"] = [
        _make_id(work.at[i, "name"], work.at[i, "location"], i)
        for i in range(len(work))
    ]

    # Ensure unique ids
    if work["id"].duplicated().any():
        work["id"] = [f"{rid}_{i}" for i, rid in enumerate(work["id"])]

    work = work[REQUIRED_COLUMNS]

    if len(work) < MIN_VALID_ROWS:
        raise ValueError(
            f"Only {len(work)} valid rows after preprocessing (minimum {MIN_VALID_ROWS}). "
            "Check dataset schema or source data."
        )

    logger.info(
        "Preprocessing complete: %d rows, dropped/duplicates=%s",
        len(work),
        stats,
    )
    logger.info(
        "Budget thresholds (33rd/66th percentiles on cost): computed during band assignment"
    )

    return work
