"""Models for Feature 3 — guided MCP-server-on-AgentCore deployment walkthrough."""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class DeployConfig(BaseModel):
    """User-supplied values used to render real, copy-pasteable commands."""

    account_id: str = Field("123456789012", min_length=1, max_length=32)
    region: str = Field("us-east-1", min_length=1, max_length=32)
    repo_name: str = Field("mongodb-mcp-server", min_length=1, max_length=128)
    runtime_name: str = Field("mongodb_mcp", min_length=1, max_length=128)
    # Standard mongodb:// (mongodb+srv:// is unsupported by AgentCore).
    connection_string: str = Field("mongodb://<user>:<pass>@<host>:27017/?directConnection=true")


class DeployStep(BaseModel):
    id: str
    title: str
    summary: str
    commands: list[str] = Field(default_factory=list)
    env: dict[str, str] = Field(default_factory=dict)
    notes: list[str] = Field(default_factory=list)
    docs: Optional[str] = None


class StepsResponse(BaseModel):
    title: str
    source_repo: str
    prerequisites: list[str]
    steps: list[DeployStep]
    config: DeployConfig


class SimulateRequest(BaseModel):
    step_id: str
    config: DeployConfig = DeployConfig()


class SimulateResponse(BaseModel):
    step_id: str
    ok: bool
    simulated: bool = True
    output: str
    duration_ms: int
