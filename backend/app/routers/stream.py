"""Feature 5 — Atlas Stream Processing ↔ AWS Kinesis routes."""
from __future__ import annotations

from fastapi import APIRouter

from app.models.stream import (
    ScenariosResponse,
    SimulateStreamRequest,
    SimulateStreamResponse,
)
from app.services import stream_service as svc

router = APIRouter(prefix="/api/stream", tags=["stream-processing"])


@router.get("/scenarios", response_model=ScenariosResponse)
async def scenarios() -> ScenariosResponse:
    """Connection-registry entries, pipelines, and management commands for both
    Kinesis↔Atlas directions."""
    return svc.get_scenarios()


@router.post("/simulate", response_model=SimulateStreamResponse)
async def simulate(req: SimulateStreamRequest) -> SimulateStreamResponse:
    """Push synthetic IoT events through the chosen pipeline (simulated) and show
    where each record lands: sink or dead-letter queue."""
    return svc.simulate(req.scenario_id, req.count)
