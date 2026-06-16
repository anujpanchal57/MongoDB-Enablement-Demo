"""Pydantic models for the search feature (request/response contracts)."""
from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class SearchMode(str, Enum):
    """The three search strategies the demo compares."""

    FULLTEXT = "fulltext"
    VECTOR = "vector"
    HYBRID = "hybrid"


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500, examples=["a heist that goes wrong"])
    mode: SearchMode = SearchMode.HYBRID
    limit: int = Field(10, ge=1, le=50)
    # RRF constant for hybrid fusion; exposed so the demo can show its effect.
    rrf_k: int = Field(60, ge=1, le=1000)


class MovieHit(BaseModel):
    """A single ranked result. Embedding vectors are intentionally omitted."""

    id: str
    title: str
    year: Optional[int] = None
    plot: Optional[str] = None
    genres: list[str] = Field(default_factory=list)
    cast: list[str] = Field(default_factory=list)
    poster: Optional[str] = None
    imdb_rating: Optional[float] = None

    # Scoring/ranking transparency — the heart of the demo.
    score: Optional[float] = None
    fulltext_rank: Optional[int] = None
    vector_rank: Optional[int] = None
    fused_score: Optional[float] = None


class SearchResponse(BaseModel):
    mode: SearchMode
    query: str
    count: int
    took_ms: int
    results: list[MovieHit]
    # True when results came from live Atlas; False if a fallback/empty path ran.
    live: bool = True
    note: Optional[str] = None
    # The actual query/pipeline executed, for display in the demo UI. For vector
    # search the queryVector is elided to a short preview. For hybrid this holds
    # both sub-pipelines plus a description of the fusion step.
    query_used: Optional[dict[str, Any]] = None
