"""Feature 4 — Atlas automated embedding service.

The contrast with Feature 1 is the whole point of the demo:
  * Feature 1: we compute Voyage embeddings ourselves and store a vector field.
  * Feature 4: we store PLAIN TEXT only. Atlas generates embeddings automatically
    from the indexed text field (managed Voyage model), and at query time we pass
    a TEXT string in `$vectorSearch.query` — Atlas embeds the query for us.
"""
from __future__ import annotations

import copy
import logging
import time
from typing import Any

from app.config import get_settings
from app.data.destinations import DESTINATIONS
from app.db import get_database
from app.models.autoembed import (
    AutoEmbedSearchResponse,
    DestinationHit,
    SetupResponse,
    StatusResponse,
)

logger = logging.getLogger(__name__)

_PROJECTION = {
    "_id": 1,
    "name": 1,
    "country": 1,
    "region": 1,
    "description": 1,
    "tags": 1,
    "best_season": 1,
}


def _to_hit(doc: dict[str, Any]) -> DestinationHit:
    return DestinationHit(
        id=str(doc.get("_id")),
        name=doc.get("name") or "(unnamed)",
        country=doc.get("country"),
        region=doc.get("region"),
        description=doc.get("description"),
        tags=doc.get("tags") or [],
        best_season=doc.get("best_season"),
        score=doc.get("_score"),
    )


class AutoEmbedService:
    def __init__(self) -> None:
        self._s = get_settings()

    def _collection(self):
        return get_database()[self._s.autoembed_collection]

    def index_definition(self) -> dict[str, Any]:
        """The auto-embedding index definition shown in the UI. The `autoEmbed`
        field type with `modality: text` + a managed `model` is what makes Atlas
        generate embeddings automatically at index- and query-time."""
        return {
            "fields": [
                {
                    "type": "autoEmbed",
                    "path": self._s.autoembed_path,
                    "modality": "text",
                    "model": self._s.autoembed_model,
                }
            ]
        }

    async def _existing_index(self) -> dict | None:
        coll = self._collection()
        cursor = await coll.list_search_indexes()
        async for ix in cursor:
            if ix.get("name") == self._s.autoembed_index:
                return ix
        return None

    async def setup(self) -> SetupResponse:
        """Idempotently ingest the curated dataset (plain text) and create the
        automated-embedding vector index."""
        from pymongo.operations import SearchIndexModel

        coll = self._collection()

        existing_count = await coll.count_documents({})
        inserted = 0
        if existing_count == 0:
            await coll.insert_many([dict(d) for d in DESTINATIONS])
            inserted = len(DESTINATIONS)

        index_created = False
        if await self._existing_index() is None:
            await coll.create_search_index(
                SearchIndexModel(
                    definition=self.index_definition(),
                    name=self._s.autoembed_index,
                    type="vectorSearch",
                )
            )
            index_created = True

        msg = (
            "Setup complete. Atlas is generating embeddings for the index — this can "
            "take a minute. Check status until it is READY, then run a search."
        )
        return SetupResponse(
            collection=self._s.autoembed_collection,
            index=self._s.autoembed_index,
            model=self._s.autoembed_model,
            inserted=inserted or existing_count,
            index_created=index_created,
            index_definition=self.index_definition(),
            message=msg,
        )

    async def status(self) -> StatusResponse:
        coll = self._collection()
        count = await coll.count_documents({})
        ix = await self._existing_index()
        status = ix.get("status") if ix else None
        queryable = bool(ix.get("queryable")) if ix else False
        return StatusResponse(
            collection=self._s.autoembed_collection,
            document_count=count,
            index_name=self._s.autoembed_index,
            index_exists=ix is not None,
            index_status=status,
            queryable=queryable,
        )

    async def search(self, query: str, limit: int) -> AutoEmbedSearchResponse:
        coll = self._collection()
        stage = {
            "$vectorSearch": {
                "index": self._s.autoembed_index,
                "path": self._s.autoembed_path,
                # TEXT query — Atlas embeds it automatically. No client-side vector!
                "query": query,
                "numCandidates": max(limit * 15, 100),
                "limit": limit,
            }
        }
        pipeline = [
            stage,
            {"$set": {"_score": {"$meta": "vectorSearchScore"}}},
            {"$project": {**_PROJECTION, "_score": 1}},
        ]
        start = time.perf_counter()
        cursor = await coll.aggregate(pipeline)
        docs = await cursor.to_list(length=limit)
        took_ms = int((time.perf_counter() - start) * 1000)
        return AutoEmbedSearchResponse(
            query=query,
            count=len(docs),
            took_ms=took_ms,
            results=[_to_hit(d) for d in docs],
            query_used={"pipeline": copy.deepcopy(pipeline)},
        )


def get_autoembed_service() -> AutoEmbedService:
    return AutoEmbedService()
