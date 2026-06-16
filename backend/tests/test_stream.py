"""Tests for Feature 5 (Atlas Stream Processing ↔ Kinesis). Fully hermetic."""
from fastapi.testclient import TestClient

from app.main import create_app
from app.services import stream_service as svc

client = TestClient(create_app())


def test_scenarios_have_both_directions():
    resp = svc.get_scenarios()
    directions = {s.direction for s in resp.scenarios}
    assert directions == {"kinesis_to_atlas", "atlas_to_kinesis"}


def test_kinesis_to_atlas_pipeline_has_source_validate_merge():
    s = next(s for s in svc.get_scenarios().scenarios if s.id == "kinesis_to_atlas")
    stages = [list(stage.keys())[0] for stage in s.pipeline]
    assert "$source" in stages
    assert "$validate" in stages
    assert "$merge" in stages
    # $source must reference the Kinesis connection.
    assert s.pipeline[0]["$source"]["connectionName"] == "awsKinesis1"


def test_atlas_to_kinesis_pipeline_emits_to_kinesis():
    s = next(s for s in svc.get_scenarios().scenarios if s.id == "atlas_to_kinesis")
    stages = [list(stage.keys())[0] for stage in s.pipeline]
    assert "$emit" in stages
    emit = s.pipeline[-1]["$emit"]
    assert emit["connectionName"] == "awsKinesis1"
    assert emit["partitionKey"] == "$device_id"


def test_simulate_routes_invalid_records_to_dlq():
    resp = svc.simulate("kinesis_to_atlas", 8)
    assert resp.processed == 8
    assert resp.to_dlq > 0  # every 4th event is out-of-range
    assert resp.to_sink + resp.to_dlq == 8
    # DLQ records carry no output document.
    dlq = [r for r in resp.records if r.sink == "dlq"]
    assert all(r.output is None for r in dlq)


def test_simulate_is_deterministic():
    a = svc.simulate("kinesis_to_atlas", 10)
    b = svc.simulate("kinesis_to_atlas", 10)
    assert [r.source for r in a.records] == [r.source for r in b.records]


def test_simulate_endpoint():
    r = client.post("/api/stream/simulate", json={"scenario_id": "atlas_to_kinesis", "count": 6})
    assert r.status_code == 200
    body = r.json()
    assert body["direction"] == "atlas_to_kinesis"
    assert body["processed"] == 6
    assert len(body["records"]) == 6


def test_simulate_validates_count_bounds():
    r = client.post("/api/stream/simulate", json={"scenario_id": "kinesis_to_atlas", "count": 999})
    assert r.status_code == 422
