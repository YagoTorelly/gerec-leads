"""Retry-safe notification outbox worker for the Railway worker service."""

from __future__ import annotations

import logging
import os
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from time import sleep
from typing import Any, Protocol

from pymongo import ReturnDocument

from gerec_api.config import Settings
from gerec_api.infrastructure.mongo.client import MongoClientFactory
from gerec_api.infrastructure.mongo.collections import MongoCollections


LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class OutboxEvent:
    event_id: Any
    event_type: str
    idempotency_key: str
    payload: dict[str, Any]
    attempts: int = 0
    status: str = "pending"

    @classmethod
    def from_document(cls, document: dict[str, Any]) -> "OutboxEvent":
        return cls(
            event_id=document["_id"],
            event_type=str(document["eventType"]),
            idempotency_key=str(document["idempotencyKey"]),
            payload=dict(document.get("payload", {})),
            attempts=int(document.get("attempts", 0)),
            status=str(document.get("status", "pending")),
        )


class OutboxRepository(Protocol):
    def claim(self, batch_size: int, now: datetime, max_attempts: int) -> Iterable[OutboxEvent]: ...

    def mark_sent(self, event: OutboxEvent, now: datetime) -> None: ...

    def mark_retry(
        self, event: OutboxEvent, error: Exception, now: datetime, max_attempts: int
    ) -> None: ...


class MongoOutboxRepository:
    """Use atomic Mongo claims so concurrent workers cannot deliver an event twice."""

    def __init__(self, database: Any, *, lock_for: timedelta = timedelta(minutes=5)) -> None:
        self._outbox = database[MongoCollections.NOTIFICATION_OUTBOX]
        self._incidents = database[MongoCollections.NOTIFICATION_INCIDENTS]
        self._lock_for = lock_for

    def claim(self, batch_size: int, now: datetime, max_attempts: int) -> list[OutboxEvent]:
        claimed: list[OutboxEvent] = []
        for _ in range(batch_size):
            document = self._outbox.find_one_and_update(
                {
                    "attempts": {"$lt": max_attempts},
                    "$or": [
                        {"status": {"$in": ["pending", "retry"]}},
                        {"status": "scheduled", "scheduledFor": {"$lte": now}},
                        {"status": "processing", "lockedUntil": {"$lte": now}},
                    ],
                },
                {
                    "$set": {"status": "processing", "lockedUntil": now + self._lock_for},
                    "$inc": {"attempts": 1},
                },
                sort=[("createdAt", 1), ("_id", 1)],
                return_document=ReturnDocument.AFTER,
            )
            if document is None:
                break
            claimed.append(OutboxEvent.from_document(document))
        return claimed

    def mark_sent(self, event: OutboxEvent, now: datetime) -> None:
        self._outbox.update_one(
            {"_id": event.event_id, "status": "processing"},
            {
                "$set": {"status": "sent", "sentAt": now},
                "$unset": {"lockedUntil": ""},
            },
        )

    def mark_retry(
        self, event: OutboxEvent, error: Exception, now: datetime, max_attempts: int
    ) -> None:
        message = str(error)[:500]
        terminal = event.attempts >= max_attempts
        self._outbox.update_one(
            {"_id": event.event_id, "status": "processing"},
            {
                "$set": {
                    "status": "dead_letter" if terminal else "retry",
                    "lastError": message,
                    "lastFailedAt": now,
                },
                "$unset": {"lockedUntil": ""},
            },
        )
        if terminal:
            self._incidents.update_one(
                {"outboxEventId": event.event_id},
                {
                    "$setOnInsert": {
                        "outboxEventId": event.event_id,
                        "idempotencyKey": event.idempotency_key,
                        "eventType": event.event_type,
                        "createdAt": now,
                    },
                    "$set": {"lastError": message, "updatedAt": now},
                },
                upsert=True,
            )


class OutboxWorker:
    """Deliver only claimed events and leave domain data untouched on delivery errors."""

    def __init__(
        self,
        repository: OutboxRepository,
        deliver: Callable[[OutboxEvent], None],
        *,
        max_attempts: int = 3,
    ) -> None:
        if max_attempts < 1:
            raise ValueError("max_attempts must be positive")
        self._repository = repository
        self._deliver = deliver
        self._max_attempts = max_attempts

    def process(self, batch_size: int, *, now: datetime | None = None) -> int:
        if batch_size < 1:
            raise ValueError("batch_size must be positive")
        timestamp = now or datetime.now(UTC)
        delivered = 0
        for event in self._repository.claim(batch_size, timestamp, self._max_attempts):
            try:
                self._deliver(event)
            except Exception as error:  # external providers are retried; domain commits remain intact
                LOGGER.warning("outbox delivery failed: event=%s type=%s", event.event_id, event.event_type)
                self._repository.mark_retry(event, error, timestamp, self._max_attempts)
                continue
            self._repository.mark_sent(event, timestamp)
            delivered += 1
        return delivered


def _unconfigured_delivery(event: OutboxEvent) -> None:
    raise RuntimeError("notification delivery adapter is not configured")


def process_outbox(batch_size: int) -> int:
    """Railway entry point. A deployment injects its delivery adapter at composition time."""
    settings = Settings.from_env()
    database = MongoClientFactory.create(settings)
    return OutboxWorker(MongoOutboxRepository(database), _unconfigured_delivery).process(batch_size)


def run_forever(*, batch_size: int = 100, poll_seconds: float = 5) -> None:
    """Persistent Railway worker loop; logs only event metadata, never lead payloads."""
    while True:
        processed = process_outbox(batch_size)
        if processed == 0:
            sleep(poll_seconds)


if __name__ == "__main__":
    run_forever(batch_size=int(os.environ.get("OUTBOX_BATCH_SIZE", "100")))
