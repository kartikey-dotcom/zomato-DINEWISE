"""Normalized restaurant record (post-preprocessing)."""

from typing import Literal

from pydantic import BaseModel, Field


class Restaurant(BaseModel):
    id: str
    name: str
    location: str
    cuisine: str
    rating: float = Field(ge=0.0, le=5.0)
    cost: float | None = None
    budget_band: Literal["low", "medium", "high"]
