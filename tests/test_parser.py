"""Tests for LLM response parser."""

import pytest

from src.llm.parser import LLMParseError, parse_llm_response


def test_parse_valid_json():
    raw = """
    {
      "recommendations": [
        {"id": "r1", "rank": 1, "explanation": "Great Italian fit."}
      ],
      "summary": "Top picks for you."
    }
    """
    result = parse_llm_response(raw, {"r1"})
    assert len(result["recommendations"]) == 1
    assert result["summary"] == "Top picks for you."


def test_parse_markdown_fences():
    raw = '```json\n{"recommendations": [{"id": "r1", "rank": 1, "explanation": "Ok"}]}\n```'
    result = parse_llm_response(raw, {"r1"})
    assert result["recommendations"][0]["id"] == "r1"


def test_drops_unknown_id():
    raw = '{"recommendations": [{"id": "bad", "rank": 1, "explanation": "x"}]}'
    result = parse_llm_response(raw, {"r1"})
    assert result["recommendations"] == []


def test_invalid_json_raises():
    with pytest.raises(LLMParseError):
        parse_llm_response("not json at all", {"r1"})
