"""Tests for settings (no dependency on your local .env values)."""

from src.config import Settings


def test_strip_api_key():
    settings = Settings(llm_api_key="  test-key-123  ")
    assert settings.llm_api_key == "test-key-123"
    assert settings.llm_configured is True


def test_llm_not_configured_when_missing():
    settings = Settings(llm_api_key="")
    assert settings.llm_api_key is None
    assert settings.llm_configured is False


def test_default_provider_and_model():
    settings = Settings()
    assert settings.llm_provider == "google"
    assert "gemini" in settings.llm_model.lower()
