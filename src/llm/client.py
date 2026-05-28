"""LLM client abstraction — default provider: Google AI Studio (Gemini)."""

from __future__ import annotations

import logging
from typing import Protocol

from src.config import Settings, get_settings

logger = logging.getLogger(__name__)

# Fallback models if primary name is unavailable in your AI Studio region/account
GEMINI_MODEL_FALLBACKS = (
    "gemini-2.0-flash",
    "gemini-1.5-flash",
    "gemini-1.5-flash-latest",
    "gemini-1.5-pro",
)


class LLMClient(Protocol):
    def complete(self, prompt: str) -> str:
        """Send prompt to the model and return raw text response."""
        ...


class LLMConfigurationError(Exception):
    """Raised when API key or provider setup is invalid."""


class GeminiClient:
    """
    Google Gemini via API key from AI Studio (aistudio.google.com).

    Docs: https://ai.google.dev/gemini-api/docs/api-key
    """

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-2.0-flash",
        temperature: float = 0.3,
    ) -> None:
        if not api_key or not api_key.strip():
            raise LLMConfigurationError(
                "GEMINI_API_KEY is missing. Get one at https://aistudio.google.com/apikey"
            )
        self._api_key = api_key.strip()
        self._model = model
        self._temperature = temperature
        self._model_instance = None
        self._active_model_name = model

    def _get_model(self, model_name: str):
        import google.generativeai as genai

        genai.configure(api_key=self._api_key)
        return genai.GenerativeModel(model_name)

    def _models_to_try(self) -> list[str]:
        ordered: list[str] = [self._model]
        for name in GEMINI_MODEL_FALLBACKS:
            if name not in ordered:
                ordered.append(name)
        return ordered

    def complete(self, prompt: str) -> str:
        last_error: Exception | None = None

        for model_name in self._models_to_try():
            try:
                logger.info("Calling Gemini model: %s", model_name)
                model = self._get_model(model_name)
                response = model.generate_content(
                    prompt,
                    generation_config={"temperature": self._temperature},
                )
                text = _extract_text(response)
                if text:
                    self._active_model_name = model_name
                    return text
                last_error = RuntimeError("Empty response")
            except Exception as exc:
                logger.warning("Gemini model %s failed: %s", model_name, exc)
                last_error = exc
                continue

        raise RuntimeError(
            f"All Gemini models failed. Last error: {last_error}. "
            "Check GEMINI_API_KEY and LLM_MODEL in .env."
        ) from last_error


def _extract_text(response: object) -> str:
    """Extract text from google-generativeai response; handle blocked/empty replies."""
    try:
        if hasattr(response, "text"):
            text = response.text
            if text:
                return str(text).strip()
    except (ValueError, AttributeError) as exc:
        logger.warning("Could not read response.text: %s", exc)

    candidates = getattr(response, "candidates", None) or []
    parts: list[str] = []
    for candidate in candidates:
        content = getattr(candidate, "content", None)
        if not content:
            continue
        for part in getattr(content, "parts", []) or []:
            if hasattr(part, "text") and part.text:
                parts.append(part.text)

    if parts:
        return "\n".join(parts).strip()

    feedback = getattr(response, "prompt_feedback", None)
    if feedback:
        logger.warning("Prompt feedback: %s", feedback)

    return ""


def create_llm_client(settings: Settings | None = None) -> LLMClient:
    """Factory: build LLM client from settings (default: Google Gemini)."""
    cfg = settings or get_settings()

    if cfg.llm_provider == "google":
        if not cfg.llm_configured:
            raise LLMConfigurationError(
                "Set GEMINI_API_KEY in .env (from https://aistudio.google.com/apikey)"
            )
        return GeminiClient(
            api_key=cfg.llm_api_key,  # type: ignore[arg-type]
            model=cfg.llm_model,
            temperature=cfg.llm_temperature,
        )

    raise LLMConfigurationError(f"Unsupported LLM provider: {cfg.llm_provider}")
