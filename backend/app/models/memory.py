"""Pydantic models for Feature 2 — agentic memory (LangChain + LangGraph)."""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    # thread_id scopes SHORT-TERM memory (the running conversation).
    thread_id: str = Field(..., min_length=1, max_length=128)
    # user_id scopes LONG-TERM memory (recalled across threads).
    user_id: str = Field("demo-user", min_length=1, max_length=128)


class RecalledMemory(BaseModel):
    text: str
    score: float
    thread_id: Optional[str] = None


class ChatResponse(BaseModel):
    reply: str
    thread_id: str
    user_id: str
    # Long-term memories the agent retrieved to answer this turn.
    recalled: list[RecalledMemory] = Field(default_factory=list)
    # New long-term memories the agent chose to persist this turn.
    saved: list[str] = Field(default_factory=list)
    # Whether the response came from a live LLM (vs an error/degraded path).
    live: bool = True
    note: Optional[str] = None


class MemoryItem(BaseModel):
    id: str
    user_id: str
    text: str
    thread_id: Optional[str] = None
    created_at: Optional[str] = None


class MemoryList(BaseModel):
    user_id: str
    count: int
    memories: list[MemoryItem]
