"""Shared pytest fixtures."""
import os

import pytest

# Ensure tests never accidentally hit a real cluster unless explicitly enabled.
os.environ.setdefault("MONGODB_URI", "")
os.environ.setdefault("VOYAGE_API_KEY", "")


@pytest.fixture(autouse=True)
def _clear_settings_cache():
    """Reset the cached Settings between tests so env overrides take effect."""
    from app.config import get_settings

    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
