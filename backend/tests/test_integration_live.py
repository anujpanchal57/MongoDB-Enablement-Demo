"""Live integration tests against a real Atlas cluster + Voyage.

These are SKIPPED unless both MONGODB_URI and VOYAGE_API_KEY are set, so the
default unit-test run stays hermetic. Run them after seeding indexes:

    MONGODB_URI=... VOYAGE_API_KEY=... python -m pytest tests/test_integration_live.py -v
"""
import os

import pytest

from app.config import get_settings
from app.db import connect, disconnect, ping
from app.models.search import SearchMode
from app.services.search_service import get_search_service

pytestmark = pytest.mark.skipif(
    not (os.getenv("MONGODB_URI") and os.getenv("VOYAGE_API_KEY")),
    reason="Live Atlas + Voyage credentials not set; skipping integration tests.",
)


@pytest.fixture(scope="module", autouse=True)
async def _db():
    get_settings.cache_clear()
    await connect()
    yield
    await disconnect()


async def test_atlas_reachable():
    assert await ping() is True


async def test_fulltext_returns_results():
    results = await get_search_service().fulltext("godfather", limit=5)
    assert isinstance(results, list)
    assert len(results) > 0
    assert results[0].title


async def test_vector_returns_results():
    results = await get_search_service().vector("a heist that goes wrong", limit=5)
    assert len(results) > 0


async def test_hybrid_combines_and_ranks():
    results = await get_search_service().hybrid("coming of age friendship", limit=8)
    assert len(results) > 0
    # At least one result should carry fusion metadata.
    assert any(r.fused_score is not None for r in results)


async def test_compare_all_modes():
    svc = get_search_service()
    for mode in (SearchMode.FULLTEXT, SearchMode.VECTOR, SearchMode.HYBRID):
        resp = await svc.search("space exploration", mode, limit=5)
        assert resp.count >= 0
        assert resp.mode is mode
