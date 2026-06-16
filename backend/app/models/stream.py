"""Models for Feature 5 — Atlas Stream Processing ↔ AWS Kinesis (guided demo)."""
from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class StreamScenario(BaseModel):
    id: str
    title: str
    direction: str  # "kinesis_to_atlas" | "atlas_to_kinesis"
    summary: str
    connections: list[dict[str, Any]]  # connection registry entries (JSON)
    pipeline: list[dict[str, Any]]  # the stream processor aggregation pipeline
    management: list[str]  # sp.createStreamProcessor / start / sample commands


class ScenariosResponse(BaseModel):
    title: str
    docs: list[str]
    scenarios: list[StreamScenario]


class SimulateStreamRequest(BaseModel):
    scenario_id: str = Field("kinesis_to_atlas")
    count: int = Field(8, ge=1, le=30)


class StreamRecord(BaseModel):
    seq: int
    source: dict[str, Any]  # the inbound event
    output: Optional[dict[str, Any]] = None  # transformed/enriched result
    sink: str  # where it went: "merge:atlas", "emit:kinesis", or "dlq"
    note: Optional[str] = None


class SimulateStreamResponse(BaseModel):
    scenario_id: str
    direction: str
    processed: int
    to_sink: int
    to_dlq: int
    records: list[StreamRecord]
