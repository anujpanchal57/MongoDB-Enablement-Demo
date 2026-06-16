"""Tests for Feature 3 (MCP-on-AgentCore guided walkthrough). Fully hermetic."""
from fastapi.testclient import TestClient

from app.main import create_app
from app.models.mcp_deploy import DeployConfig
from app.services import mcp_deploy_service as svc

client = TestClient(create_app())


def test_steps_render_config_into_commands():
    cfg = DeployConfig(account_id="999000111222", region="eu-west-1", repo_name="my-mcp")
    steps = svc.build_steps(cfg)
    ids = [s.id for s in steps]
    assert ids == ["ecr-repo", "ecr-auth", "build", "push", "configure", "invoke", "monitor"]
    joined = "\n".join(c for s in steps for c in s.commands)
    # Config values must be substituted into the real commands.
    assert "999000111222.dkr.ecr.eu-west-1.amazonaws.com/my-mcp" in joined
    assert "--platform linux/arm64" in joined


def test_configure_step_sets_required_env():
    steps = {s.id: s for s in svc.build_steps(DeployConfig())}
    env = steps["configure"].env
    assert env["MDB_MCP_EXTERNALLY_MANAGED_SESSIONS"] == "true"
    assert env["MDB_MCP_HTTP_RESPONSE_TYPE"] == "json"
    assert "MDB_MCP_CONNECTION_STRING" in env


def test_steps_endpoint_default():
    r = client.get("/api/mcp-deploy/steps")
    assert r.status_code == 200
    body = r.json()
    assert "agentcore" in body["source_repo"].lower() or "mongodb-mcp-server" in body["source_repo"]
    assert len(body["steps"]) == 7
    assert len(body["prerequisites"]) >= 3


def test_simulate_returns_output_per_step():
    for step_id in ["ecr-repo", "build", "invoke", "monitor"]:
        r = client.post("/api/mcp-deploy/simulate", json={"step_id": step_id, "config": {}})
        assert r.status_code == 200
        body = r.json()
        assert body["ok"] is True
        assert body["simulated"] is True
        assert len(body["output"]) > 0


def test_simulate_invoke_lists_tools():
    r = client.post("/api/mcp-deploy/simulate", json={"step_id": "invoke", "config": {}})
    assert "tools" in r.json()["output"]


def test_simulate_unknown_step_fails_gracefully():
    r = client.post("/api/mcp-deploy/simulate", json={"step_id": "nope", "config": {}})
    assert r.status_code == 200
    assert r.json()["ok"] is False
