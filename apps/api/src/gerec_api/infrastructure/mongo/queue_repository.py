"""MongoDB transaction adapter for queue rotation, ownership and skip credits."""

from __future__ import annotations

from datetime import UTC, datetime
from time import sleep
from typing import Any, Callable, TypeVar

from bson import ObjectId
from pymongo.errors import DuplicateKeyError

from gerec_api.domain.business_time import BusinessClock
from gerec_api.domain.queue import (
    AssignmentResult,
    QueueRules,
    SellerState,
    TransferResult,
)
from gerec_api.infrastructure.mongo.collections import MongoCollections


NORMAL_COMMAND = "queue.distribute_normal"
READY_COMMAND = "queue.distribute_ready"
RECURRING_COMMAND = "queue.assign_recurring"
TEMPORARY_COMMAND = "queue.assign_temporarily"
TRANSFER_COMMAND = "queue.transfer_owner"
QUEUE_STATE_ID = "global"

ResultT = TypeVar("ResultT", AssignmentResult, TransferResult)


class QueueStateError(RuntimeError):
    """Raised when a queue command cannot preserve a domain invariant."""


class _FifoPredecessorPending(QueueStateError):
    """Allows a concurrent older lead a bounded window to commit first."""


class QueueRepository:
    """Commit every queue side effect in one retryable MongoDB transaction."""

    def __init__(
        self,
        database: Any,
        *,
        now: Callable[[], datetime] | None = None,
        business_clock: BusinessClock | None = None,
    ) -> None:
        self._database = database
        self._now = now or (lambda: datetime.now(UTC))
        self._business_clock = business_clock

    def distribute_normal(
        self, lead_id: Any, command_id: str, *, actor_id: Any
    ) -> AssignmentResult:
        pending_error: _FifoPredecessorPending | None = None
        for attempt in range(100):
            try:
                return self._execute(
                    NORMAL_COMMAND,
                    command_id,
                    AssignmentResult,
                    lambda session: self._distribute_normal(
                        lead_id, command_id, actor_id, session
                    ),
                )
            except _FifoPredecessorPending as error:
                pending_error = error
                if attempt < 99:
                    sleep(0.01)
        raise QueueStateError(str(pending_error))

    def distribute_ready(
        self, lead_id: Any, command_id: str, *, actor_id: Any
    ) -> AssignmentResult:
        return self._execute(
            READY_COMMAND,
            command_id,
            AssignmentResult,
            lambda session: self._distribute_ready(lead_id, command_id, actor_id, session),
        )

    def assign_recurring(
        self, lead_id: Any, command_id: str, *, actor_id: Any
    ) -> AssignmentResult:
        return self._execute(
            RECURRING_COMMAND,
            command_id,
            AssignmentResult,
            lambda session: self._assign_recurring(lead_id, command_id, actor_id, session),
        )

    def assign_temporarily(
        self,
        lead_id: Any,
        seller_id: Any,
        reason: str,
        command_id: str,
        *,
        actor_id: Any,
    ) -> AssignmentResult:
        return self._execute(
            TEMPORARY_COMMAND,
            command_id,
            AssignmentResult,
            lambda session: self._assign_temporarily(
                lead_id,
                seller_id,
                reason,
                command_id,
                actor_id,
                session,
            ),
        )

    def transfer_owner(
        self,
        company_id: Any,
        seller_id: Any,
        reason: str,
        command_id: str,
        *,
        actor_id: Any,
    ) -> TransferResult:
        return self._execute(
            TRANSFER_COMMAND,
            command_id,
            TransferResult,
            lambda session: self._transfer_owner(
                company_id,
                seller_id,
                reason,
                command_id,
                actor_id,
                session,
            ),
        )

    def _execute(
        self,
        command_name: str,
        command_id: str,
        result_type: type[ResultT],
        operation: Callable[[Any], ResultT],
    ) -> ResultT:
        receipt = self._receipt(command_name, command_id)
        if receipt is not None:
            return result_type.from_document(receipt["result"])

        def callback(session: Any) -> ResultT:
            existing = self._receipt(command_name, command_id, session=session)
            if existing is not None:
                return result_type.from_document(existing["result"])
            result = operation(session)
            self._command_results.insert_one(
                {
                    "commandName": command_name,
                    "idempotencyKey": command_id,
                    "result": result.to_document(),
                    "createdAt": self._now(),
                },
                session=session,
            )
            return result

        try:
            with self._database.client.start_session() as session:
                return session.with_transaction(callback)
        except DuplicateKeyError:
            receipt = self._receipt(command_name, command_id)
            if receipt is None:
                raise
            return result_type.from_document(receipt["result"])

    def _receipt(
        self,
        command_name: str,
        command_id: str,
        *,
        session: Any | None = None,
    ) -> dict[str, Any] | None:
        options = {} if session is None else {"session": session}
        receipt = self._command_results.find_one({"idempotencyKey": command_id}, **options)
        if receipt is not None and receipt.get("commandName") != command_name:
            raise QueueStateError("idempotency key already belongs to another command")
        return receipt

    def _distribute_normal(
        self,
        lead_id: Any,
        command_id: str,
        actor_id: Any,
        session: Any,
    ) -> AssignmentResult:
        now = self._now()
        lead = self._available_lead(lead_id, session)
        self._require_fifo(lead, session)
        queue_state = self._queue_state.find_one({"_id": QUEUE_STATE_ID}, session=session)
        if queue_state is None:
            raise QueueStateError("global queue state is not initialized")
        sellers = self._seller_states(now, session)
        decision = QueueRules.select_normal(sellers, queue_state["nextSellerId"])

        state_update = self._queue_state.update_one(
            {"_id": QUEUE_STATE_ID, "version": queue_state["version"]},
            {
                "$set": {"nextSellerId": decision.next_seller_id, "updatedAt": now},
                "$inc": {"version": 1},
            },
            session=session,
        )
        if state_update.matched_count != 1:
            raise QueueStateError("queue state changed concurrently")
        for credit_index, seller_id in enumerate(decision.consumed_credit_seller_ids):
            previous_balance = self._balance(seller_id, session)
            consumed = self._skip_balances.update_one(
                {"sellerId": seller_id, "balance": {"$gte": 1}},
                {"$inc": {"balance": -1}, "$set": {"updatedAt": now}},
                session=session,
            )
            if consumed.matched_count != 1:
                raise QueueStateError("skip balance changed concurrently")
            self._record_event(
                event_type="seller.skip_consumed",
                entity_type="seller",
                entity_id=seller_id,
                action="seller.skip_consumed",
                command_id=command_id,
                actor_id=actor_id,
                before={"balance": previous_balance},
                after={"balance": previous_balance - 1},
                now=now,
                session=session,
                event_key=f"{command_id}:seller.skip_consumed:{credit_index}",
            )

        if decision.seller_id is None:
            self._leads.update_one(
                {"_id": lead_id, "currentAssignmentId": None},
                {
                    "$set": {
                        "assignmentStatus": "parked",
                        "parkReason": "no_eligible_seller",
                        "updatedAt": now,
                    }
                },
                session=session,
            )
            result = AssignmentResult(
                lead_id=str(lead_id),
                assignment_id=None,
                seller_id=None,
                assignment_type=None,
                status="parked",
                owner_id=self._owner_id(lead, session),
            )
            self._record_event(
                event_type="lead.parked",
                entity_type="lead",
                entity_id=lead_id,
                action="queue.parked",
                command_id=command_id,
                actor_id=actor_id,
                before={"assignmentStatus": lead.get("assignmentStatus")},
                after={"assignmentStatus": "parked", "parkReason": "no_eligible_seller"},
                now=now,
                session=session,
            )
            return result

        return self._assign_effective(
            lead,
            decision.seller_id,
            "normal",
            None,
            command_id,
            actor_id,
            now,
            session,
        )

    def _distribute_ready(
        self,
        lead_id: Any,
        command_id: str,
        actor_id: Any,
        session: Any,
    ) -> AssignmentResult:
        lead = self._available_lead(lead_id, session)
        company = self._companies.find_one({"_id": lead["companyId"]}, session=session)
        if company is not None and company.get("ownerId") is not None:
            return self._assign_recurring(lead_id, command_id, actor_id, session)
        return self._distribute_normal(lead_id, command_id, actor_id, session)

    def _assign_recurring(
        self,
        lead_id: Any,
        command_id: str,
        actor_id: Any,
        session: Any,
    ) -> AssignmentResult:
        now = self._now()
        lead = self._available_lead(lead_id, session)
        company = self._companies.find_one({"_id": lead["companyId"]}, session=session)
        owner_id = None if company is None else company.get("ownerId")
        if owner_id is None:
            raise QueueStateError("recurring company does not have an owner")
        if not self._seller_operational(owner_id, now, session):
            self._leads.update_one(
                {"_id": lead_id, "currentAssignmentId": None},
                {
                    "$set": {
                        "assignmentStatus": "parked",
                        "parkReason": "owner_unavailable",
                        "updatedAt": now,
                    }
                },
                session=session,
            )
            result = AssignmentResult(
                lead_id=str(lead_id),
                assignment_id=None,
                seller_id=None,
                assignment_type="recurring",
                status="parked",
                owner_id=str(owner_id),
            )
            self._record_event(
                event_type="lead.parked",
                entity_type="lead",
                entity_id=lead_id,
                action="queue.recurring_parked",
                command_id=command_id,
                actor_id=actor_id,
                before={"assignmentStatus": lead.get("assignmentStatus")},
                after={"assignmentStatus": "parked", "parkReason": "owner_unavailable"},
                now=now,
                session=session,
            )
            return result
        self._credit(owner_id, command_id, actor_id, now, session)
        return self._assign_effective(
            lead,
            owner_id,
            "recurring",
            None,
            command_id,
            actor_id,
            now,
            session,
        )

    def _assign_temporarily(
        self,
        lead_id: Any,
        seller_id: Any,
        reason: str,
        command_id: str,
        actor_id: Any,
        session: Any,
    ) -> AssignmentResult:
        now = self._now()
        lead = self._available_lead(lead_id, session)
        if lead.get("assignmentStatus") != "parked" or lead.get("parkReason") != "owner_unavailable":
            raise QueueStateError("temporary assignment requires a recurring parked lead")
        company = self._companies.find_one({"_id": lead["companyId"]}, session=session)
        owner_id = None if company is None else company.get("ownerId")
        if owner_id is None:
            raise QueueStateError("temporary assignment requires a previous owner")
        if owner_id == seller_id:
            raise QueueStateError("temporary seller must differ from the company owner")
        if not self._seller_operational(seller_id, now, session):
            raise QueueStateError("temporary seller is not operational")
        self._credit(seller_id, command_id, actor_id, now, session)
        return self._assign_effective(
            lead,
            seller_id,
            "temporary",
            reason,
            command_id,
            actor_id,
            now,
            session,
        )

    def _transfer_owner(
        self,
        company_id: Any,
        seller_id: Any,
        reason: str,
        command_id: str,
        actor_id: Any,
        session: Any,
    ) -> TransferResult:
        now = self._now()
        company = self._companies.find_one({"_id": company_id}, session=session)
        if company is None:
            raise QueueStateError("company not found")
        user = self._users.find_one({"_id": seller_id, "active": True}, session=session)
        if user is None:
            raise QueueStateError("new owner is not an active seller")
        previous_owner_id = company.get("ownerId")
        self._companies.update_one(
            {"_id": company_id, "ownerId": previous_owner_id},
            {"$set": {"ownerId": seller_id, "updatedAt": now}},
            session=session,
        )
        self._record_event(
            event_type="company.owner_transferred",
            entity_type="company",
            entity_id=company_id,
            action="company.owner_transferred",
            command_id=command_id,
            actor_id=actor_id,
            before={"ownerId": previous_owner_id},
            after={"ownerId": seller_id},
            now=now,
            session=session,
            reason=reason,
        )
        return TransferResult(
            company_id=str(company_id),
            previous_owner_id=(str(previous_owner_id) if previous_owner_id is not None else None),
            owner_id=str(seller_id),
        )

    def _assign_effective(
        self,
        lead: dict[str, Any],
        seller_id: Any,
        assignment_type: str,
        reason: str | None,
        command_id: str,
        actor_id: Any,
        now: datetime,
        session: Any,
    ) -> AssignmentResult:
        company = self._companies.find_one({"_id": lead["companyId"]}, session=session)
        if company is None:
            raise QueueStateError("lead company not found")
        owner_id = company.get("ownerId")
        if assignment_type == "temporary" and owner_id is None:
            raise QueueStateError("temporary assignment cannot claim company ownership")
        assignment = {
            "leadId": lead["_id"],
            "sellerId": seller_id,
            "type": assignment_type,
            "reason": reason,
            "current": True,
            "startedAt": now,
            "endedAt": None,
            "commandId": command_id,
        }
        assignment_id = self._assignments.insert_one(assignment, session=session).inserted_id
        lead_update = {
            "assignmentStatus": "assigned",
            "assigneeId": seller_id,
            "currentAssignmentId": assignment_id,
            "assignmentType": assignment_type,
            "parkReason": None,
            "assignedAt": now,
            "updatedAt": now,
        }
        if self._business_clock is not None:
            cycle_id = ObjectId()
            reminder_at = self._business_clock.add_business_hours(now, 20)
            due_at = self._business_clock.add_business_hours(now, 24)
            self._feedback_cycles.insert_one(
                {
                    "_id": cycle_id,
                    "leadId": lead["_id"],
                    "startAt": now,
                    "reminderAt": reminder_at,
                    "dueAt": due_at,
                    "closedAt": None,
                },
                session=session,
            )
            lead_update.update(
                {
                    "feedbackCycleId": cycle_id,
                    "feedbackReminderAt": reminder_at,
                    "feedbackDueAt": due_at,
                }
            )
        updated = self._leads.update_one(
            {"_id": lead["_id"], "currentAssignmentId": None},
            {"$set": lead_update},
            session=session,
        )
        if updated.matched_count != 1:
            raise QueueStateError("lead already has a current assignment")

        if owner_id is None:
            claimed = self._companies.update_one(
                {"_id": lead["companyId"], "ownerId": None},
                {"$set": {"ownerId": seller_id, "updatedAt": now}},
                session=session,
            )
            if claimed.matched_count == 1:
                owner_id = seller_id
            else:
                owner_id = self._companies.find_one(
                    {"_id": lead["companyId"]}, session=session
                ).get("ownerId")

        self._record_event(
            event_type="lead.assigned",
            entity_type="lead",
            entity_id=lead["_id"],
            action="queue.assigned",
            command_id=command_id,
            actor_id=actor_id,
            before={
                "assignmentStatus": lead.get("assignmentStatus"),
                "assigneeId": lead.get("assigneeId"),
            },
            after={
                "assignmentStatus": "assigned",
                "assigneeId": seller_id,
                "assignmentType": assignment_type,
            },
            now=now,
            session=session,
            reason=reason,
        )
        if self._business_clock is not None:
            cycle_id = lead_update["feedbackCycleId"]
            reminder_at = lead_update["feedbackReminderAt"]
            due_at = lead_update["feedbackDueAt"]
            self._notification_outbox.insert_one(
                {
                    "eventType": "lead.feedback_due_soon",
                    "aggregateId": lead["_id"],
                    "actorId": actor_id,
                    "idempotencyKey": f"{lead['_id']}:{cycle_id}:feedback_due_soon",
                    "cycleId": cycle_id,
                    "scheduledFor": reminder_at,
                    "dueAt": due_at,
                    "status": "scheduled",
                    "attempts": 0,
                    "payload": {"leadId": lead["_id"], "cycleId": cycle_id},
                    "createdAt": now,
                },
                session=session,
            )
        return AssignmentResult(
            lead_id=str(lead["_id"]),
            assignment_id=str(assignment_id),
            seller_id=str(seller_id),
            assignment_type=assignment_type,
            status="assigned",
            owner_id=str(owner_id) if owner_id is not None else None,
        )

    def _seller_states(self, now: datetime, session: Any) -> list[SellerState]:
        queue_documents = sorted(
            self._seller_queue.find({}, session=session),
            key=lambda value: value["position"],
        )
        return [
            SellerState(
                seller_id=item["sellerId"],
                active=(
                    self._users.find_one(
                        {"_id": item["sellerId"], "active": True}, session=session
                    )
                    is not None
                ),
                paused=bool(item.get("paused", False)),
                has_overdue_feedback=self._seller_has_overdue(item["sellerId"], now, session),
                skip_balance=self._balance(item["sellerId"], session),
            )
            for item in queue_documents
        ]

    def _seller_operational(self, seller_id: Any, now: datetime, session: Any) -> bool:
        user = self._users.find_one({"_id": seller_id, "active": True}, session=session)
        queue = self._seller_queue.find_one({"sellerId": seller_id}, session=session)
        return bool(
            user is not None
            and queue is not None
            and not queue.get("paused", False)
            and not self._seller_has_overdue(seller_id, now, session)
        )

    def _seller_has_overdue(self, seller_id: Any, now: datetime, session: Any) -> bool:
        return (
            self._leads.find_one(
                {
                    "assigneeId": seller_id,
                    "assignmentStatus": "assigned",
                    "feedbackDueAt": {"$lt": now},
                },
                session=session,
            )
            is not None
        )

    def _balance(self, seller_id: Any, session: Any) -> int:
        document = self._skip_balances.find_one({"sellerId": seller_id}, session=session)
        balance = 0 if document is None else int(document.get("balance", 0))
        if balance < 0:
            raise QueueStateError("skip balance cannot be negative")
        return balance

    def _credit(
        self,
        seller_id: Any,
        command_id: str,
        actor_id: Any,
        now: datetime,
        session: Any,
    ) -> None:
        previous_balance = self._balance(seller_id, session)
        self._skip_balances.update_one(
            {"sellerId": seller_id},
            {
                "$inc": {"balance": 1},
                "$set": {"updatedAt": now},
                "$setOnInsert": {"sellerId": seller_id},
            },
            upsert=True,
            session=session,
        )
        self._record_event(
            event_type="seller.skip_credited",
            entity_type="seller",
            entity_id=seller_id,
            action="seller.skip_credited",
            command_id=command_id,
            actor_id=actor_id,
            before={"balance": previous_balance},
            after={"balance": previous_balance + 1},
            now=now,
            session=session,
        )

    def _available_lead(self, lead_id: Any, session: Any) -> dict[str, Any]:
        lead = self._leads.find_one({"_id": lead_id, "archivedAt": None}, session=session)
        if lead is None:
            raise QueueStateError("lead not found")
        if lead.get("currentAssignmentId") is not None or lead.get("assigneeId") is not None:
            raise QueueStateError("lead already has a current assignment")
        if lead.get("assignmentStatus") not in {"ready", "parked"}:
            raise QueueStateError("lead is not ready for assignment")
        return lead

    def _require_fifo(self, lead: dict[str, Any], session: Any) -> None:
        candidates = []
        for candidate in self._leads.find(
            {
                "assignmentStatus": {"$in": ["ready", "parked"]},
                "assigneeId": None,
                "archivedAt": None,
            },
            session=session,
        ):
            if candidate.get("parkReason") not in (None, "no_eligible_seller"):
                continue
            candidates.append(candidate)
        if not candidates:
            return
        first = min(
            candidates,
            key=lambda value: (
                value.get("sourceEnteredAt") or datetime.max.replace(tzinfo=UTC),
                value.get("sourceLeadId") or str(value["_id"]),
            ),
        )
        if first["_id"] != lead["_id"]:
            raise _FifoPredecessorPending("normal lead would bypass FIFO order")

    def _owner_id(self, lead: dict[str, Any], session: Any) -> str | None:
        company = self._companies.find_one({"_id": lead["companyId"]}, session=session)
        owner_id = None if company is None else company.get("ownerId")
        return str(owner_id) if owner_id is not None else None

    def _record_event(
        self,
        *,
        event_type: str,
        entity_type: str,
        entity_id: Any,
        action: str,
        command_id: str,
        actor_id: Any,
        before: dict[str, Any],
        after: dict[str, Any],
        now: datetime,
        session: Any,
        reason: str | None = None,
        event_key: str | None = None,
    ) -> None:
        self._audit_log.insert_one(
            {
                "actorId": actor_id,
                "action": action,
                "entityType": entity_type,
                "entityId": entity_id,
                "before": before,
                "after": after,
                "reason": reason,
                "createdAt": now,
                "correlationId": command_id,
            },
            session=session,
        )
        self._notification_outbox.insert_one(
            {
                "eventType": event_type,
                "aggregateId": entity_id,
                "actorId": actor_id,
                "idempotencyKey": event_key or f"{command_id}:{event_type}",
                "status": "pending",
                "attempts": 0,
                "payload": after,
                "createdAt": now,
            },
            session=session,
        )

    @property
    def _users(self):
        return self._database[MongoCollections.USERS]

    @property
    def _seller_queue(self):
        return self._database[MongoCollections.SELLER_QUEUE]

    @property
    def _queue_state(self):
        return self._database[MongoCollections.QUEUE_STATE]

    @property
    def _skip_balances(self):
        return self._database[MongoCollections.SKIP_BALANCES]

    @property
    def _companies(self):
        return self._database[MongoCollections.COMPANIES]

    @property
    def _leads(self):
        return self._database[MongoCollections.LEADS]

    @property
    def _assignments(self):
        return self._database[MongoCollections.ASSIGNMENTS]

    @property
    def _feedback_cycles(self):
        return self._database[MongoCollections.FEEDBACK_CYCLES]

    @property
    def _audit_log(self):
        return self._database[MongoCollections.AUDIT_LOG]

    @property
    def _notification_outbox(self):
        return self._database[MongoCollections.NOTIFICATION_OUTBOX]

    @property
    def _command_results(self):
        return self._database[MongoCollections.COMMAND_RESULTS]
