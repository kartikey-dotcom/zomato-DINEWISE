"""User preference input model with validation."""

from typing import Literal

from pydantic import BaseModel, Field, field_validator

from src.data.preprocessor import normalize_city

BudgetTier = Literal["low", "medium", "high"]


class UserPreferences(BaseModel):
    location: str
    budget: BudgetTier
    cuisine: str | None = None
    min_rating: float = Field(default=0.0, ge=0.0, le=5.0)
    additional: str | None = None

    @field_validator("location")
    @classmethod
    def validate_location(cls, value: str) -> str:
        text = value.strip()
        if not text:
            raise ValueError("Location is required")
        return normalize_city(text)

    @field_validator("min_rating", mode="before")
    @classmethod
    def clamp_min_rating(cls, value: object) -> float:
        if value is None or value == "":
            return 0.0
        rating = float(value)
        return max(0.0, min(5.0, rating))

    @field_validator("budget", mode="before")
    @classmethod
    def normalize_budget(cls, value: object) -> str:
        if value is None:
            raise ValueError("Budget is required (low, medium, or high)")
        text = str(value).strip().lower()
        if text not in {"low", "medium", "high"}:
            raise ValueError("Budget must be low, medium, or high")
        return text

    @field_validator("cuisine", "additional", mode="before")
    @classmethod
    def empty_string_to_none(cls, value: object) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text if text else None
