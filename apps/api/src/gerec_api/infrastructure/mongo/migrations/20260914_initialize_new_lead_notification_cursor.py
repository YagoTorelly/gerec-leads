"""Initialize seller notification cursors without rewriting existing acknowledgements."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Callable

from gerec_api.infrastructure.mongo.collections import MongoCollections


VERSION = "20260914_initialize_new_lead_notification_cursor"


def apply(
    database: Any,
    *,
    session: Any | None = None,
    now: Callable[[], datetime] | None = None,
) -> None:
    """Set the first-window baseline only for sellers whose cursor is absent."""
    timestamp = (now or (lambda: datetime.now(UTC)))()
    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        raise ValueError("migration clock must return a timezone-aware datetime")
    options = {} if session is None else {"session": session}
    database[MongoCollections.USERS].update_many(
        {"role": "seller", "newLeadsSeenAt": {"$exists": False}},
        {"$set": {"newLeadsSeenAt": timestamp.astimezone(UTC)}},
        **options,
    )
