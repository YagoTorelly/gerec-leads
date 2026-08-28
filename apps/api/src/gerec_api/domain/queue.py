"""Domain rules and narrow command interface for the global lead queue."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Protocol, Sequence


@dataclass(frozen=True)
class SellerState:
    seller_id: Any
    active: bool
    paused: bool
    has_overdue_feedback: bool
    skip_balance: int


@dataclass(frozen=True)
class QueueDecision:
    seller_id: Any | None
    next_seller_id: Any
    consumed_credit_seller_ids: tuple[Any, ...] = ()
    unavailable_seller_ids: tuple[Any, ...] = ()


class QueueRules:
    @staticmethod
    def select_normal(sellers: Sequence[SellerState], next_seller_id: Any) -> QueueDecision:
        if not sellers:
            raise ValueError("seller queue cannot be empty")
        try:
            cursor = next(
                index for index, seller in enumerate(sellers) if seller.seller_id == next_seller_id
            )
        except StopIteration as error:
            raise ValueError("queue cursor does not reference a seller") from error

        operational = [
            seller
            for seller in sellers
            if seller.active and not seller.paused and not seller.has_overdue_feedback
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
            if not seller.active or seller.paused or seller.has_overdue_feedback:
                unavailable.append(seller.seller_id)
                continue
            if balances[seller.seller_id] > 0:
                balances[seller.seller_id] -= 1
                consumed.append(seller.seller_id)
                continue
            return QueueDecision(
                seller_id=seller.seller_id,
                next_seller_id=sellers[cursor].seller_id,
                consumed_credit_seller_ids=tuple(consumed),
                unavailable_seller_ids=tuple(unavailable),
            )


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
    def distribute_normal(self, lead_id: Any, command_id: str) -> AssignmentResult: ...

    def assign_recurring(self, lead_id: Any, command_id: str) -> AssignmentResult: ...

    def assign_temporarily(
        self,
        lead_id: Any,
        seller_id: Any,
        reason: str,
        command_id: str,
    ) -> AssignmentResult: ...

    def transfer_owner(
        self,
        company_id: Any,
        seller_id: Any,
        reason: str,
        command_id: str,
    ) -> TransferResult: ...


class QueueService:
    """Expose queue mutations without leaking MongoDB details to routes or workers."""

    def __init__(self, persistence: QueuePersistence) -> None:
        self._persistence = persistence

    def distribute_normal(self, lead_id: Any, command_id: str) -> AssignmentResult:
        return self._persistence.distribute_normal(lead_id, _required(command_id, "command id"))

    def assign_recurring(self, lead_id: Any, command_id: str) -> AssignmentResult:
        return self._persistence.assign_recurring(lead_id, _required(command_id, "command id"))

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
        )


def _required(value: str, label: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{label} is required")
    return normalized
