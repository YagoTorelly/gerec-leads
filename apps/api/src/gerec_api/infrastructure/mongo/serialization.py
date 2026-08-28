"""JSON-safe projection for values returned by PyMongo."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from bson import ObjectId


def serialize_bson(value: Any) -> Any:
    """Recursively stringify BSON identifiers while preserving JSON-native values."""
    if isinstance(value, ObjectId):
        return str(value)
    if isinstance(value, Mapping):
        return {str(key): serialize_bson(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [serialize_bson(item) for item in value]
    return value
