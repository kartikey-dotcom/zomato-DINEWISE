"""Smoke test: verify Google AI Studio (Gemini) API key and model."""

from __future__ import annotations

import logging
import sys

from src.config import get_settings
from src.llm.client import LLMConfigurationError, create_llm_client

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    settings = get_settings()
    if not settings.llm_configured:
        logger.error(
            "GEMINI_API_KEY not set. Add your AI Studio key to .env:\n"
            "  https://aistudio.google.com/apikey"
        )
        sys.exit(1)

    logger.info("Provider: %s | Model: %s", settings.llm_provider, settings.llm_model)

    try:
        client = create_llm_client(settings)
    except LLMConfigurationError as exc:
        logger.error("%s", exc)
        sys.exit(1)

    reply = client.complete('Reply with JSON only: {"status": "ok", "provider": "gemini"}')
    logger.info("Response (first 500 chars):\n%s", reply[:500])


if __name__ == "__main__":
    main()
