"""MongoDB persistence for seller notification windows and cursors."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from bson import ObjectId
from pymongo import ASCENDING, ReturnDocument

from gerec_api.domain.lead_notifications import NewLeadNotification
from gerec_api.infrastructure.mongo.collections import MongoCollections


class LeadNotificationStateError(RuntimeError):
    """Raised when a persisted seller lacks a valid notification cursor."""


class MongoLeadNotificationRepository:
    """Read derived notification state without changing assignments, queue, or outbox."""

    def __init__(self, database: Any) -> None:
        self._users = database[MongoCollections.USERS]
        self._leads = database[MongoCollections.LEADS]

    def for_seller(self, seller_id: str, watermark: datetime) -> tuple[NewLeadNotification, ...]:
        seller = self._seller(seller_id)
        seen_at = seller.get("newLeadsSeenAt")
        if not isinstance(seen_at, datetime):
            raise LeadNotificationStateError("seller notification cursor is not initialized")
        cursor = self._leads.find(
            {
                "assigneeId": {"$in": _identity_values(seller_id)},
                "assignedAt": {"$gt": seen_at, "$lte": watermark},
            }
        ).sort([("assignedAt", ASCENDING), ("_id", ASCENDING)])
        return tuple(
            NewLeadNotification(
                lead_id=str(lead["_id"]),
                contact_name=_contact_name(lead),
                assigned_at=lead["assignedAt"].astimezone(UTC),
            )
            for lead in cursor
        )

    def acknowledge(self, seller_id: str, watermark: datetime) -> datetime:
        seller = self._users.find_one_and_update(
            {"_id": {"$in": _identity_values(seller_id)}, "role": "seller"},
            {"$max": {"newLeadsSeenAt": watermark}},
            return_document=ReturnDocument.AFTER,
        )
        if seller is None or not isinstance(seller.get("newLeadsSeenAt"), datetime):
            raise LeadNotificationStateError("seller notification cursor cannot be acknowledged")
        return seller["newLeadsSeenAt"].astimezone(UTC)

    def _seller(self, seller_id: str) -> dict[str, Any]:
        seller = self._users.find_one({"_id": {"$in": _identity_values(seller_id)}, "role": "seller"})
        if seller is None:
            raise LeadNotificationStateError("seller notification cursor is unavailable")
        return seller


def _identity_values(value: str) -> list[Any]:
    values: list[Any] = [value]
    if ObjectId.is_valid(value):
        values.append(ObjectId(value))
    return values


def _contact_name(lead: dict[str, Any]) -> str:
    value = lead.get("contactName")
    return str(value).strip() if value is not None and str(value).strip() else "Não informado"
