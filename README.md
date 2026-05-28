# AI-Powered Restaurant Recommendation System (Zomato)

Hybrid recommender: structured filtering on Zomato data + LLM ranking and explanations.

## Documentation

- [`context.md`](context.md) — product requirements
- [`architecture.md`](architecture.md) — system design
- [`implementation.md`](implementation.md) — build guide
- [`edge-cases.md`](edge-cases.md) — boundary conditions

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
copy .env.example .env
```

### Google AI Studio (Gemini) API key

This project uses **Google AI Studio** ([aistudio.google.com](https://aistudio.google.com)) as the LLM provider.

1. Open [aistudio.google.com/apikey](https://aistudio.google.com/apikey)
2. Create an API key
3. Add to `.env`:

```env
GEMINI_API_KEY=your_key_here
LLM_MODEL=gemini-2.0-flash
```

Verify the connection:

```bash
python scripts/smoke_llm.py
```

## Phase 1: Data pipeline

Download and preprocess the [Hugging Face dataset](https://huggingface.co/datasets/ManikaSaini/zomato-restaurant-recommendation):

```bash
python -m src.data.run_pipeline
```

Force rebuild from Hugging Face:

```bash
# .env: FORCE_REFRESH=true
python -m src.data.run_pipeline --force
```

**Output:** `data/processed/restaurants.parquet`

**Schema:**

| Column | Description |
|--------|-------------|
| `id` | Stable identifier |
| `name` | Restaurant name |
| `location` | City (normalized, e.g. Bengaluru → Bangalore) |
| `cuisine` | Cuisine string |
| `rating` | 0.0–5.0 |
| `cost` | Approx cost for two (numeric, nullable) |
| `budget_band` | `low` / `medium` / `high` (33rd/66th percentile of costs) |

**Raw column mapping** (auto-detected): `name`, `listed_in(city)` or `location`, `cuisines`, `rate`, `approx_cost(for two people)`.

## Phase 2: Domain models & filtering

Filter restaurants by preferences (no LLM yet):

```python
from src.config import get_settings
from src.data.repository import RestaurantRepository
from src.models.preferences import UserPreferences
from src.services.filter_service import FilterService

settings = get_settings()
repo = RestaurantRepository()
repo.load(settings.data_path)

prefs = UserPreferences(location="Bangalore", budget="medium", cuisine="Italian", min_rating=4.0)
result = FilterService(max_candidates=settings.max_candidates).filter(prefs, repo.all())
print(result.candidates)
```

Or use the smoke script:

```bash
python scripts/smoke_filter.py Bangalore Italian
```

**Filter rules:** location (case-insensitive, city aliases), `min_rating`, optional cuisine substring, `budget_band` match; results capped by `MAX_CANDIDATES` and sorted by rating.

## Tests

```bash
# Unit tests (no API calls)
pytest tests/ -v

# Windows helper (creates venv if needed)
.\scripts\run_tests.ps1

# Live Gemini test (uses .env key)
pytest tests/test_llm_live.py -v -m slow
python scripts/smoke_llm.py

# Or both:
.\scripts\run_tests.ps1 -Live
```

By default, `pytest` **skips** live LLM tests. Use `-m slow` to run them.

## Project status

| Phase | Status |
|-------|--------|
| 1 Data ingestion | Implemented |
| 2 Domain & filter | Implemented |
| 3 LLM (Google Gemini / AI Studio) | Implemented (`src/llm/`) |
| 4 Orchestration | Implemented (`recommendation_service.py`) |
| 5 UI (Streamlit) | Planned — see `implementation.md` |

## Run all tests (after Python install)

```powershell
.\scripts\run_tests.ps1
.\scripts\run_tests.ps1 -Live   # includes Gemini API test
```
