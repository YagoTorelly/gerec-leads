"""Domain command for administrator-created leads and the manual queue."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Mapping, Protocol


@dataclass(frozen=True)
class ManualLeadCommand:
    name: str
    email: str
    phone: str
    idempotency_key: str
    campaign: str | None = None
    source: str | None = None


@dataclass(frozen=True)
class ManualLeadResult:
    lead_id: str
    manual_queue_lead_id: str
    assignee_id: str | None
    assigned_at: datetime | None
    commercial_status: str = "undefined"
    source: str = "manual"
    status: str = "assigned"

    def to_document(self) -> dict[str, Any]:
        return {
            "leadId": self.lead_id,
            "manualQueueLeadId": self.manual_queue_lead_id,
            "assigneeId": self.assignee_id,
            "assignedAt": self.assigned_at,
            "commercialStatus": self.commercial_status,
            "source": self.source,
            "status": self.status,
        }

    @classmethod
    def from_document(cls, value: Mapping[str, Any]) -> "ManualLeadResult":
        return cls(
            lead_id=str(value["leadId"]),
            manual_queue_lead_id=str(value["manualQueueLeadId"]),
            assignee_id=(
                str(value["assigneeId"]) if value.get("assigneeId") is not None else None
            ),
            assigned_at=value.get("assignedAt"),
            commercial_status=str(value.get("commercialStatus", "undefined")),
            source=str(value.get("source", "manual")),
            status=str(value.get("status", "assigned")),
        )


class ManualLeadPersistence(Protocol):
    def create_manual_lead(
        self,
        actor: Any,
        command: ManualLeadCommand,
        now: datetime,
    ) -> ManualLeadResult: ...


class ManualLeadService:
    """Validate and normalize the command before entering persistence."""

    def __init__(self, persistence: ManualLeadPersistence) -> None:
        self._persistence = persistence

    def create_manual_lead(
        self,
        actor: Any,
        command: ManualLeadCommand,
        now: datetime,
    ) -> ManualLeadResult:
        actor_id = _actor_id(actor)
        timestamp = _aware_utc(now)
        normalized = ManualLeadCommand(
            name=_required(command.name, "name"),
            email=_email(command.email),
            phone=_required(command.phone, "phone"),
            campaign=_optional(command.campaign),
            source=_optional(command.source),
            idempotency_key=_required(command.idempotency_key, "idempotency key"),
        )
        return self._persistence.create_manual_lead(actor_id, normalized, timestamp)


def _actor_id(actor: Any) -> Any:
    if isinstance(actor, Mapping):
        actor = actor.get("id") or actor.get("user_id")
    else:
        actor = getattr(actor, "id", getattr(actor, "user_id", actor))
    if actor is None or (isinstance(actor, str) and not actor.strip()):
        raise ValueError("actor is required")
    return actor.strip() if isinstance(actor, str) else actor


def _aware_utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("now must be timezone-aware")
    return value.astimezone(UTC)


def _required(value: str, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} is required")
    return value.strip()


def _optional(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


def _email(value: str) -> str:
    normalized = _required(value, "email").casefold()
    local, separator, domain = normalized.partition("@")
    if not separator or not local or not domain:
        raise ValueError("email is invalid")
    return normalized
