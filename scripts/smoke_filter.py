"""Manual smoke test for Phase 2 filtering (requires processed dataset)."""

from __future__ import annotations

import logging
import sys

from src.config import get_settings
from src.data.repository import RestaurantRepository
from src.models.preferences import UserPreferences
from src.services.filter_service import FilterService, to_candidate_dicts

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    settings = get_settings()
    repo = RestaurantRepository()

    try:
        repo.load(settings.data_path)
    except FileNotFoundError as exc:
        logger.error("%s", exc)
        sys.exit(1)

    prefs = UserPreferences(
        location=sys.argv[1] if len(sys.argv) > 1 else "Bangalore",
        budget="medium",
        cuisine=sys.argv[2] if len(sys.argv) > 2 else None,
        min_rating=4.0,
    )

    service = FilterService(max_candidates=settings.max_candidates)
    result = service.filter(prefs, repo.all())

    logger.info("Filters: %s", result.filters_applied)
    logger.info("Matched: %d, candidates: %d", result.total_matched, len(result.candidates))

    for i, r in enumerate(result.candidates[:5], start=1):
        logger.info("%d. %s | %s | ★%.1f | %s", i, r.name, r.cuisine, r.rating, r.budget_band)

    if result.candidates:
        logger.info("Sample candidate JSON keys: %s", list(to_candidate_dicts(result.candidates[:1])[0].keys()))


if __name__ == "__main__":
    main()
