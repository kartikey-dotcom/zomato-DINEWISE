# Project Context: AI-Powered Restaurant Recommendation System

This document captures the full context from `docs/ProblemStatement.txt` for building a Zomato-inspired restaurant recommendation service.

---

## Overview

Build an **AI-powered restaurant recommendation service** inspired by Zomato. The system intelligently suggests restaurants by combining **structured restaurant data** with a **Large Language Model (LLM)** to produce personalized, human-like recommendations.

---

## Objective

Design and implement an application that:

1. **Accepts user preferences** — location, budget, cuisine, ratings, and other filters
2. **Uses a real-world restaurant dataset** — Zomato data from Hugging Face
3. **Leverages an LLM** — generates personalized, natural-language recommendations
4. **Displays clear, useful results** — structured output with AI explanations

---

## Data Source

| Item | Detail |
|------|--------|
| **Dataset** | Zomato restaurant recommendation dataset |
| **URL** | https://huggingface.co/datasets/ManikaSaini/zomato-restaurant-recommendation |
| **Relevant fields** | Restaurant name, location, cuisine, cost, rating, and related attributes |

---

## System Workflow

### 1. Data Ingestion

- Load and preprocess the Zomato dataset from Hugging Face
- Extract fields: restaurant name, location, cuisine, cost, rating, etc.

### 2. User Input

Collect preferences:

| Preference | Examples |
|------------|----------|
| **Location** | Delhi, Bangalore |
| **Budget** | low, medium, high |
| **Cuisine** | Italian, Chinese |
| **Minimum rating** | Numeric threshold |
| **Additional** | family-friendly, quick service, etc. |

### 3. Integration Layer

- Filter and prepare restaurant data based on user input
- Pass structured (filtered) results into an LLM prompt
- Design a prompt that helps the LLM **reason** and **rank** options

### 4. Recommendation Engine

Use the LLM to:

- **Rank** restaurants
- **Explain** why each recommendation fits the user
- **Optionally summarize** the overall choice set

### 5. Output Display

Present top recommendations in a user-friendly format. Each item should include:

- Restaurant name
- Cuisine
- Rating
- Estimated cost
- AI-generated explanation

---

## Architecture (Logical Flow)

```
User Preferences
       ↓
Dataset (Hugging Face) → Preprocess → Filter by preferences
       ↓
Structured candidate list → LLM prompt (reason + rank)
       ↓
Top recommendations + explanations → User-facing display
```

---

## Key Technical Considerations

- **Hybrid approach**: deterministic filtering on structured data + LLM for ranking and narrative
- **Prompt design**: must encode user constraints and candidate restaurant facts clearly
- **UX**: results should be readable and actionable, not raw model output
- **Dataset dependency**: pipeline starts with reliable load/preprocess of the Hugging Face dataset

---

## Success Criteria

- User can specify location, budget, cuisine, rating, and extra preferences
- System returns a ranked shortlist with human-readable rationale per restaurant
- Output fields are consistent: name, cuisine, rating, cost, explanation
- Recommendations reflect both **data filters** and **LLM judgment**

---

## Out of Scope (Unless Extended)

The problem statement does not specify:

- Deployment platform (web, CLI, API)
- Specific LLM provider or API
- Authentication or user accounts
- Real-time Zomato API integration (dataset-only)

These can be chosen during implementation while staying aligned with the workflow above.

---

## Reference

- Original spec: `docs/ProblemStatement.txt`
- Dataset: [ManikaSaini/zomato-restaurant-recommendation](https://huggingface.co/datasets/ManikaSaini/zomato-restaurant-recommendation)
