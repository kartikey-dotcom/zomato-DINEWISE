"""Pytest configuration and shared fixtures."""

import pytest


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers",
        "slow: tests that call the live Gemini API (require GEMINI_API_KEY)",
    )


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Skip live LLM tests unless -m slow is passed explicitly."""
    markexpr = config.getoption("-m", default="")
    if "slow" in markexpr:
        return
    skip_live = pytest.mark.skip(reason="Pass -m slow to run live Gemini API tests")
    for item in items:
        if "slow" in item.keywords:
            item.add_marker(skip_live)
