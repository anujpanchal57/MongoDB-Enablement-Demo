"""Feature 4 — Atlas automated embedding routes."""
from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from app.config import get_settings
from app.data.destinations import DESTINATIONS
from app.models.autoembed import (
    AutoEmbedSearchRequest,
    AutoEmbedSearchResponse,
    SetupResponse,
    StatusResponse,
)
from app.services.autoembed_service import get_autoembed_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/autoembed", tags=["auto-embedding"])

# Queries chosen so semantic auto-embedding clearly beats keyword matching:
# none of these words appear literally in the target descriptions.
_EXAMPLES = [
    {"label": "Romantic island honeymoon", "query": "a romantic secluded island honeymoon"},
    {"label": "Adrenaline & adventure", "query": "extreme adventure sports and adrenaline"},
    {"label": "Ancient ruins & history", "query": "ancient civilizations and archaeological ruins"},
    {"label": "Snowy mountain skiing", "query": "snowy mountain peaks for skiing"},
    {"label": "See exotic wildlife", "query": "see exotic wild animals up close"},
    {"label": "Bustling big city energy", "query": "vibrant big city nightlife and culture"},
]


def _require_mongo() -> None:
    if not get_settings().has_mongodb:
        raise HTTPException(status_code=503, detail="MongoDB is not configured (set MONGODB_URI).")


@router.get("/dataset")
async def dataset() -> dict:
    """Preview the curated dataset + the auto-embedding index definition."""
    svc = get_autoembed_service()
    return {
        "count": len(DESTINATIONS),
        "sample": DESTINATIONS[:6],
        "index_definition": svc.index_definition(),
        "model": get_settings().autoembed_model,
        "examples": _EXAMPLES,
    }


@router.post("/setup", response_model=SetupResponse)
async def setup() -> SetupResponse:
    _require_mongo()
    try:
        return await get_autoembed_service().setup()
    except Exception as exc:  # noqa: BLE001
        logger.exception("Auto-embed setup failed")
        raise HTTPException(status_code=500, detail=f"Setup failed: {exc}") from exc


@router.get("/status", response_model=StatusResponse)
async def status() -> StatusResponse:
    _require_mongo()
    try:
        return await get_autoembed_service().status()
    except Exception as exc:  # noqa: BLE001
        logger.exception("Auto-embed status failed")
        raise HTTPException(status_code=500, detail=f"Status failed: {exc}") from exc


@router.post("", response_model=AutoEmbedSearchResponse)
async def search(req: AutoEmbedSearchRequest) -> AutoEmbedSearchResponse:
    _require_mongo()
    try:
        return await get_autoembed_service().search(req.query, req.limit)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Auto-embed search failed")
        raise HTTPException(
            status_code=500,
            detail=f"Search failed (is the index READY?): {exc}",
        ) from exc
