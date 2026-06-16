"""FastAPI application entrypoint for the MongoDB-on-AWS demo backend.

Run locally:  uvicorn app.main:app --reload --port 8000
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.db import connect, disconnect, ping
from app.routers import autoembed, mcp_deploy, memory, search, stream

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Open the Atlas client on startup, close it on shutdown."""
    await connect()
    yield
    await disconnect()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="MongoDB on AWS — Demo API",
        description="Backend for the MongoDB Atlas + AWS demonstration app.",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(search.router)
    app.include_router(autoembed.router)
    app.include_router(memory.router)
    app.include_router(mcp_deploy.router)
    app.include_router(stream.router)

    @app.get("/", tags=["meta"])
    async def root() -> dict:
        return {"name": "MongoDB on AWS — Demo API", "version": "0.1.0", "docs": "/docs"}

    @app.get("/health", tags=["meta"])
    async def health() -> dict:
        """Liveness + dependency status for demo confidence checks."""
        return {
            "status": "ok",
            "mongodb_configured": settings.has_mongodb,
            "mongodb_reachable": await ping(),
            "voyage_configured": settings.has_voyage,
        }

    return app


app = create_app()
