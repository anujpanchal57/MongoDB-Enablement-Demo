"""Feature 3 — MCP-on-AgentCore guided walkthrough routes."""
from __future__ import annotations

from fastapi import APIRouter

from app.models.mcp_deploy import (
    DeployConfig,
    SimulateRequest,
    SimulateResponse,
    StepsResponse,
)
from app.services import mcp_deploy_service as svc

router = APIRouter(prefix="/api/mcp-deploy", tags=["mcp-deploy"])


@router.post("/steps", response_model=StepsResponse)
async def steps(config: DeployConfig = DeployConfig()) -> StepsResponse:
    """Return the full, parameterised deployment walkthrough. POST your config to
    render copy-paste-ready commands; the default config returns placeholder values."""
    return svc.get_steps(config)


@router.get("/steps", response_model=StepsResponse)
async def steps_default() -> StepsResponse:
    """Convenience GET with placeholder config (for first page load)."""
    return svc.get_steps(DeployConfig())


@router.post("/simulate", response_model=SimulateResponse)
async def simulate(req: SimulateRequest) -> SimulateResponse:
    """Simulate executing one step (no real AWS calls) — safe for live demos."""
    return svc.simulate(req.step_id, req.config)
