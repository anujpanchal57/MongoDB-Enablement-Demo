"""Tests for Feature 2 (agentic memory). Hermetic — the LLM/graph is mocked and
no live MongoDB is required."""
import app.routers.memory as memory_router
from app.services.memory_store import _cosine


def test_cosine_similarity_basic():
    assert _cosine([1, 0], [1, 0]) == 1.0
    assert _cosine([1, 0], [0, 1]) == 0.0
    assert round(_cosine([1, 1], [1, 0]), 4) == 0.7071
    # Degenerate inputs are safe.
    assert _cosine([], [1]) == 0.0
    assert _cosine([0, 0], [0, 0]) == 0.0


def test_extract_facts_parses_json_array(monkeypatch):
    from app.services import memory_agent

    class _Resp:
        content = 'Sure. ["The user is vegetarian", "The user loves hiking"] done'

    class _LLM:
        def invoke(self, messages):
            return _Resp()

    facts = memory_agent._extract_facts(_LLM(), "I'm vegetarian and love hiking", "ok")
    assert facts == ["The user is vegetarian", "The user loves hiking"]


def test_extract_facts_handles_no_array(monkeypatch):
    from app.services import memory_agent

    class _Resp:
        content = "Nothing worth remembering here."

    class _LLM:
        def invoke(self, messages):
            return _Resp()

    assert memory_agent._extract_facts(_LLM(), "what time is it?", "ok") == []


def test_system_prompt_includes_recalled_memories():
    from app.services.memory_agent import _system_prompt

    p = _system_prompt([{"text": "The user is vegetarian", "score": 0.9}])
    assert "vegetarian" in p
    empty = _system_prompt([])
    assert "no long-term memories" in empty.lower()


def test_chat_requires_mongodb(monkeypatch):
    from fastapi.testclient import TestClient

    from app.config import get_settings
    from app.main import create_app

    get_settings.cache_clear()
    client = TestClient(create_app())
    r = client.post(
        "/api/memory/chat",
        json={"message": "hi", "thread_id": "t1", "user_id": "u1"},
    )
    assert r.status_code == 503


def test_demo_script_endpoint():
    from fastapi.testclient import TestClient

    from app.main import create_app

    client = TestClient(create_app())
    r = client.get("/api/memory/demo-script")
    assert r.status_code == 200
    body = r.json()
    assert len(body["steps"]) >= 2
    # Demo must span at least two distinct threads to prove cross-thread recall.
    threads = {s["thread"] for s in body["steps"]}
    assert len(threads) >= 2


def test_agent_state_schema_resolves_for_langgraph():
    """Regression: `from __future__ import annotations` stringifies AgentState's
    hints, so StateGraph(AgentState) must resolve `Annotated`/`add_messages` from
    module globals. This raised NameError when State was defined inside _build_graph."""
    from langgraph.graph import StateGraph

    from app.services.memory_agent import AgentState

    assert AgentState is not None
    graph = StateGraph(AgentState)
    # The reducer-backed 'messages' channel must be present.
    assert "messages" in graph.channels
    assert {"user_id", "thread_id", "recalled", "saved"} <= set(graph.channels)


def test_last_human_text_supports_dict_and_objects():
    from app.services.memory_agent import _last_human_text

    assert _last_human_text([{"role": "user", "content": "hello"}]) == "hello"

    class _Msg:
        type = "human"
        content = "hi there"

    assert _last_human_text([_Msg()]) == "hi there"
