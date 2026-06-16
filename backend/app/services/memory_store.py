"""Long-term agentic memory backed by MongoDB.

Each memory is one document: { user_id, text, embedding, thread_id, created_at }.
Recall embeds the query with Voyage and ranks the user's memories by cosine
similarity. For a demo the per-user memory set is small, so we rank in Python —
at scale you would store these in an Atlas Vector Search index (or LangGraph's
MongoDBStore) and use `$vectorSearch`. The interface here mirrors that intent.
"""
from __future__ import annotations

import logging
import math
from datetime import datetime, timezone

from app.config import get_settings
from app.db import get_client
from app.models.memory import MemoryItem, RecalledMemory
from app.services.embeddings import get_embedding_service

logger = logging.getLogger(__name__)


def _cosine(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


class MongoMemoryStore:
    """CRUD + semantic recall for long-term memories."""

    def __init__(self) -> None:
        self._s = get_settings()

    def _collection(self):
        return get_client()[self._s.memory_db][self._s.memory_store_collection]

    async def save(self, user_id: str, text: str, thread_id: str | None = None) -> str:
        """Embed and persist one memory. Skips near-duplicates of existing text."""
        text = text.strip()
        if not text:
            return ""
        coll = self._collection()
        # Cheap exact-dedupe so the demo doesn't accumulate identical facts.
        if await coll.find_one({"user_id": user_id, "text": text}):
            return ""
        embedding = get_embedding_service().embed([text], input_type="document")[0]
        doc = {
            "user_id": user_id,
            "text": text,
            "embedding": embedding,
            "thread_id": thread_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        result = await coll.insert_one(doc)
        return str(result.inserted_id)

    async def recall(self, user_id: str, query: str, k: int = 4) -> list[RecalledMemory]:
        """Return the user's top-k memories most similar to the query."""
        coll = self._collection()
        cursor = coll.find({"user_id": user_id})
        docs = await cursor.to_list(length=500)
        if not docs:
            return []
        q_vec = get_embedding_service().embed_query(query)
        scored = [
            (
                _cosine(q_vec, d.get("embedding", [])),
                d.get("text", ""),
                d.get("thread_id"),
            )
            for d in docs
        ]
        scored.sort(key=lambda t: t[0], reverse=True)
        return [
            RecalledMemory(text=text, score=round(score, 4), thread_id=tid)
            for score, text, tid in scored[:k]
            if text
        ]

    async def list_for_user(self, user_id: str) -> list[MemoryItem]:
        coll = self._collection()
        cursor = coll.find({"user_id": user_id}).sort("created_at", -1)
        docs = await cursor.to_list(length=500)
        return [
            MemoryItem(
                id=str(d.get("_id")),
                user_id=d.get("user_id"),
                text=d.get("text", ""),
                thread_id=d.get("thread_id"),
                created_at=d.get("created_at"),
            )
            for d in docs
        ]

    async def clear(self, user_id: str) -> int:
        coll = self._collection()
        result = await coll.delete_many({"user_id": user_id})
        return result.deleted_count


def get_memory_store() -> MongoMemoryStore:
    return MongoMemoryStore()
