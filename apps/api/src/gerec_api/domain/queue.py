"""Domain rules and narrow command interface for the global lead queue."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Mapping, Protocol, Sequence

from bson import ObjectId


@dataclass(frozen=True)
class SellerState:
    seller_id: Any
    active: bool
    paused: bool
    has_overdue_feedback: bool
    skip_balance: int
    position: int = 0


@dataclass(frozen=True)
class SellerAvailability:
    status: Literal["active", "paused"]
    reason: str | None


@dataclass(frozen=True)
class QueueEntry:
    seller_id: Any
    position: int
    availability: SellerAvailability
    skip_balance: int


@dataclass(frozen=True)
class QueueSnapshot:
    cursor_seller_id: ObjectId | None
    entries: list[QueueEntry]


@dataclass(frozen=True)
class QueueDecision:
    seller_id: Any | None
    next_seller_id: Any
    consumed_credit_seller_ids: tuple[Any, ...] = ()
    unavailable_seller_ids: tuple[Any, ...] = ()


class QueueRules:
    @staticmethod
    def availability(seller: SellerState) -> SellerAvailability:
        if seller.paused:
            return SellerAvailability("paused", "Pausa manual ativa.")
        if not seller.active:
            return SellerAvailability("paused", "Vendedor inativo.")
        # Feedback/SLA fields remain historical data, but do not affect the
        # current operational availability. Only manual pause (or account
        # deactivation) can remove a seller from the rotation.
        return SellerAvailability("active", None)

    @classmethod
    def snapshot(cls, sellers: Sequence[SellerState], next_seller_id: Any) -> QueueSnapshot:
        if not sellers:
            return QueueSnapshot(cursor_seller_id=None, entries=[])
        decision = cls.select_normal(sellers, next_seller_id)
        start_seller_id = decision.seller_id or next_seller_id
        ordered = cls._circular_from_cursor(sellers, start_seller_id)
        return QueueSnapshot(
            cursor_seller_id=next_seller_id,
            entries=[
                QueueEntry(
                    seller_id=seller.seller_id,
                    position=seller.position,
                    availability=cls.availability(seller),
                    skip_balance=seller.skip_balance,
                )
                for seller in ordered
            ],
        )

    @staticmethod
    def select_normal(sellers: Sequence[SellerState], next_seller_id: Any) -> QueueDecision:
        if not sellers:
            raise ValueError("seller queue cannot be empty")
        cursor = QueueRules._cursor_index(sellers, next_seller_id)

        operational = [
            seller
            for seller in sellers
            if QueueRules.availability(seller).status == "active"
        ]
        if not operational:
            return QueueDecision(seller_id=None, next_seller_id=next_seller_id)

        balances = {seller.seller_id: seller.skip_balance for seller in sellers}
        if any(balance < 0 for balance in balances.values()):
            raise ValueError("skip balance cannot be negative")
        consumed: list[Any] = []
        unavailable: list[Any] = []

        while True:
            seller = sellers[cursor]
            cursor = (cursor + 1) % len(sellers)
            if QueueRules.availability(seller).status != "active":
                unavailable.append(seller.seller_id)
                continue
            if balances[seller.seller_id] > 0:
                balances[seller.seller_id] -= 1
                consumed.append(seller.seller_id)
                continue
            return QueueDecision(
                seller_id=seller.seller_id,
                next_seller_id=QueueRules._next_eligible_seller_id(sellers, cursor),
                consumed_credit_seller_ids=tuple(consumed),
                unavailable_seller_ids=tuple(unavailable),
            )

    @staticmethod
    def _cursor_index(sellers: Sequence[SellerState], seller_id: Any) -> int:
        try:
            return next(
                index for index, seller in enumerate(sellers) if seller.seller_id == seller_id
            )
        except StopIteration as error:
            raise ValueError("queue cursor does not reference a seller") from error

    @classmethod
    def _circular_from_cursor(
        cls, sellers: Sequence[SellerState], next_seller_id: Any
    ) -> list[SellerState]:
        cursor = cls._cursor_index(sellers, next_seller_id)
        return [*sellers[cursor:], *sellers[:cursor]]

    @classmethod
    def _next_eligible_seller_id(cls, sellers: Sequence[SellerState], start_index: int) -> Any:
        for offset in range(len(sellers)):
            seller = sellers[(start_index + offset) % len(sellers)]
            if cls.availability(seller).status == "active":
                return seller.seller_id
        raise ValueError("queue does not have an eligible seller")


@dataclass(frozen=True)
class AssignmentResult:
    lead_id: str
    assignment_id: str | None
    seller_id: str | None
    assignment_type: str | None
    status: str
    owner_id: str | None

    def to_document(self) -> dict[str, Any]:
        return {
            "leadId": self.lead_id,
            "assignmentId": self.assignment_id,
            "sellerId": self.seller_id,
            "assignmentType": self.assignment_type,
            "status": self.status,
            "ownerId": self.owner_id,
        }

    @classmethod
    def from_document(cls, value: Mapping[str, Any]) -> "AssignmentResult":
        return cls(
            lead_id=str(value["leadId"]),
            assignment_id=(
                str(value["assignmentId"]) if value.get("assignmentId") is not None else None
            ),
            seller_id=str(value["sellerId"]) if value.get("sellerId") is not None else None,
            assignment_type=(
                str(value["assignmentType"])
                if value.get("assignmentType") is not None
                else None
            ),
            status=str(value["status"]),
            owner_id=str(value["ownerId"]) if value.get("ownerId") is not None else None,
        )


@dataclass(frozen=True)
class TransferResult:
    company_id: str
    previous_owner_id: str | None
    owner_id: str
    status: str = "transferred"

    def to_document(self) -> dict[str, Any]:
        return {
            "companyId": self.company_id,
            "previousOwnerId": self.previous_owner_id,
            "ownerId": self.owner_id,
            "status": self.status,
        }

    @classmethod
    def from_document(cls, value: Mapping[str, Any]) -> "TransferResult":
        return cls(
            company_id=str(value["companyId"]),
            previous_owner_id=(
                str(value["previousOwnerId"])
                if value.get("previousOwnerId") is not None
                else None
            ),
            owner_id=str(value["ownerId"]),
            status=str(value.get("status", "transferred")),
        )


class QueuePersistence(Protocol):
    def distribute_ready(
        self, lead_id: Any, command_id: str, *, actor_id: Any
    ) -> AssignmentResult: ...

    def distribute_normal(
        self, lead_id: Any, command_id: str, *, actor_id: Any
    ) -> AssignmentResult: ...

    def assign_recurring(
        self, lead_id: Any, command_id: str, *, actor_id: Any
    ) -> AssignmentResult: ...

    def assign_temporarily(
        self,
        lead_id: Any,
        seller_id: Any,
        reason: str,
        command_id: str,
        *,
        actor_id: Any,
    ) -> AssignmentResult: ...

    def transfer_owner(
        self,
        company_id: Any,
        seller_id: Any,
        reason: str,
        command_id: str,
        *,
        actor_id: Any,
    ) -> TransferResult: ...

    def transfer_lead(
        self,
        lead_id: Any,
        seller_id: Any,
        reason: str,
        command_id: str,
        *,
        actor_id: Any,
    ) -> AssignmentResult: ...


class QueueService:
    """Expose queue mutations without leaking MongoDB details to routes or workers."""

    def __init__(self, persistence: QueuePersistence, *, actor_id: Any = "system") -> None:
        self._persistence = persistence
        self._actor_id = actor_id

    def with_actor(self, actor_id: Any) -> "QueueService":
        if actor_id is None or (isinstance(actor_id, str) and not actor_id.strip()):
            raise ValueError("actor id is required")
        return QueueService(self._persistence, actor_id=actor_id)

    def distribute_normal(self, lead_id: Any, command_id: str) -> AssignmentResult:
        return self._persistence.distribute_normal(
            lead_id,
            _required(command_id, "command id"),
            actor_id=self._actor_id,
        )

    def distribute_ready(self, lead_id: Any, command_id: str) -> AssignmentResult:
        """Assign a ready lead using recurring ownership or the global queue."""
        return self._persistence.distribute_ready(
            lead_id,
            _required(command_id, "command id"),
            actor_id=self._actor_id,
        )

    def assign_recurring(self, lead_id: Any, command_id: str) -> AssignmentResult:
        return self._persistence.assign_recurring(
            lead_id,
            _required(command_id, "command id"),
            actor_id=self._actor_id,
        )

    def assign_temporarily(
        self,
        lead_id: Any,
        seller_id: Any,
        reason: str,
        command_id: str,
    ) -> AssignmentResult:
        return self._persistence.assign_temporarily(
            lead_id,
            seller_id,
            _required(reason, "reason"),
            _required(command_id, "command id"),
            actor_id=self._actor_id,
        )

    def transfer_owner(
        self,
        company_id: Any,
        seller_id: Any,
        reason: str,
        command_id: str,
    ) -> TransferResult:
        return self._persistence.transfer_owner(
            company_id,
            seller_id,
            _required(reason, "reason"),
            _required(command_id, "command id"),
            actor_id=self._actor_id,
        )

    def transfer_lead(
        self,
        lead_id: Any,
        seller_id: Any,
        reason: str,
        command_id: str,
    ) -> AssignmentResult:
        return self._persistence.transfer_lead(
            lead_id,
            seller_id,
            _required(reason, "reason"),
            _required(command_id, "command id"),
            actor_id=self._actor_id,
        )


def _required(value: str, label: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{label} is required")
    return normalized
