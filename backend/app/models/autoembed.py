"""Pydantic models for Feature 4 — Atlas automated embedding."""
from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class AutoEmbedSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500, examples=["remote tropical island escape"])
    limit: int = Field(8, ge=1, le=50)


class DestinationHit(BaseModel):
    id: str
    name: str
    country: Optional[str] = None
    region: Optional[str] = None
    description: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    best_season: Optional[str] = None
    score: Optional[float] = None


class AutoEmbedSearchResponse(BaseModel):
    query: str
    count: int
    took_ms: int
    results: list[DestinationHit]
    # The $vectorSearch stage executed — note it carries a TEXT `query`, not a vector.
    query_used: Optional[dict[str, Any]] = None


class SetupResponse(BaseModel):
    collection: str
    index: str
    model: str
    inserted: int
    index_created: bool
    index_definition: dict[str, Any]
    message: str


class StatusResponse(BaseModel):
    collection: str
    document_count: int
    index_name: str
    index_exists: bool
    index_status: Optional[str] = None  # e.g. BUILDING, READY
    queryable: bool = False
