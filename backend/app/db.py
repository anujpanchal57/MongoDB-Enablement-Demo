"""Async MongoDB Atlas client lifecycle.

Uses PyMongo's native async client (`AsyncMongoClient`, PyMongo >= 4.9) so we
avoid a separate Motor dependency. The client is created lazily and shared for
the process lifetime; FastAPI's lifespan handler opens/closes it.
"""
from __future__ import annotations

import logging
from typing import Optional

from pymongo import AsyncMongoClient
from pymongo.asynchronous.collection import AsyncCollection
from pymongo.asynchronous.database import AsyncDatabase

from app.config import get_settings

logger = logging.getLogger(__name__)

_client: Optional[AsyncMongoClient] = None


async def connect() -> None:
    """Open the shared Atlas client (idempotent). Safe to call with no URI set;
    the app still boots so non-DB screens and docs work in a dev environment."""
    global _client
    if _client is not None:
        return
    settings = get_settings()
    if not settings.has_mongodb:
        logger.warning("MONGODB_URI not set — MongoDB features will be unavailable.")
        return
    _client = AsyncMongoClient(settings.mongodb_uri, serverSelectionTimeoutMS=8000)
    logger.info("MongoDB async client initialised.")


async def disconnect() -> None:
    """Close the shared client on shutdown."""
    global _client
    if _client is not None:
        await _client.close()
        _client = None
        logger.info("MongoDB client closed.")


def get_client() -> AsyncMongoClient:
    if _client is None:
        raise RuntimeError(
            "MongoDB client is not initialised. Is MONGODB_URI set in your .env?"
        )
    return _client


def get_database() -> AsyncDatabase:
    return get_client()[get_settings().mongodb_db]


def get_collection() -> AsyncCollection:
    """The primary collection used by the search feature (embedded_movies)."""
    return get_database()[get_settings().mongodb_collection]


async def ping() -> bool:
    """Return True if Atlas responds to a ping; False otherwise."""
    if _client is None:
        return False
    try:
        await _client.admin.command("ping")
        return True
    except Exception as exc:  # noqa: BLE001 - surface as boolean health
        logger.warning("MongoDB ping failed: %s", exc)
        return False
