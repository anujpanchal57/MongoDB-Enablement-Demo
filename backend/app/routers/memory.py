"""Feature 2 — agentic memory routes (LangChain + LangGraph)."""
from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Query
from fastapi.concurrency import run_in_threadpool

from app.config import get_settings
from app.models.memory import (
    ChatRequest,
    ChatResponse,
    MemoryList,
    RecalledMemory,
)
from app.services.memory_agent import AgentUnavailable, run_chat
from app.services.memory_store import get_memory_store

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/memory", tags=["agentic-memory"])

# A scripted two-thread demo that proves cross-thread recall.
_DEMO_SCRIPT = {
    "user_id": "demo-user",
    "steps": [
        {
            "thread": "thread-A",
            "message": "Hi! I'm Alex. I'm vegetarian and I love hiking in the Swiss Alps.",
            "note": "Thread A — the agent learns and stores durable facts about Alex.",
        },
        {
            "thread": "thread-A",
            "message": "I'm also planning a trip for my anniversary next month.",
            "note": "Still thread A — more facts accumulate in long-term memory.",
        },
        {
            "thread": "thread-B",
            "message": "Can you suggest a restaurant and a weekend activity for me?",
            "note": "NEW thread B — watch the agent recall Alex is vegetarian & loves hiking, "
            "even though those were said in a different conversation.",
        },
    ],
}


@router.get("/demo-script")
async def demo_script() -> dict:
    """A guided sequence the presenter can click through to show cross-thread recall."""
    return _DEMO_SCRIPT


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    if not get_settings().has_mongodb:
        raise HTTPException(status_code=503, detail="MongoDB is not configured (set MONGODB_URI).")
    if not get_settings().has_voyage:
        raise HTTPException(status_code=503, detail="VOYAGE_API_KEY is not set (needed for memory recall).")
    try:
        out = await run_in_threadpool(run_chat, req.message, req.thread_id, req.user_id)
    except AgentUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        logger.exception("Agent chat failed")
        raise HTTPException(status_code=500, detail=f"Agent failed: {exc}") from exc

    return ChatResponse(
        reply=out["reply"],
        thread_id=req.thread_id,
        user_id=req.user_id,
        recalled=[RecalledMemory(**m) for m in out["recalled"]],
        saved=out["saved"],
        live=True,
    )


@router.get("/list", response_model=MemoryList)
async def list_memories(user_id: str = Query("demo-user", min_length=1)) -> MemoryList:
    if not get_settings().has_mongodb:
        raise HTTPException(status_code=503, detail="MongoDB is not configured (set MONGODB_URI).")
    memories = await get_memory_store().list_for_user(user_id)
    return MemoryList(user_id=user_id, count=len(memories), memories=memories)


@router.post("/clear")
async def clear_memories(user_id: str = Query("demo-user", min_length=1)) -> dict:
    if not get_settings().has_mongodb:
        raise HTTPException(status_code=503, detail="MongoDB is not configured (set MONGODB_URI).")
    deleted = await get_memory_store().clear(user_id)
    return {"user_id": user_id, "deleted": deleted}
