"""Search API routes (Feature 1)."""
from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Query

from app.config import get_settings
from app.db import ping
from app.models.search import SearchMode, SearchRequest, SearchResponse
from app.services.search_service import get_search_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/search", tags=["search"])


# Curated example queries that produce visibly different rankings across modes.
# These power the "click to demo" chips in the UI.
_EXAMPLE_QUERIES = [
    {
        "label": "Heist gone wrong",
        "query": "a heist that goes wrong",
        "why": "Vector search surfaces thematically-similar crime films even without the words 'heist' in the plot.",
    },
    {
        "label": "Space exploration & isolation",
        "query": "loneliness of space exploration",
        "why": "Semantic search shines: few plots use these exact words, but many match the concept.",
    },
    {
        "label": "Exact title: The Godfather",
        "query": "The Godfather",
        "why": "Full-text wins on exact titles; vector may drift to thematically-similar mob films.",
    },
    {
        "label": "Coming of age friendship",
        "query": "coming of age story about friendship",
        "why": "Hybrid blends keyword precision with semantic recall for the strongest list.",
    },
]


@router.get("/examples")
async def examples() -> dict:
    """Curated demo queries with an explanation of what each one illustrates."""
    return {"examples": _EXAMPLE_QUERIES}


@router.post("", response_model=SearchResponse)
async def run_search(req: SearchRequest) -> SearchResponse:
    """Run a single search in the requested mode."""
    if not get_settings().has_mongodb:
        raise HTTPException(status_code=503, detail="MongoDB is not configured (set MONGODB_URI).")
    try:
        return await get_search_service().search(
            query=req.query, mode=req.mode, limit=req.limit, rrf_k=req.rrf_k
        )
    except RuntimeError as exc:
        # e.g. missing Voyage key on a vector/hybrid request.
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        logger.exception("Search failed")
        raise HTTPException(status_code=500, detail=f"Search failed: {exc}") from exc


@router.get("/compare")
async def compare(
    q: str = Query(..., min_length=1, max_length=500),
    limit: int = Query(10, ge=1, le=50),
) -> dict:
    """Run all three modes for the same query in one call — the side-by-side
    comparison that is the centerpiece of the demo."""
    if not get_settings().has_mongodb:
        raise HTTPException(status_code=503, detail="MongoDB is not configured (set MONGODB_URI).")
    svc = get_search_service()
    try:
        out = {}
        for mode in (SearchMode.FULLTEXT, SearchMode.VECTOR, SearchMode.HYBRID):
            out[mode.value] = await svc.search(query=q, mode=mode, limit=limit)
        return {
            "query": q,
            "modes": {k: v.model_dump() for k, v in out.items()},
            "atlas_reachable": await ping(),
        }
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        logger.exception("Compare failed")
        raise HTTPException(status_code=500, detail=f"Compare failed: {exc}") from exc
