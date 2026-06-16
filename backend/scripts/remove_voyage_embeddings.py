"""Remove the `plot_embedding_voyage` field from every embedded_movies document.

Undoes what scripts/seed_search_indexes.py adds. Useful when re-seeding with a
different Voyage model/dimensionality, or to reset the collection.

Run from the backend/ directory after filling in `.env`:

    python -m scripts.remove_voyage_embeddings            # ask for confirmation
    python -m scripts.remove_voyage_embeddings --yes      # skip the prompt

Note: this only unsets the field on documents. It does NOT drop the vector
search index — delete that separately (Atlas UI or driver) if you no longer
want it, otherwise it will simply index an absent field.
"""
from __future__ import annotations

import argparse
import sys

from pymongo import MongoClient

# Import the app settings so the script and server share one config source.
sys.path.insert(0, ".")
from app.config import get_settings  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Remove plot_embedding_voyage from embedded_movies."
    )
    parser.add_argument(
        "--yes", action="store_true", help="Skip the confirmation prompt."
    )
    args = parser.parse_args()

    settings = get_settings()
    if not settings.has_mongodb:
        sys.exit("ERROR: MONGODB_URI is not set. Fill in .env first.")

    field = settings.vector_field  # "plot_embedding_voyage" by default

    client = MongoClient(settings.mongodb_uri)
    coll = client[settings.mongodb_db][settings.mongodb_collection]

    target = {field: {"$exists": True}}
    count = coll.count_documents(target)
    print(
        f"Collection : {settings.mongodb_db}.{settings.mongodb_collection}\n"
        f"Field      : {field}\n"
        f"Documents  : {count} have this field"
    )

    if count == 0:
        print("Nothing to do.")
        client.close()
        return

    if not args.yes:
        reply = input(f"Remove '{field}' from {count} documents? [y/N] ").strip().lower()
        if reply not in ("y", "yes"):
            print("Aborted.")
            client.close()
            return

    result = coll.update_many(target, {"$unset": {field: ""}})
    print(f"Done. Modified {result.modified_count} documents.")
    client.close()


if __name__ == "__main__":
    main()
