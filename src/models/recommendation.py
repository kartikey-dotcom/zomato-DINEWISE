"""Recommendation output models (used from Phase 4 orchestration onward)."""

from pydantic import BaseModel, Field


class RecommendationItem(BaseModel):
    rank: int = Field(ge=1)
    name: str
    cuisine: str
    rating: float = Field(ge=0.0, le=5.0)
    estimated_cost: str | float
    explanation: str


class RecommendationResponse(BaseModel):
    items: list[RecommendationItem] = Field(default_factory=list)
    summary: str | None = None
    metadata: dict = Field(default_factory=dict)
