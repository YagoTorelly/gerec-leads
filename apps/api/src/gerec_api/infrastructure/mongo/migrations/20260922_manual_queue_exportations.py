"""Initialize the independent manual queue without rewriting automatic state."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Callable

from gerec_api.infrastructure.mongo.collections import MongoCollections


VERSION = "20260922_manual_queue_exportations"
MANUAL_QUEUE_STATE_ID = "manual"


def apply(
    database: Any,
    *,
    session: Any | None = None,
    now: Callable[[], datetime] | None = None,
) -> None:
    """Create the manual cursor once, starting at the first configured seller."""
    timestamp = (now or (lambda: datetime.now(UTC)))()
    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        raise ValueError("migration clock must return a timezone-aware datetime")
    timestamp = timestamp.astimezone(UTC)
    options = {} if session is None else {"session": session}
    states = database[MongoCollections.QUEUE_STATE]
    if states.find_one({"_id": MANUAL_QUEUE_STATE_ID}, **options) is not None:
        return
    sellers = sorted(
        database[MongoCollections.SELLER_QUEUE].find({}, **options),
        key=lambda seller: (seller.get("position", 0), str(seller.get("sellerId", ""))),
    )
    states.insert_one(
        {
            "_id": MANUAL_QUEUE_STATE_ID,
            "nextSellerId": sellers[0]["sellerId"] if sellers else None,
            "version": 0,
            "createdAt": timestamp,
            "updatedAt": timestamp,
        },
        **options,
    )
