"""Build prompts for Gemini (Google AI Studio) recommendation ranking."""

from __future__ import annotations

import json

from src.models.preferences import UserPreferences
from src.models.restaurant import Restaurant
from src.services.filter_service import to_candidate_dicts


class PromptBuilder:
    def __init__(self, top_n: int = 5) -> None:
        self.top_n = top_n

    def build(self, preferences: UserPreferences, candidates: list[Restaurant]) -> str:
        if not candidates:
            raise ValueError("Cannot build prompt without candidates")

        cuisine = preferences.cuisine or "any"
        additional = preferences.additional or "none"
        candidate_json = json.dumps(to_candidate_dicts(candidates), indent=2)

        return f"""You are a restaurant recommendation assistant for Indian cities (Zomato-style).
You must ONLY rank restaurants from the CANDIDATES list below. Do not invent restaurants.
Return valid JSON only, matching the output schema exactly. No markdown fences.

[User constraints]
- Location: {preferences.location}
- Budget: {preferences.budget}
- Cuisine: {cuisine}
- Minimum rating: {preferences.min_rating}
- Additional preferences: {additional}

[CANDIDATES]
{candidate_json}

[Task]
1. Select and rank the top {self.top_n} restaurants from CANDIDATES only.
2. For each, write a 1-2 sentence explanation tied to the user constraints.
3. Optionally include a short summary paragraph for the overall list.

[Output schema]
{{
  "recommendations": [
    {{ "id": "string", "rank": 1, "explanation": "string" }}
  ],
  "summary": "string or null"
}}
"""
