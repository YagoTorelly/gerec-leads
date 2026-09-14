"""Seller-scoped, persistent notification windows for newly assigned leads."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Callable, Protocol

from gerec_api.auth.sessions import CurrentUser


@dataclass(frozen=True)
class NewLeadNotification:
    """Minimal lead data that can be shown in the seller's notification window."""

    lead_id: str
    contact_name: str
    assigned_at: datetime

    def to_document(self) -> dict[str, str]:
        return {
            "leadId": self.lead_id,
            "contactName": self.contact_name,
            "assignedAt": self.assigned_at.isoformat(),
        }


@dataclass(frozen=True)
class NewLeadNotificationSnapshot:
    """A stable notification window and its server-issued closing watermark."""

    items: tuple[NewLeadNotification, ...]
    watermark: datetime

    def to_document(self) -> dict[str, Any]:
        return {
            "items": [item.to_document() for item in self.items],
            "watermark": self.watermark.isoformat(),
        }


class LeadNotificationPersistence(Protocol):
    def for_seller(self, seller_id: str, watermark: datetime) -> tuple[NewLeadNotification, ...]: ...

    def acknowledge(self, seller_id: str, watermark: datetime) -> datetime: ...


class LeadNotificationService:
    """Owns authorization and time validation; persistence owns the atomic cursor update."""

    def __init__(
        self,
        persistence: LeadNotificationPersistence,
        *,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        self._persistence = persistence
        self._now = now or (lambda: datetime.now(UTC))

    def for_seller(self, user: CurrentUser) -> NewLeadNotificationSnapshot:
        self._require_seller(user)
        watermark = self._timestamp(self._now(), label="clock")
        return NewLeadNotificationSnapshot(
            items=self._persistence.for_seller(user.id, watermark),
            watermark=watermark,
        )

    def acknowledge(self, user: CurrentUser, watermark: datetime) -> datetime:
        self._require_seller(user)
        received = self._timestamp(watermark, label="notification watermark")
        if received > self._timestamp(self._now(), label="clock"):
            raise ValueError("notification watermark cannot be in the future")
        return self._persistence.acknowledge(user.id, received)

    @staticmethod
    def _require_seller(user: CurrentUser) -> None:
        if not isinstance(user, CurrentUser) or user.role != "seller" or not user.id:
            raise PermissionError("seller role is required")

    @staticmethod
    def _timestamp(value: datetime, *, label: str) -> datetime:
        if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"{label} must be timezone-aware")
        return value.astimezone(UTC)
