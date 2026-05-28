"""Load raw Zomato dataset from Hugging Face."""

from __future__ import annotations

import logging
import urllib.request
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

DATASET_ID = "ManikaSaini/zomato-restaurant-recommendation"

# Map normalized field -> possible raw column names (first match wins).
COLUMN_ALIASES: dict[str, list[str]] = {
    "name": ["name", "restaurant_name", "Restaurant Name"],
    "location": [
        "location",
        "Location",
        "listed_in(city)",
        "listed_in_city",
        "city",
    ],
    "cuisine": ["cuisines", "cuisine", "Cuisines"],
    "cost": [
        "approx_cost(for two people)",
        "approx_cost_for_two_people",
        "average_cost",
        "avg_cost",
        "cost",
    ],
    "rating": ["rate", "rating", "aggregate_rating", "Rating"],
}


def _resolve_column(df: pd.DataFrame, aliases: list[str]) -> str | None:
    lower_map = {c.lower(): c for c in df.columns}
    for alias in aliases:
        if alias in df.columns:
            return alias
        if alias.lower() in lower_map:
            return lower_map[alias.lower()]
    return None


def map_raw_columns(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, str]]:
    """Rename raw columns to normalized names; return mapping used."""
    mapping: dict[str, str] = {}
    rename: dict[str, str] = {}

    for target, aliases in COLUMN_ALIASES.items():
        source = _resolve_column(df, aliases)
        if source is None:
            continue
        mapping[target] = source
        if source != target:
            rename[source] = target

    if "name" not in mapping:
        raise ValueError(
            f"Could not find restaurant name column. Available columns: {list(df.columns)}"
        )
    if "rating" not in mapping:
        raise ValueError(
            f"Could not find rating column. Available columns: {list(df.columns)}"
        )
    if "location" not in mapping:
        logger.warning(
            "No city/location column found; using placeholder 'Unknown' for location."
        )

    out = df.rename(columns=rename)
    for target in COLUMN_ALIASES:
        if target not in mapping and target not in out.columns:
            if target == "location":
                out["location"] = "Unknown"
                mapping["location"] = "(synthetic)"
            elif target == "cuisine":
                out["cuisine"] = ""
                mapping["cuisine"] = "(empty)"
            elif target == "cost":
                out["cost"] = None
                mapping["cost"] = "(missing)"

    logger.info("Column mapping: %s", mapping)
    return out, mapping


def load_raw_dataset() -> pd.DataFrame:
    """Download dataset from Hugging Face and return as DataFrame with normalized columns."""
    logger.info("Loading dataset from Hugging Face: %s", DATASET_ID)
    url = f"https://huggingface.co/datasets/{DATASET_ID}/resolve/main/zomato.csv"
    
    # Download the CSV file directly to data/ folder
    temp_dir = Path("data")
    temp_dir.mkdir(parents=True, exist_ok=True)
    csv_path = temp_dir / "zomato.csv"
    
    if not csv_path.exists():
        logger.info("Downloading raw CSV from %s", url)
        # Use simple chunked download to minimize memory footprint
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response, open(csv_path, 'wb') as out_file:
            chunk_size = 1024 * 1024  # 1MB chunks
            while True:
                chunk = response.read(chunk_size)
                if not chunk:
                    break
                out_file.write(chunk)
        logger.info("Raw CSV downloaded successfully.")
    else:
        logger.info("Using existing raw CSV at %s", csv_path)
        
    logger.info("Parsing CSV file into Pandas DataFrame...")
    import csv
    # Increase field size limit to handle huge fields (like reviews)
    csv.field_size_limit(10000000)
    
    rows = []
    try:
        with open(csv_path, encoding="utf-8", errors="replace") as f:
            reader = csv.reader(f)
            header = next(reader)
            for row in reader:
                if len(row) == len(header):
                    rows.append(row)
                else:
                    logger.warning(f"Skipping row with mismatching column count: expected {len(header)}, got {len(row)}")
        df = pd.DataFrame(rows, columns=header)
    except Exception as e:
        logger.error(f"Failed to parse CSV with csv.reader: {e}")
        # fallback to pandas standard read
        df = pd.read_csv(csv_path, low_memory=True)
    logger.info("Loaded %d raw rows, columns: %s", len(df), list(df.columns))

    mapped, column_mapping = map_raw_columns(df)
    mapped.attrs["column_mapping"] = column_mapping
    return mapped
