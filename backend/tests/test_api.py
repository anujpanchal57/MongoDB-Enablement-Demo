"""API-level tests using FastAPI's TestClient. No live MongoDB required —
these verify routing, validation, and graceful degradation when unconfigured."""
from fastapi.testclient import TestClient

from app.main import create_app

client = TestClient(create_app())


def test_root():
    r = client.get("/")
    assert r.status_code == 200
    assert r.json()["name"].startswith("MongoDB on AWS")


def test_health_reports_dependency_flags():
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert "mongodb_configured" in body
    assert "voyage_configured" in body


def test_examples_endpoint_returns_curated_queries():
    r = client.get("/api/search/examples")
    assert r.status_code == 200
    examples = r.json()["examples"]
    assert len(examples) >= 3
    assert all({"label", "query", "why"} <= set(e) for e in examples)


def test_search_requires_mongodb_configured():
    # With no MONGODB_URI set in the test env, search should 503, not crash.
    r = client.post("/api/search", json={"query": "test", "mode": "fulltext"})
    assert r.status_code == 503


def test_search_validates_empty_query():
    r = client.post("/api/search", json={"query": "", "mode": "fulltext"})
    assert r.status_code == 422  # pydantic min_length


def test_compare_requires_query_param():
    r = client.get("/api/search/compare")
    assert r.status_code == 422
