"""Application configuration loaded from environment variables."""

import os
from pathlib import Path
from typing import Any, Literal

from pydantic import AliasChoices, Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent

LLMProvider = Literal["google"]

_ENV_KEY_ALIASES = ("GEMINI_API_KEY", "LLM_API_KEY", "GOOGLE_API_KEY")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    # Google AI Studio: https://aistudio.google.com/apikey
    llm_provider: LLMProvider = "google"
    llm_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices(*_ENV_KEY_ALIASES),
    )
    llm_model: str = "gemini-2.0-flash"
    llm_temperature: float = Field(default=0.3, ge=0.0, le=1.0)

    max_candidates: int = 30
    top_n: int = 5
    data_path: Path = Field(default=PROJECT_ROOT / "data" / "processed" / "restaurants.parquet")
    force_refresh: bool = False
    log_level: str = "INFO"

    @model_validator(mode="before")
    @classmethod
    def load_api_key_from_env(cls, data: Any) -> Any:
        """Ensure GEMINI_API_KEY / LLM_API_KEY are picked up reliably on all platforms."""
        if not isinstance(data, dict):
            return data
        existing = data.get("llm_api_key")
        if existing is not None and str(existing).strip():
            return data
        # Try loading from standard environment variables first
        for env_name in _ENV_KEY_ALIASES:
            value = os.getenv(env_name)
            if value and value.strip():
                data["llm_api_key"] = value.strip()
                return data
        # Try loading from Streamlit secrets if running inside Streamlit
        try:
            import streamlit as st
            if hasattr(st, "secrets") and st.secrets:
                for env_name in _ENV_KEY_ALIASES:
                    if env_name in st.secrets:
                        val = st.secrets[env_name]
                        if val and str(val).strip():
                            data["llm_api_key"] = str(val).strip()
                            return data
        except Exception:
            pass
        return data

    @field_validator("llm_api_key", mode="before")
    @classmethod
    def strip_api_key(cls, value: object) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text if text else None

    @property
    def llm_configured(self) -> bool:
        return bool(self.llm_api_key)


def get_settings() -> Settings:
    return Settings()
