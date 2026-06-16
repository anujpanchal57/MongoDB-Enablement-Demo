"""One-time setup for Feature 1 (Search).

Does three things against your Atlas cluster:

  1. Adds a Voyage embedding field (`plot_embedding_voyage`, 1024-dim) to each
     embedded_movies document that has a plot but no Voyage embedding yet.
  2. Creates the Atlas Search (full-text) index.
  3. Creates the Atlas Vector Search index on the Voyage field.

Run from the backend/ directory after filling in `.env`:

    python -m scripts.seed_search_indexes            # embeddings + both indexes
    python -m scripts.seed_search_indexes --indexes-only
    python -m scripts.seed_search_indexes --embeddings-only --limit 500

Uses the synchronous PyMongo client (simpler for a batch script).
"""
from __future__ import annotations

import argparse
import sys
import time

import voyageai
from pymongo import MongoClient, UpdateOne
from pymongo.operations import SearchIndexModel

# Import the app settings so the script and server share one config source.
sys.path.insert(0, ".")
from app.config import get_settings  # noqa: E402

BATCH = 96  # Voyage batch size cap is generous; keep batches modest for safety.


def _embed_documents(settings, limit: int | None) -> int:
    client = MongoClient(settings.mongodb_uri)
    coll = client[settings.mongodb_db][settings.mongodb_collection]
    vo = voyageai.Client(api_key=settings.voyage_api_key or None)

    query = {
        "plot": {"$exists": True, "$ne": ""},
        settings.vector_field: {"$exists": False},
    }
    total = coll.count_documents(query)
    if limit:
        total = min(total, limit)
    print(f"Documents needing a Voyage embedding: {total}")
    if total == 0:
        return 0

    processed = 0
    cursor = coll.find(query, {"plot": 1, "title": 1}).limit(limit or 0)
    batch: list[dict] = []

    def flush(batch: list[dict]) -> int:
        texts = [f"{d.get('title', '')}. {d['plot']}" for d in batch]
        vectors = vo.embed(texts, model=settings.voyage_model, input_type="document").embeddings
        ops = [
            UpdateOne({"_id": d["_id"]}, {"$set": {settings.vector_field: vec}})
            for d, vec in zip(batch, vectors)
        ]
        coll.bulk_write(ops, ordered=False)
        return len(ops)

    for doc in cursor:
        batch.append(doc)
        if len(batch) >= BATCH:
            processed += flush(batch)
            print(f"  embedded {processed}/{total}")
            batch = []
            time.sleep(0.2)  # gentle pacing for rate limits
    if batch:
        processed += flush(batch)
        print(f"  embedded {processed}/{total}")

    client.close()
    return processed


def _create_indexes(settings) -> None:
    client = MongoClient(settings.mongodb_uri)
    coll = client[settings.mongodb_db][settings.mongodb_collection]
    existing = {ix["name"] for ix in coll.list_search_indexes()}

    # 1. Full-text search index (dynamic mapping covers all string fields).
    if settings.atlas_text_index not in existing:
        coll.create_search_index(
            SearchIndexModel(
                definition={"mappings": {"dynamic": True}},
                name=settings.atlas_text_index,
                type="search",
            )
        )
        print(f"Created full-text search index: {settings.atlas_text_index}")
    else:
        print(f"Full-text index already exists: {settings.atlas_text_index}")

    # 2. Vector search index on the Voyage embedding field.
    if settings.atlas_vector_index not in existing:
        coll.create_search_index(
            SearchIndexModel(
                definition={
                    "fields": [
                        {
                            "type": "vector",
                            "path": settings.vector_field,
                            "numDimensions": settings.voyage_embedding_dim,
                            "similarity": "cosine",
                        }
                    ]
                },
                name=settings.atlas_vector_index,
                type="vectorSearch",
            )
        )
        print(f"Created vector search index: {settings.atlas_vector_index}")
    else:
        print(f"Vector index already exists: {settings.atlas_vector_index}")

    print("\nNote: Atlas builds search indexes asynchronously — they may take a")
    print("minute or two to become queryable. Check status in the Atlas UI.")
    client.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed Voyage embeddings + Atlas search indexes.")
    parser.add_argument("--embeddings-only", action="store_true")
    parser.add_argument("--indexes-only", action="store_true")
    parser.add_argument("--limit", type=int, default=None, help="Cap docs embedded (for quick tests).")
    args = parser.parse_args()

    settings = get_settings()
    if not settings.has_mongodb:
        sys.exit("ERROR: MONGODB_URI is not set. Fill in .env first.")

    do_embed = not args.indexes_only
    do_index = not args.embeddings_only

    if do_embed:
        if not settings.has_voyage:
            sys.exit("ERROR: VOYAGE_API_KEY is not set — required for embeddings.")
        print("== Embedding documents with Voyage ==")
        _embed_documents(settings, args.limit)
    if do_index:
        print("\n== Creating Atlas search indexes ==")
        _create_indexes(settings)
    print("\nDone.")


if __name__ == "__main__":
    main()
