"""Search service: full-text, vector, and hybrid (RRF) search over embedded_movies.

This is the centerpiece of Feature 1. Each strategy is a separate method so the
UI can run all three for the same query and show how the rankings differ.

  * full-text  -> Atlas Search `$search` (text operator over title/plot/genres/cast)
  * vector     -> Atlas `$vectorSearch` over the Voyage embedding field
  * hybrid     -> Reciprocal Rank Fusion of the two result lists, computed here in
                  Python so per-method ranks remain visible for the demo.
"""
from __future__ import annotations

import copy
import logging
import time
from typing import Any, Optional

from app.config import get_settings
from app.db import get_collection
from app.models.search import MovieHit, SearchMode, SearchResponse
from app.services.embeddings import get_embedding_service

logger = logging.getLogger(__name__)

# Fields returned to the client. Embedding arrays are deliberately excluded.
_PROJECTION = {
    "_id": 1,
    "title": 1,
    "year": 1,
    "plot": 1,
    "genres": 1,
    "cast": 1,
    "poster": 1,
    "imdb": 1,
}

# Atlas Search fields for full-text relevance, weighted toward title/plot.
_TEXT_PATHS = ["title", "plot", "fullplot", "genres", "cast"]


def _to_hit(doc: dict[str, Any]) -> MovieHit:
    """Map a raw Mongo document to the API MovieHit model."""
    imdb = doc.get("imdb") or {}
    rating = imdb.get("rating") if isinstance(imdb, dict) else None
    # Atlas stores year sometimes as a string like "1995è"; coerce defensively.
    year = doc.get("year")
    if isinstance(year, str):
        digits = "".join(ch for ch in year if ch.isdigit())[:4]
        year = int(digits) if digits else None
    return MovieHit(
        id=str(doc.get("_id")),
        title=doc.get("title") or "(untitled)",
        year=year,
        plot=doc.get("plot"),
        genres=doc.get("genres") or [],
        cast=doc.get("cast") or [],
        poster=doc.get("poster"),
        imdb_rating=float(rating) if isinstance(rating, (int, float)) else None,
        score=doc.get("_score"),
    )


def _display_pipeline(pipeline: list[dict]) -> list[dict]:
    """Return a copy of an aggregation pipeline safe to show in the UI: the
    `queryVector` (1024 floats) is replaced by a short preview string."""
    shown = copy.deepcopy(pipeline)
    for stage in shown:
        vs = stage.get("$vectorSearch")
        if vs and isinstance(vs.get("queryVector"), list):
            vec = vs["queryVector"]
            preview = ", ".join(f"{x:.4f}" for x in vec[:3])
            vs["queryVector"] = f"[{preview}, … {len(vec)} dims]"
    return shown


class SearchService:
    def __init__(self) -> None:
        self._settings = get_settings()

    # ------------------------------------------------------------------ #
    # Full-text
    # ------------------------------------------------------------------ #
    async def fulltext(
        self, query: str, limit: int, capture: Optional[dict] = None
    ) -> list[MovieHit]:
        coll = get_collection()
        pipeline = [
            {
                "$search": {
                    "index": self._settings.atlas_text_index,
                    "text": {"query": query, "path": _TEXT_PATHS},
                }
            },
            {"$limit": limit},
            {"$set": {"_score": {"$meta": "searchScore"}}},
            {"$project": {**_PROJECTION, "_score": 1}},
        ]
        if capture is not None:
            capture["fulltext"] = _display_pipeline(pipeline)
        # PyMongo async: aggregate() is a coroutine returning the cursor.
        cursor = await coll.aggregate(pipeline)
        docs = await cursor.to_list(length=limit)
        return [_to_hit(d) for d in docs]

    # ------------------------------------------------------------------ #
    # Vector
    # ------------------------------------------------------------------ #
    async def vector(
        self, query: str, limit: int, capture: Optional[dict] = None
    ) -> list[MovieHit]:
        coll = get_collection()
        query_vector = get_embedding_service().embed_query(query)
        pipeline = [
            {
                "$vectorSearch": {
                    "index": self._settings.atlas_vector_index,
                    "path": self._settings.vector_field,
                    "queryVector": query_vector,
                    "numCandidates": max(limit * 15, 150),
                    "limit": limit,
                }
            },
            {"$set": {"_score": {"$meta": "vectorSearchScore"}}},
            {"$project": {**_PROJECTION, "_score": 1}},
        ]
        if capture is not None:
            capture["vector"] = _display_pipeline(pipeline)
        cursor = await coll.aggregate(pipeline)
        docs = await cursor.to_list(length=limit)
        return [_to_hit(d) for d in docs]

    # ------------------------------------------------------------------ #
    # Hybrid (Reciprocal Rank Fusion)
    # ------------------------------------------------------------------ #
    async def hybrid(
        self, query: str, limit: int, rrf_k: int = 60, capture: Optional[dict] = None
    ) -> list[MovieHit]:
        """Fuse full-text and vector results with RRF.

        RRF score for a doc = sum over lists of 1 / (k + rank), rank being its
        1-based position in that list. We over-fetch each list so fusion has
        enough candidates, then keep the top `limit`.
        """
        fetch = min(max(limit * 3, 20), 100)
        text_hits = await self.fulltext(query, fetch, capture=capture)
        vec_hits = await self.vector(query, fetch, capture=capture)
        if capture is not None:
            capture["fusion"] = (
                f"Reciprocal Rank Fusion — score = Σ 1 / (k + rank) with k={rrf_k}, "
                f"over the top {fetch} candidates from each method; keep top {limit}."
            )

        fused: dict[str, MovieHit] = {}

        def _accumulate(hits: list[MovieHit], rank_attr: str) -> None:
            for rank, hit in enumerate(hits, start=1):
                entry = fused.get(hit.id)
                if entry is None:
                    # Copy so we don't mutate the per-method ranking objects.
                    entry = hit.model_copy()
                    entry.fused_score = 0.0
                    fused[hit.id] = entry
                entry.fused_score = (entry.fused_score or 0.0) + 1.0 / (rrf_k + rank)
                setattr(entry, rank_attr, rank)

        _accumulate(text_hits, "fulltext_rank")
        _accumulate(vec_hits, "vector_rank")

        ranked = sorted(fused.values(), key=lambda h: h.fused_score or 0.0, reverse=True)
        for hit in ranked:
            hit.score = hit.fused_score
        return ranked[:limit]

    # ------------------------------------------------------------------ #
    # Dispatch
    # ------------------------------------------------------------------ #
    async def search(
        self, query: str, mode: SearchMode, limit: int, rrf_k: int = 60
    ) -> SearchResponse:
        start = time.perf_counter()
        capture: dict[str, Any] = {}
        if mode is SearchMode.FULLTEXT:
            results = await self.fulltext(query, limit, capture=capture)
        elif mode is SearchMode.VECTOR:
            results = await self.vector(query, limit, capture=capture)
        else:
            results = await self.hybrid(query, limit, rrf_k=rrf_k, capture=capture)
        took_ms = int((time.perf_counter() - start) * 1000)
        return SearchResponse(
            mode=mode,
            query=query,
            count=len(results),
            took_ms=took_ms,
            results=results,
            live=True,
            query_used=capture,
        )


def get_search_service() -> SearchService:
    return SearchService()
