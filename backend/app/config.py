"""Application configuration, loaded from environment / repo-root `.env`.

All settings are read once and cached via `get_settings()`. Nothing here
connects to a service — it only declares what the app needs to run.
"""
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Repo root is two levels up from this file (backend/app/config.py -> repo root).
_REPO_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Strongly-typed view of the environment. See `.env.example` for docs."""

    model_config = SettingsConfigDict(
        env_file=(_REPO_ROOT / ".env", "backend/.env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # MongoDB Atlas
    mongodb_uri: str = ""
    mongodb_db: str = "sample_mflix"
    mongodb_collection: str = "embedded_movies"
    atlas_text_index: str = "default"
    atlas_vector_index: str = "vector_index"

    # Voyage AI embeddings
    voyage_api_key: str = ""
    voyage_model: str = "voyage-3"
    voyage_embedding_dim: int = 1024
    vector_field: str = "plot_embedding_voyage"

    # Feature 4 — Atlas automated embedding (Voyage managed by Atlas).
    autoembed_collection: str = "auto_embedded_destinations"
    autoembed_index: str = "autoembed_vector_index"
    autoembed_path: str = "description"
    # Atlas-managed auto-embed model. Supported set (per Atlas): voyage-4,
    # voyage-4-large, voyage-4-lite, voyage-code-3. (Distinct from VOYAGE_MODEL,
    # which is the client-side model used for Features 1 & 2.)
    autoembed_model: str = "voyage-4"

    # Feature 2 — agentic memory (LangGraph + MongoDB).
    memory_db: str = "agentic_memory"
    memory_checkpoint_collection: str = "thread_checkpoints"
    memory_store_collection: str = "long_term_memories"

    # AWS / Bedrock (chat/agent LLM for Feature 2).
    aws_region: str = "us-east-1"
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    # Required when using TEMPORARY credentials (AWS SSO / assumed role / STS).
    aws_session_token: str = ""
    # Optional named profile from ~/.aws/credentials; used when keys are blank.
    aws_profile: str = ""
    bedrock_chat_model_id: str = "anthropic.claude-3-5-sonnet-20240620-v1:0"

    # Server
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    cors_origins: str = "http://localhost:3000"

    @property
    def cors_origin_list(self) -> list[str]:
        """CORS_ORIGINS as a clean list."""
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def has_mongodb(self) -> bool:
        return bool(self.mongodb_uri)

    @property
    def has_voyage(self) -> bool:
        return bool(self.voyage_api_key)


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()
