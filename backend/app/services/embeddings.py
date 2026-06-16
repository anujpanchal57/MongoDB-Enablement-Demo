"""Voyage AI embedding service.

Wraps the Voyage client so the rest of the app depends on a small, testable
interface rather than the SDK directly. Used for query embeddings at search
time and document embeddings in the seed script.
"""
from __future__ import annotations

import logging
from typing import Literal

import voyageai

from app.config import get_settings

logger = logging.getLogger(__name__)

InputType = Literal["query", "document"]


class EmbeddingService:
    """Thin wrapper around the Voyage embeddings API."""

    def __init__(self) -> None:
        settings = get_settings()
        self._model = settings.voyage_model
        self._dim = settings.voyage_embedding_dim
        # voyageai reads VOYAGE_API_KEY from env; pass explicitly for clarity.
        self._client = voyageai.Client(api_key=settings.voyage_api_key or None)

    @property
    def dimension(self) -> int:
        return self._dim

    def embed(self, texts: list[str], input_type: InputType = "document") -> list[list[float]]:
        """Embed a batch of texts. `input_type` lets Voyage optimise asymmetric
        query-vs-document retrieval."""
        if not texts:
            return []
        result = self._client.embed(texts, model=self._model, input_type=input_type)
        return result.embeddings

    def embed_query(self, text: str) -> list[float]:
        """Embed a single search query."""
        return self.embed([text], input_type="query")[0]


_service: EmbeddingService | None = None


def get_embedding_service() -> EmbeddingService:
    """Cached singleton. Raises a clear error if the API key is missing."""
    global _service
    if _service is None:
        if not get_settings().has_voyage:
            raise RuntimeError(
                "VOYAGE_API_KEY is not set — vector/hybrid search requires Voyage embeddings."
            )
        _service = EmbeddingService()
    return _service
