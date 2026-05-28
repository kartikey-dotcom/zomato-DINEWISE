"""Live LLM test — requires GEMINI_API_KEY in .env (skipped if missing)."""

import pytest

from src.config import get_settings
from src.llm.client import LLMConfigurationError, create_llm_client


@pytest.mark.slow
def test_gemini_api_call_returns_text():
    settings = get_settings()
    if not settings.llm_configured:
        pytest.skip("GEMINI_API_KEY / LLM_API_KEY not set in .env")

    try:
        client = create_llm_client(settings)
    except LLMConfigurationError as exc:
        pytest.skip(str(exc))

    reply = client.complete(
        'Respond with JSON only, no markdown: {"status": "ok", "message": "gemini works"}'
    )
    assert reply
    assert len(reply) > 5
    assert "ok" in reply.lower() or "gemini" in reply.lower() or "status" in reply.lower()
