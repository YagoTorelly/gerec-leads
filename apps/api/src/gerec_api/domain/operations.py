"""Domain interface for feedback, contact attempts and commercial outcomes."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import Any, Literal, Mapping, Protocol
from zoneinfo import ZoneInfo

from gerec_api.domain.business_time import BusinessClock


SAO_PAULO = ZoneInfo("America/Sao_Paulo")
OUTCOMES = frozenset(
    {"qualified_follow_up", "qualified_closed_no_conversion", "disqualified", "won"}
)
DISQUALIFICATION_REASONS = frozenset({"no_answer_after_5_attempts", "no_cnpj", "outside_sp"})
COMMERCIAL_STATUSES = frozenset({"undefined", "negotiation", "won"})
CommercialStatus = Literal["undefined", "negotiation", "won"]


@dataclass(frozen=True)
class FeedbackCommand:
    lead_id: Any
    comment: str
    contact_started: bool
    idempotency_key: str
    administrative_note: bool = False


@dataclass(frozen=True)
class AttemptCommand:
    lead_id: Any
    comment: str
    idempotency_key: str
    business_date: date | None = None
    channel: str = "whatsapp"


@dataclass(frozen=True)
class OutcomeCommand:
    lead_id: Any
    outcome: str
    comment: str
    idempotency_key: str
    disqualification_reason: str | None = None
    response_confirmed: bool = False


@dataclass(frozen=True)
class TreatmentCommand:
    lead_id: Any
    comment: str
    commercial_status: CommercialStatus
    is_disqualified: bool
    idempotency_key: str


@dataclass(frozen=True)
class FeedbackResult:
    lead_id: str
    feedback_id: str
    status: str

    def to_document(self) -> dict[str, Any]:
        return {
            "leadId": self.lead_id,
            "feedbackId": self.feedback_id,
            "status": self.status,
        }

    @classmethod
    def from_document(cls, value: Mapping[str, Any]) -> "FeedbackResult":
        return cls(
            lead_id=str(value["leadId"]),
            feedback_id=str(value["feedbackId"]),
            status=str(value["status"]),
        )


@dataclass(frozen=True)
class AttemptResult:
    lead_id: str
    attempt_id: str
    sequence: int
    business_date: date
    may_disqualify_no_answer: bool
    status: str

    def to_document(self) -> dict[str, Any]:
        return {
            "leadId": self.lead_id,
            "attemptId": self.attempt_id,
            "sequence": self.sequence,
            "businessDate": self.business_date.isoformat(),
            "mayDisqualifyNoAnswer": self.may_disqualify_no_answer,
            "status": self.status,
        }

    @classmethod
    def from_document(cls, value: Mapping[str, Any]) -> "AttemptResult":
        raw_date = value["businessDate"]
        business_date = raw_date if isinstance(raw_date, date) else date.fromisoformat(str(raw_date))
        return cls(
            lead_id=str(value["leadId"]),
            attempt_id=str(value["attemptId"]),
            sequence=int(value["sequence"]),
            business_date=business_date,
            may_disqualify_no_answer=bool(value["mayDisqualifyNoAnswer"]),
            status=str(value["status"]),
        )


@dataclass(frozen=True)
class OutcomeResult:
    lead_id: str
    outcome_event_id: str
    outcome: str
    sale_id: str | None
    status: str

    def to_document(self) -> dict[str, Any]:
        return {
            "leadId": self.lead_id,
            "outcomeEventId": self.outcome_event_id,
            "outcome": self.outcome,
            "saleId": self.sale_id,
            "status": self.status,
        }

    @classmethod
    def from_document(cls, value: Mapping[str, Any]) -> "OutcomeResult":
        return cls(
            lead_id=str(value["leadId"]),
            outcome_event_id=str(value["outcomeEventId"]),
            outcome=str(value["outcome"]),
            sale_id=str(value["saleId"]) if value.get("saleId") is not None else None,
            status=str(value["status"]),
        )


@dataclass(frozen=True)
class TreatmentResult:
    lead_id: str
    treatment_id: str
    status: str
    commercial_status: CommercialStatus
    is_disqualified: bool
    comment_count: int
    last_updated_at: datetime

    def to_document(self) -> dict[str, Any]:
        return {
            "leadId": self.lead_id,
            "treatmentId": self.treatment_id,
            "status": self.status,
            "commercialStatus": self.commercial_status,
            "isDisqualified": self.is_disqualified,
            "commentCount": self.comment_count,
            "lastUpdatedAt": self.last_updated_at,
        }

    @classmethod
    def from_document(cls, value: Mapping[str, Any]) -> "TreatmentResult":
        return cls(
            lead_id=str(value["leadId"]),
            treatment_id=str(value["treatmentId"]),
            status=str(value["status"]),
            commercial_status=str(value["commercialStatus"]),  # type: ignore[arg-type]
            is_disqualified=bool(value["isDisqualified"]),
            comment_count=int(value["commentCount"]),
            last_updated_at=value["lastUpdatedAt"],
        )


class Clock(Protocol):
    def now(self, session: Any | None = None) -> datetime: ...


class SystemClock:
    def now(self, session: Any | None = None) -> datetime:
        return datetime.now(UTC)


class OperationsPersistence(Protocol):
    def register_treatment(
        self,
        command: TreatmentCommand,
        *,
        actor_id: Any,
        actor_role: str,
        now: datetime,
    ) -> TreatmentResult: ...

    def register_feedback(
        self,
        command: FeedbackCommand,
        *,
        actor_id: Any,
        actor_role: str,
        now: datetime,
    ) -> FeedbackResult: ...

    def register_attempt(
        self,
        command: AttemptCommand,
        *,
        actor_id: Any,
        actor_role: str,
        now: datetime,
        business_date: date,
    ) -> AttemptResult: ...

    def register_outcome(
        self,
        command: OutcomeCommand,
        *,
        actor_id: Any,
        actor_role: str,
        now: datetime,
    ) -> OutcomeResult: ...


class OperationsService:
    def __init__(
        self,
        persistence: OperationsPersistence,
        *,
        business_clock: BusinessClock,
        clock: Clock,
        actor_id: Any = "system",
        actor_role: str = "system",
    ) -> None:
        self._persistence = persistence
        self._business_clock = business_clock
        self._clock = clock
        self._actor_id = actor_id
        self._actor_role = actor_role

    def with_actor(self, actor_id: Any, actor_role: str) -> "OperationsService":
        if actor_id is None or (isinstance(actor_id, str) and not actor_id.strip()):
            raise ValueError("actor id is required")
        if actor_role not in {"admin", "seller", "system"}:
            raise ValueError("actor role is invalid")
        return OperationsService(
            self._persistence,
            business_clock=self._business_clock,
            clock=self._clock,
            actor_id=actor_id,
            actor_role=actor_role,
        )

    def register_feedback(self, command: FeedbackCommand) -> FeedbackResult:
        command = FeedbackCommand(
            command.lead_id,
            _comment(command.comment),
            command.contact_started,
            _required(command.idempotency_key, "idempotency key"),
            command.administrative_note,
        )
        now = self._aware_now()
        if command.administrative_note:
            if self._actor_role != "admin":
                raise ValueError("administrative notes require an admin actor")
        else:
            if self._actor_role != "seller":
                raise ValueError("seller feedback requires a seller actor")
            if not command.contact_started:
                raise ValueError("feedback requires an explicit contact action")
        return self._persistence.register_feedback(
            command,
            actor_id=self._actor_id,
            actor_role=self._actor_role,
            now=now,
        )

    def register_treatment(self, command: TreatmentCommand) -> TreatmentResult:
        if self._actor_role != "seller":
            raise ValueError("treatments require a seller actor")
        if command.commercial_status not in COMMERCIAL_STATUSES:
            raise ValueError("commercial status is invalid")
        if not isinstance(command.is_disqualified, bool):
            raise ValueError("is disqualified must be a boolean")
        command = TreatmentCommand(
            command.lead_id,
            _comment(command.comment),
            command.commercial_status,
            command.is_disqualified,
            _required(command.idempotency_key, "idempotency key"),
        )
        now = self._aware_now()
        return self._persistence.register_treatment(
            command,
            actor_id=self._actor_id,
            actor_role=self._actor_role,
            now=now,
        )

    def register_attempt(self, command: AttemptCommand) -> AttemptResult:
        if self._actor_role != "seller":
            raise ValueError("contact attempts require a seller actor")
        now = self._aware_now()
        business_date = command.business_date or now.astimezone(SAO_PAULO).date()
        if business_date > now.astimezone(SAO_PAULO).date():
            raise ValueError("contact attempt cannot use a future date")
        if not self._business_clock.is_business_day(business_date):
            raise ValueError("contact attempt date must be a business day")
        if command.channel != "whatsapp":
            raise ValueError("only whatsapp attempts count in the MVP")
        command = AttemptCommand(
            command.lead_id,
            _comment(command.comment),
            _required(command.idempotency_key, "idempotency key"),
            business_date,
            command.channel,
        )
        return self._persistence.register_attempt(
            command,
            actor_id=self._actor_id,
            actor_role=self._actor_role,
            now=now,
            business_date=business_date,
        )

    def register_outcome(self, command: OutcomeCommand) -> OutcomeResult:
        if self._actor_role != "seller":
            raise ValueError("commercial outcomes require a seller actor")
        if command.outcome not in OUTCOMES:
            raise ValueError("outcome is invalid")
        reason = command.disqualification_reason
        if command.outcome == "disqualified":
            if reason not in DISQUALIFICATION_REASONS:
                raise ValueError("disqualification reason is invalid")
        elif reason is not None:
            raise ValueError("disqualification reason is only valid for disqualified outcomes")
        command = OutcomeCommand(
            command.lead_id,
            command.outcome,
            _comment(command.comment),
            _required(command.idempotency_key, "idempotency key"),
            reason,
            command.response_confirmed,
        )
        if command.outcome in {"qualified_follow_up", "qualified_closed_no_conversion"} and not command.response_confirmed:
            raise ValueError("qualified outcome requires explicit response confirmation")
        return self._persistence.register_outcome(
            command,
            actor_id=self._actor_id,
            actor_role=self._actor_role,
            now=self._aware_now(),
        )

    def _aware_now(self) -> datetime:
        value = self._clock.now()
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("clock must return a timezone-aware datetime")
        return value


def _required(value: str, label: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{label} is required")
    return normalized


def _comment(value: str) -> str:
    normalized = value.strip()
    if len(normalized) < 6:
        raise ValueError("comment must contain at least 6 useful characters")
    return normalized
