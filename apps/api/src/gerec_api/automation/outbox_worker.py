"""Retry-safe notification outbox worker for the Railway worker service."""

from __future__ import annotations

import logging
import os
import json
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from time import sleep
from typing import Any, Protocol
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from uuid import uuid4

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
    claim_token: str | None = None

    @classmethod
    def from_document(cls, document: dict[str, Any]) -> "OutboxEvent":
        return cls(
            event_id=document["_id"],
            event_type=str(document["eventType"]),
            idempotency_key=str(document["idempotencyKey"]),
            payload=dict(document.get("payload", {})),
            attempts=int(document.get("attempts", 0)),
            status=str(document.get("status", "pending")),
            claim_token=str(document["claimToken"]) if document.get("claimToken") else None,
        )


class OutboxRepository(Protocol):
    def claim(self, batch_size: int, now: datetime, max_attempts: int) -> Iterable[OutboxEvent]: ...

    def mark_sent(self, event: OutboxEvent, now: datetime) -> bool: ...

    def mark_retry(
        self, event: OutboxEvent, error: Exception, now: datetime, max_attempts: int
    ) -> bool: ...


class MongoOutboxRepository:
    """Use atomic Mongo claims so concurrent workers cannot deliver an event twice."""

    def __init__(self, database: Any, *, lock_for: timedelta = timedelta(minutes=5)) -> None:
        self._outbox = database[MongoCollections.NOTIFICATION_OUTBOX]
        self._incidents = database[MongoCollections.NOTIFICATION_INCIDENTS]
        self._lock_for = lock_for

    def claim(self, batch_size: int, now: datetime, max_attempts: int) -> list[OutboxEvent]:
        claimed: list[OutboxEvent] = []
        for _ in range(batch_size):
            claim_token = uuid4().hex
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
                    "$set": {
                        "status": "processing",
                        "lockedUntil": now + self._lock_for,
                        "claimToken": claim_token,
                    },
                    "$inc": {"attempts": 1},
                },
                sort=[("createdAt", 1), ("_id", 1)],
                return_document=ReturnDocument.AFTER,
            )
            if document is None:
                break
            claimed.append(OutboxEvent.from_document(document))
        return claimed

    def mark_sent(self, event: OutboxEvent, now: datetime) -> bool:
        if not event.claim_token:
            return False
        result = self._outbox.update_one(
            {"_id": event.event_id, "status": "processing", "claimToken": event.claim_token},
            {
                "$set": {"status": "sent", "sentAt": now},
                "$unset": {"lockedUntil": "", "claimToken": ""},
            },
        )
        return result.matched_count == 1

    def mark_retry(
        self, event: OutboxEvent, error: Exception, now: datetime, max_attempts: int
    ) -> bool:
        if not event.claim_token:
            return False
        message = str(error)[:500]
        terminal = event.attempts >= max_attempts
        result = self._outbox.update_one(
            {"_id": event.event_id, "status": "processing", "claimToken": event.claim_token},
            {
                "$set": {
                    "status": "dead_letter" if terminal else "retry",
                    "lastError": message,
                    "lastFailedAt": now,
                },
                "$unset": {"lockedUntil": "", "claimToken": ""},
            },
        )
        if result.matched_count != 1:
            return False
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
        return True


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
            if self._repository.mark_sent(event, timestamp):
                delivered += 1
            else:
                LOGGER.warning("outbox acknowledgement fenced: event=%s", event.event_id)
        return delivered


class WebhookDeliveryAdapter:
    """Provider-neutral Railway delivery hook; provider receives idempotency key."""

    def __init__(self, url: str, token: str | None, *, open_request: Callable[..., Any] = urlopen) -> None:
        if not url:
            raise ValueError("OUTBOX_DELIVERY_WEBHOOK_URL must be configured in Railway")
        self._url = url
        self._token = token
        self._open_request = open_request

    @classmethod
    def from_env(cls, *, open_request: Callable[..., Any] = urlopen) -> "WebhookDeliveryAdapter":
        return cls(os.environ.get("OUTBOX_DELIVERY_WEBHOOK_URL", ""), os.environ.get("OUTBOX_DELIVERY_TOKEN"), open_request=open_request)

    def deliver(self, event: OutboxEvent) -> None:
        headers = {"Content-Type": "application/json", "Idempotency-Key": event.idempotency_key}
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        body = json.dumps({"eventType": event.event_type, "idempotencyKey": event.idempotency_key, "payload": event.payload}).encode("utf-8")
        request = Request(self._url, data=body, headers=headers, method="POST")
        try:
            with self._open_request(request, timeout=10):
                return
        except (HTTPError, URLError) as error:
            raise RuntimeError(f"notification provider failed: {error}") from error


def process_outbox(batch_size: int) -> int:
    """Railway entry point. A deployment injects its delivery adapter at composition time."""
    settings = Settings.from_env()
    database = MongoClientFactory.create(settings)
    delivery = WebhookDeliveryAdapter.from_env()
    return OutboxWorker(MongoOutboxRepository(database), delivery.deliver).process(batch_size)


def run_forever(*, batch_size: int = 100, poll_seconds: float = 5) -> None:
    """Persistent Railway worker loop; logs only event metadata, never lead payloads."""
    while True:
        processed = process_outbox(batch_size)
        if processed == 0:
            sleep(poll_seconds)


if __name__ == "__main__":
    run_forever(batch_size=int(os.environ.get("OUTBOX_BATCH_SIZE", "100")))
