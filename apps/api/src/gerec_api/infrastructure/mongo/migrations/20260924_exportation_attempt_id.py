"""Backfill a stable identity for every existing exportation attempt."""

from __future__ import annotations

from typing import Any

from gerec_api.infrastructure.mongo.collections import MongoCollections


VERSION = "20260924_exportation_attempt_id"


def apply(database: Any, *, session: Any | None = None) -> None:
    """Assign a deterministic unique attemptId without changing final status."""
    options = {} if session is None else {"session": session}
    collection = database[MongoCollections.EXPORTATIONS]
    for document in collection.find({"attemptId": {"$exists": False}}, **options):
        collection.update_one(
            {"_id": document["_id"], "attemptId": {"$exists": False}},
            {"$set": {"attemptId": f"legacy:{document['_id']}"}},
            **options,
        )
