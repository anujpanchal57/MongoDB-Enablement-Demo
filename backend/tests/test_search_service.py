"""Unit tests for the search service — focused on the RRF hybrid logic and the
document->model mapping. These run with no live DB or Voyage key."""
import pytest

from app.models.search import MovieHit, SearchMode
from app.services.search_service import SearchService, _display_pipeline, _to_hit


def test_display_pipeline_elides_query_vector():
    pipeline = [
        {"$vectorSearch": {"path": "v", "queryVector": [0.111, 0.222, 0.333, 0.444], "limit": 5}},
        {"$project": {"title": 1}},
    ]
    shown = _display_pipeline(pipeline)
    qv = shown[0]["$vectorSearch"]["queryVector"]
    assert isinstance(qv, str)
    assert "4 dims" in qv
    # Original pipeline must be untouched (deep copy).
    assert pipeline[0]["$vectorSearch"]["queryVector"] == [0.111, 0.222, 0.333, 0.444]


def _hit(id_: str, title: str) -> MovieHit:
    return MovieHit(id=id_, title=title)


def test_to_hit_coerces_messy_year_and_rating():
    doc = {
        "_id": "abc",
        "title": "Test Movie",
        "year": "1995è",  # embedded_movies sometimes has trailing junk
        "imdb": {"rating": 7.4},
        "genres": ["Drama"],
    }
    hit = _to_hit(doc)
    assert hit.id == "abc"
    assert hit.year == 1995
    assert hit.imdb_rating == 7.4
    assert hit.genres == ["Drama"]


def test_to_hit_handles_missing_fields():
    hit = _to_hit({"_id": 1})
    assert hit.title == "(untitled)"
    assert hit.year is None
    assert hit.genres == []
    assert hit.imdb_rating is None


class _FakeCursor:
    """Mimics PyMongo async command cursor: to_list() is a coroutine."""

    def __init__(self, docs):
        self._docs = docs

    async def to_list(self, length=None):
        return self._docs[:length] if length else self._docs


class _FakeCollection:
    """Mimics PyMongo async collection: aggregate() is a coroutine returning a cursor."""

    def __init__(self, docs):
        self._docs = docs
        self.last_pipeline = None

    async def aggregate(self, pipeline):
        self.last_pipeline = pipeline
        return _FakeCursor(self._docs)


@pytest.mark.asyncio
async def test_fulltext_awaits_async_aggregate(monkeypatch):
    """Regression: PyMongo async aggregate() must be awaited before to_list()."""
    fake = _FakeCollection([{"_id": "1", "title": "Alpha", "genres": ["Drama"]}])
    monkeypatch.setattr("app.services.search_service.get_collection", lambda: fake)
    svc = SearchService()
    results = await svc.fulltext("query", limit=5)
    assert results[0].title == "Alpha"
    # Sanity: the $search stage made it into the pipeline.
    assert any("$search" in stage for stage in fake.last_pipeline)


@pytest.mark.asyncio
async def test_vector_awaits_async_aggregate(monkeypatch):
    """Regression: vector search also awaits aggregate(); embedding is mocked."""
    fake = _FakeCollection([{"_id": "2", "title": "Bravo"}])
    monkeypatch.setattr("app.services.search_service.get_collection", lambda: fake)

    class _FakeEmbed:
        def embed_query(self, text):
            return [0.1, 0.2, 0.3]

    monkeypatch.setattr(
        "app.services.search_service.get_embedding_service", lambda: _FakeEmbed()
    )
    svc = SearchService()
    results = await svc.vector("query", limit=5)
    assert results[0].title == "Bravo"
    assert any("$vectorSearch" in stage for stage in fake.last_pipeline)


@pytest.mark.asyncio
async def test_hybrid_rrf_fuses_and_ranks(monkeypatch):
    """A doc ranked highly by both methods should beat docs ranked by only one."""
    svc = SearchService()

    text_results = [_hit("A", "Alpha"), _hit("B", "Bravo"), _hit("C", "Charlie")]
    vector_results = [_hit("B", "Bravo"), _hit("D", "Delta"), _hit("A", "Alpha")]

    async def fake_fulltext(query, limit, capture=None):
        return text_results

    async def fake_vector(query, limit, capture=None):
        return vector_results

    monkeypatch.setattr(svc, "fulltext", fake_fulltext)
    monkeypatch.setattr(svc, "vector", fake_vector)

    fused = await svc.hybrid("anything", limit=10, rrf_k=60)

    # B appears in both lists near the top -> should rank first.
    assert fused[0].id == "B"
    # Every fused hit carries a fused_score and at least one contributing rank.
    for h in fused:
        assert h.fused_score is not None
        assert (h.fulltext_rank is not None) or (h.vector_rank is not None)

    # B's ranks come from both lists.
    b = next(h for h in fused if h.id == "B")
    assert b.fulltext_rank == 2
    assert b.vector_rank == 1


@pytest.mark.asyncio
async def test_hybrid_respects_limit(monkeypatch):
    svc = SearchService()
    many = [_hit(str(i), f"m{i}") for i in range(20)]

    async def fake(query, limit, capture=None):
        return many

    monkeypatch.setattr(svc, "fulltext", fake)
    monkeypatch.setattr(svc, "vector", fake)

    fused = await svc.hybrid("q", limit=5)
    assert len(fused) == 5


@pytest.mark.asyncio
async def test_search_dispatch_routes_modes(monkeypatch):
    svc = SearchService()
    calls = {}

    async def fake_fulltext(query, limit, capture=None):
        calls["fulltext"] = True
        return []

    async def fake_vector(query, limit, capture=None):
        calls["vector"] = True
        return []

    async def fake_hybrid(query, limit, rrf_k=60, capture=None):
        calls["hybrid"] = True
        return []

    monkeypatch.setattr(svc, "fulltext", fake_fulltext)
    monkeypatch.setattr(svc, "vector", fake_vector)
    monkeypatch.setattr(svc, "hybrid", fake_hybrid)

    await svc.search("q", SearchMode.FULLTEXT, 10)
    await svc.search("q", SearchMode.VECTOR, 10)
    await svc.search("q", SearchMode.HYBRID, 10)
    assert calls == {"fulltext": True, "vector": True, "hybrid": True}


@pytest.mark.asyncio
async def test_search_response_shape(monkeypatch):
    svc = SearchService()

    async def fake_fulltext(query, limit, capture=None):
        if capture is not None:
            capture["fulltext"] = [{"$search": {"text": {"query": query}}}]
        return [_hit("A", "Alpha")]

    monkeypatch.setattr(svc, "fulltext", fake_fulltext)
    resp = await svc.search("q", SearchMode.FULLTEXT, 10)
    assert resp.mode is SearchMode.FULLTEXT
    assert resp.count == 1
    assert resp.took_ms >= 0
    assert resp.results[0].title == "Alpha"
    # The executed pipeline is surfaced for the UI.
    assert resp.query_used is not None
    assert "fulltext" in resp.query_used
