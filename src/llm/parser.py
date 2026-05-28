"""Parse and validate JSON responses from the LLM."""

from __future__ import annotations

import json
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


class LLMParseError(Exception):
    """Response could not be parsed or validated."""


def _strip_markdown_fences(text: str) -> str:
    cleaned = text.strip()
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return cleaned


def _extract_json_object(text: str) -> dict[str, Any]:
    cleaned = _strip_markdown_fences(text)
    try:
        data = json.loads(cleaned)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass

    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start >= 0 and end > start:
        try:
            data = json.loads(cleaned[start : end + 1])
            if isinstance(data, dict):
                return data
        except json.JSONDecodeError as exc:
            raise LLMParseError(f"Invalid JSON in LLM response: {exc}") from exc

    raise LLMParseError("No JSON object found in LLM response")


def parse_llm_response(
    raw: str,
    valid_ids: set[str],
    *,
    renumber_ranks: bool = True,
) -> dict[str, Any]:
    """
    Parse LLM JSON and validate restaurant ids against candidate set.

    Returns dict with keys: recommendations (list), summary (optional).
    """
    data = _extract_json_object(raw)
    recommendations = data.get("recommendations")
    if not isinstance(recommendations, list):
        raise LLMParseError("Missing or invalid 'recommendations' array")

    validated: list[dict[str, Any]] = []
    seen_ids: set[str] = set()

    for item in recommendations:
        if not isinstance(item, dict):
            continue
        rid = item.get("id")
        if rid is None or str(rid) not in valid_ids:
            logger.warning("Dropping invalid or unknown restaurant id: %s", rid)
            continue
        rid = str(rid)
        if rid in seen_ids:
            continue
        seen_ids.add(rid)

        explanation = item.get("explanation") or ""
        rank = item.get("rank", len(validated) + 1)
        try:
            rank = int(rank)
        except (TypeError, ValueError):
            rank = len(validated) + 1

        validated.append(
            {
                "id": rid,
                "rank": rank,
                "explanation": str(explanation).strip(),
            }
        )

    if renumber_ranks:
        for i, item in enumerate(validated, start=1):
            item["rank"] = i

    summary = data.get("summary")
    if summary is not None:
        summary = str(summary).strip() or None

    return {"recommendations": validated, "summary": summary}
