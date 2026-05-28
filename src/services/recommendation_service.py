"""Orchestrates filter → LLM → response (single entry point)."""

from __future__ import annotations

import logging

from src.config import Settings, get_settings
from src.data.repository import RestaurantRepository
from src.llm.client import LLMClient, LLMConfigurationError, create_llm_client
from src.llm.parser import LLMParseError, parse_llm_response
from src.models.preferences import UserPreferences
from src.models.recommendation import RecommendationResponse
from src.models.restaurant import Restaurant
from src.services.filter_service import FilterService
from src.services.merge import fallback_recommendations, merge_recommendations
from src.services.prompt_builder import PromptBuilder

logger = logging.getLogger(__name__)

EMPTY_MESSAGE = (
    "No restaurants match your filters. Try lowering minimum rating, "
    "changing cuisine, or selecting a different budget."
)


class RecommendationService:
    def __init__(
        self,
        repository: RestaurantRepository,
        filter_service: FilterService | None = None,
        prompt_builder: PromptBuilder | None = None,
        llm_client: LLMClient | None = None,
        settings: Settings | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._repository = repository
        self._filter = filter_service or FilterService(
            max_candidates=self._settings.max_candidates
        )
        self._prompt_builder = prompt_builder or PromptBuilder(top_n=self._settings.top_n)
        self._llm_client = llm_client

    def _get_llm_client(self) -> LLMClient:
        if self._llm_client is not None:
            return self._llm_client
        return create_llm_client(self._settings)

    def get_recommendations(self, preferences: UserPreferences) -> RecommendationResponse:
        if not self._repository.is_loaded:
            raise RuntimeError(
                "Dataset not loaded. Run: python -m src.data.run_pipeline"
            )

        filter_result = self._filter.filter(preferences, self._repository.all())
        metadata: dict = {
            "candidates_considered": len(filter_result.candidates),
            "total_matched": filter_result.total_matched,
            "filters_applied": filter_result.filters_applied,
            "fallback": False,
        }

        if not filter_result.candidates:
            metadata["message"] = EMPTY_MESSAGE
            return RecommendationResponse(items=[], summary=None, metadata=metadata)

        candidates = filter_result.candidates
        valid_ids = {r.id for r in candidates}

        try:
            client = self._get_llm_client()
            prompt = self._prompt_builder.build(preferences, candidates)
            raw = client.complete(prompt)
            try:
                parsed = parse_llm_response(raw, valid_ids)
            except LLMParseError as parse_exc:
                logger.warning(
                    "First LLM response parsing failed (%s). Retrying once with strict JSON-only instructions...",
                    parse_exc,
                )
                retry_prompt = (
                    prompt
                    + "\n\nCRITICAL: Your previous response could not be parsed. "
                    "You MUST respond with VALID JSON ONLY matching the output schema. "
                    "Do NOT include any markdown code fences (like ```json), "
                    "explanations outside the JSON block, or conversational filler."
                )
                raw = client.complete(retry_prompt)
                parsed = parse_llm_response(raw, valid_ids)

            items = merge_recommendations(parsed["recommendations"], candidates)

            if not items:
                logger.warning("LLM returned no valid items; using fallback ranking")
                items = fallback_recommendations(candidates, self._settings.top_n)
                metadata["fallback"] = True

            return RecommendationResponse(
                items=items,
                summary=parsed.get("summary"),
                metadata=metadata,
            )

        except (LLMConfigurationError, LLMParseError, RuntimeError) as exc:
            logger.warning("LLM path failed (%s); using fallback ranking", exc)
            items = fallback_recommendations(candidates, self._settings.top_n)
            metadata["fallback"] = True
            metadata["message"] = str(exc)
            return RecommendationResponse(items=items, summary=None, metadata=metadata)


def build_recommendation_service(
    repository: RestaurantRepository | None = None,
    settings: Settings | None = None,
) -> RecommendationService:
    """Factory: load repository from settings and return service."""
    cfg = settings or get_settings()
    repo = repository or RestaurantRepository()
    if not repo.is_loaded:
        repo.load(cfg.data_path)
    return RecommendationService(repository=repo, settings=cfg)
