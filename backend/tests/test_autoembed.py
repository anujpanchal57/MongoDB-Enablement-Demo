"""Tests for Feature 4 (auto-embedding). Hermetic — no live Atlas required."""
from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import create_app
from app.services.autoembed_service import AutoEmbedService, _to_hit

client = TestClient(create_app())


def test_index_definition_uses_autoembed_type_and_managed_model():
    get_settings.cache_clear()
    svc = AutoEmbedService()
    definition = svc.index_definition()
    field = definition["fields"][0]
    # The auto-embedding contract: autoEmbed + modality:text + a managed model,
    # no client-side vector.
    assert field["type"] == "autoEmbed"
    assert field["modality"] == "text"
    assert field["model"]  # e.g. voyage-3.5
    assert field["path"] == get_settings().autoembed_path


def test_to_hit_maps_destination():
    hit = _to_hit(
        {"_id": "x", "name": "Kyoto", "country": "Japan", "tags": ["temples"], "_score": 0.9}
    )
    assert hit.name == "Kyoto"
    assert hit.country == "Japan"
    assert hit.tags == ["temples"]
    assert hit.score == 0.9


def test_dataset_endpoint_exposes_definition_and_examples():
    r = client.get("/api/autoembed/dataset")
    assert r.status_code == 200
    body = r.json()
    assert body["count"] >= 15
    assert body["index_definition"]["fields"][0]["type"] == "autoEmbed"
    assert len(body["examples"]) >= 3
    assert len(body["sample"]) > 0


def test_setup_requires_mongodb():
    get_settings.cache_clear()
    r = client.post("/api/autoembed/setup")
    assert r.status_code == 503


def test_search_validates_empty_query():
    r = client.post("/api/autoembed", json={"query": "", "limit": 5})
    assert r.status_code == 422
