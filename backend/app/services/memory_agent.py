"""Feature 2 — a LangGraph agent with MongoDB-backed memory.

Graph:  recall ──▶ agent ──▶ memorize

  * recall   : semantic-search the user's LONG-TERM memories (MongoDB + Voyage)
               and inject them into the system prompt.
  * agent    : call Claude (via AWS Bedrock / LangChain) with the running
               conversation. SHORT-TERM thread history is persisted by the
               LangGraph MongoDBSaver checkpointer, keyed by thread_id.
  * memorize : ask the model to extract durable facts about the user and store
               them as new long-term memories (recalled by future threads).

All heavy imports (langgraph, langchain_aws) are lazy so the rest of the app
boots even if these optional deps are absent. The agent runs synchronously and
is called from the async router via a threadpool.
"""
from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from typing import Annotated, Any, TypedDict

from app.config import get_settings
from app.services.embeddings import get_embedding_service
from app.services.memory_store import _cosine

logger = logging.getLogger(__name__)

# The agent's graph state. Defined at MODULE level (not inside _build_graph) so
# that LangGraph's get_type_hints() can resolve the annotations against this
# module's globals — `Annotated` and `add_messages` must live here too. Importing
# add_messages is guarded so the app still boots when langgraph is absent; in that
# case _build_graph() raises AgentUnavailable instead.
try:
    from langgraph.graph.message import add_messages

    class AgentState(TypedDict):
        messages: Annotated[list, add_messages]
        user_id: str
        thread_id: str
        recalled: list
        saved: list

except ImportError:  # pragma: no cover - exercised only without langgraph
    add_messages = None  # type: ignore[assignment]
    AgentState = None  # type: ignore[assignment]


class AgentUnavailable(RuntimeError):
    """Raised when the agent cannot run (missing deps or configuration)."""


# --- module-level lazy singletons (built on first use) ----------------------
_sync_client = None
_graph = None
_llm = None


def _client():
    global _sync_client
    if _sync_client is None:
        from pymongo import MongoClient

        s = get_settings()
        if not s.has_mongodb:
            raise AgentUnavailable("MongoDB is not configured (set MONGODB_URI).")
        _sync_client = MongoClient(s.mongodb_uri)
    return _sync_client


def _memory_collection():
    s = get_settings()
    return _client()[s.memory_db][s.memory_store_collection]


# --- long-term memory ops (sync, shared schema with MongoMemoryStore) -------
def _recall(user_id: str, query: str, k: int = 4) -> list[dict[str, Any]]:
    docs = list(_memory_collection().find({"user_id": user_id}))
    if not docs:
        return []
    q_vec = get_embedding_service().embed_query(query)
    scored = [
        (_cosine(q_vec, d.get("embedding", [])), d.get("text", ""), d.get("thread_id"))
        for d in docs
    ]
    scored.sort(key=lambda t: t[0], reverse=True)
    return [
        {"text": text, "score": round(score, 4), "thread_id": tid}
        for score, text, tid in scored[:k]
        if text
    ]


def _save(user_id: str, text: str, thread_id: str | None) -> bool:
    text = text.strip()
    coll = _memory_collection()
    if not text or coll.find_one({"user_id": user_id, "text": text}):
        return False
    embedding = get_embedding_service().embed([text], input_type="document")[0]
    coll.insert_one(
        {
            "user_id": user_id,
            "text": text,
            "embedding": embedding,
            "thread_id": thread_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
    )
    return True


# --- LLM + graph ------------------------------------------------------------
def _build_llm():
    global _llm
    if _llm is not None:
        return _llm
    s = get_settings()
    try:
        import boto3
        from langchain_aws import ChatBedrockConverse
    except ImportError as exc:  # pragma: no cover - depends on optional deps
        raise AgentUnavailable(
            "langchain-aws / boto3 not installed — run pip install -r requirements.txt."
        ) from exc

    # Build an explicit boto3 Session so we can support static keys, temporary
    # credentials (session token), or a named profile — and fall back to the
    # default credential chain (env / shared config / IAM role) when none given.
    session_kwargs: dict[str, Any] = {"region_name": s.aws_region}
    if s.aws_access_key_id and s.aws_secret_access_key:
        session_kwargs["aws_access_key_id"] = s.aws_access_key_id
        session_kwargs["aws_secret_access_key"] = s.aws_secret_access_key
        if s.aws_session_token:
            session_kwargs["aws_session_token"] = s.aws_session_token
    elif s.aws_profile:
        session_kwargs["profile_name"] = s.aws_profile

    session = boto3.Session(**session_kwargs)
    bedrock = session.client("bedrock-runtime")
    _llm = ChatBedrockConverse(
        model=s.bedrock_chat_model_id, client=bedrock, temperature=0.3, max_tokens=1024
    )
    return _llm


def _system_prompt(recalled: list[dict]) -> str:
    base = (
        "You are a helpful, friendly travel & lifestyle assistant with long-term memory. "
        "Use any remembered facts about the user to personalise your answer naturally. "
        "Do not claim to remember things that are not listed."
    )
    if not recalled:
        return base + "\n\n(no long-term memories about this user yet)"
    lines = "\n".join(f"- {m['text']}" for m in recalled)
    return f"{base}\n\nWhat you remember about this user:\n{lines}"


def _extract_facts(llm, last_user: str, reply: str) -> list[str]:
    """Ask the model for 0–3 durable facts about the user worth remembering."""
    from langchain_core.messages import HumanMessage, SystemMessage

    instruction = (
        "From the user's latest message, extract durable facts worth remembering "
        "long-term (preferences, constraints, identity, goals). Ignore transient "
        "questions and small talk. Return ONLY a JSON array of short strings "
        '(e.g. ["The user is vegetarian", "The user loves hiking"]). '
        "Return [] if nothing is worth remembering."
    )
    try:
        resp = llm.invoke(
            [SystemMessage(content=instruction), HumanMessage(content=last_user)]
        )
        text = resp.content if isinstance(resp.content, str) else str(resp.content)
        match = re.search(r"\[.*\]", text, re.DOTALL)
        if not match:
            return []
        facts = json.loads(match.group(0))
        return [str(f).strip() for f in facts if isinstance(f, (str,)) and str(f).strip()][:3]
    except Exception as exc:  # noqa: BLE001 - extraction is best-effort
        logger.warning("Fact extraction failed: %s", exc)
        return []


def _build_graph():
    global _graph
    if _graph is not None:
        return _graph
    try:
        from langgraph.checkpoint.mongodb import MongoDBSaver
        from langgraph.graph import END, START, StateGraph
    except ImportError as exc:  # pragma: no cover
        raise AgentUnavailable(
            "langgraph / langgraph-checkpoint-mongodb not installed."
        ) from exc
    if AgentState is None:  # pragma: no cover - guarded at import
        raise AgentUnavailable("langgraph not available — cannot build agent state schema.")

    llm = _build_llm()
    s = get_settings()

    def recall_node(state: dict) -> dict:
        last = _last_human_text(state["messages"])
        return {"recalled": _recall(state["user_id"], last) if last else []}

    def agent_node(state: dict) -> dict:
        from langchain_core.messages import SystemMessage

        sys = _system_prompt(state.get("recalled", []))
        resp = llm.invoke([SystemMessage(content=sys)] + state["messages"])
        return {"messages": [resp]}

    def memorize_node(state: dict) -> dict:
        last = _last_human_text(state["messages"])
        reply = state["messages"][-1].content if state["messages"] else ""
        reply = reply if isinstance(reply, str) else str(reply)
        facts = _extract_facts(llm, last, reply)
        saved = [f for f in facts if _save(state["user_id"], f, state["thread_id"])]
        return {"saved": saved}

    builder = StateGraph(AgentState)
    builder.add_node("recall", recall_node)
    builder.add_node("agent", agent_node)
    builder.add_node("memorize", memorize_node)
    builder.add_edge(START, "recall")
    builder.add_edge("recall", "agent")
    builder.add_edge("agent", "memorize")
    builder.add_edge("memorize", END)

    checkpointer = MongoDBSaver(
        _client(),
        db_name=s.memory_db,
        checkpoint_collection_name=s.memory_checkpoint_collection,
    )
    _graph = builder.compile(checkpointer=checkpointer)
    return _graph


def _last_human_text(messages: list) -> str:
    for m in reversed(messages):
        # Support both dict-form and LangChain message objects.
        if isinstance(m, dict) and m.get("role") in ("user", "human"):
            return str(m.get("content", ""))
        if getattr(m, "type", None) == "human":
            return str(getattr(m, "content", ""))
    return ""


def run_chat(message: str, thread_id: str, user_id: str) -> dict[str, Any]:
    """Synchronously run one agent turn. Raises AgentUnavailable on config/dep gaps."""
    graph = _build_graph()
    config = {"configurable": {"thread_id": f"{user_id}:{thread_id}"}}
    state_in = {
        "messages": [{"role": "user", "content": message}],
        "user_id": user_id,
        "thread_id": thread_id,
        "recalled": [],
        "saved": [],
    }
    result = graph.invoke(state_in, config=config)
    reply_msg = result["messages"][-1]
    reply = reply_msg.content if not isinstance(reply_msg, dict) else reply_msg.get("content", "")
    reply = reply if isinstance(reply, str) else str(reply)
    return {
        "reply": reply,
        "recalled": result.get("recalled", []),
        "saved": result.get("saved", []),
    }
