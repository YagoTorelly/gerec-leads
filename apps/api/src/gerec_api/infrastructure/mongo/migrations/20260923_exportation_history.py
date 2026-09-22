"""Version the administrative exportation-history collection and indexes."""

from __future__ import annotations

from typing import Any

from gerec_api.infrastructure.mongo.collections import MongoCollections
from gerec_api.infrastructure.mongo.indexes import INDEXES


VERSION = "20260923_exportation_history"


def apply(database: Any, *, session: Any | None = None) -> None:
    """Create the history indexes idempotently without rewriting prior migrations."""
    target = database[MongoCollections.EXPORTATIONS]
    for definition in INDEXES:
        if definition.collection_name == MongoCollections.EXPORTATIONS:
            definition.apply(target)
