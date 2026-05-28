"""Bootstrap script: download, preprocess, and cache restaurant data."""

from __future__ import annotations

import logging
import sys

from src.config import get_settings
from src.data.loader import load_raw_dataset
from src.data.preprocessor import preprocess

logger = logging.getLogger(__name__)


def configure_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )


def run(force_refresh: bool | None = None) -> None:
    settings = get_settings()
    refresh = settings.force_refresh if force_refresh is None else force_refresh
    data_path = settings.data_path

    data_path.parent.mkdir(parents=True, exist_ok=True)

    if data_path.exists() and not refresh:
        logger.info("Using cached data at %s (set FORCE_REFRESH=true to rebuild)", data_path)
        return

    if refresh and data_path.exists():
        logger.info("FORCE_REFRESH enabled; rebuilding dataset")

    raw = load_raw_dataset()
    processed = preprocess(raw)
    processed.to_parquet(data_path, index=False)

    logger.info("Wrote %d restaurants to %s", len(processed), data_path)

    # Summary stats for README / verification
    by_city = processed.groupby("location").size().sort_values(ascending=False)
    logger.info("Top cities by count:\n%s", by_city.head(10).to_string())
    logger.info(
        "Budget band distribution:\n%s",
        processed["budget_band"].value_counts().to_string(),
    )


def main() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)

    try:
        force = "--force" in sys.argv or settings.force_refresh
        run(force_refresh=force)
    except Exception:
        logger.exception("Data pipeline failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
