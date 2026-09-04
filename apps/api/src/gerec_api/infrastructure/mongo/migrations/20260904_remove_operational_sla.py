"""Disable legacy SLA projections without deleting historical audit records."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from gerec_api.infrastructure.mongo.collections import MongoCollections


VERSION = "20260904_remove_operational_sla"


def apply(database: Any, *, session: Any | None = None) -> None:
    """Clear active deadline state and cancel every nonterminal legacy reminder."""
    options = {} if session is None else {"session": session}
    now = datetime.now(UTC)
    database[MongoCollections.LEADS].update_many(
        {},
        {
            "$unset": {
                "feedbackCycleId": "",
                "feedbackDueAt": "",
                "feedbackReminderAt": "",
            }
        },
        **options,
    )
    database[MongoCollections.FEEDBACK_CYCLES].update_many(
        {"closedAt": None},
        {"$set": {"closedAt": now, "closedByMigration": VERSION}},
        **options,
    )
    database[MongoCollections.NOTIFICATION_OUTBOX].update_many(
        {
            "eventType": "lead.feedback_due_soon",
            "status": {"$nin": ["sent", "dead_letter", "cancelled"]},
        },
        {"$set": {"status": "cancelled", "cancelledAt": now, "cancelledByMigration": VERSION}},
        **options,
    )
