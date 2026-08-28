"""MongoDB transaction adapter for feedback, attempts and outcomes."""

from __future__ import annotations

from copy import deepcopy
from datetime import date, datetime
from typing import Any, Callable, TypeVar

from bson import ObjectId
from pymongo.errors import DuplicateKeyError

from gerec_api.domain.operations import (
    AttemptCommand,
    AttemptResult,
    FeedbackCommand,
    FeedbackResult,
    OutcomeCommand,
    OutcomeResult,
    Clock,
    SystemClock,
)
from gerec_api.domain.business_time import BusinessClock
from gerec_api.infrastructure.mongo.collections import MongoCollections


FEEDBACK_COMMAND = "operations.register_feedback"
ATTEMPT_COMMAND = "operations.register_attempt"
OUTCOME_COMMAND = "operations.register_outcome"
TERMINAL_CONVERSIONS = frozenset({"closed_no_conversion", "won"})
ResultT = TypeVar("ResultT", FeedbackResult, AttemptResult, OutcomeResult)


class OperationsStateError(RuntimeError):
    """Raised when an operations command would violate a domain invariant."""


class MongoOperationsRepository:
    """Commit each operational command and all its effects in one Mongo transaction."""

    def __init__(
        self,
        database: Any,
        *,
        clock: Clock | None = None,
        business_clock: BusinessClock | None = None,
    ) -> None:
        self._database = database
        self._clock = clock or SystemClock()
        self._business_clock = business_clock

    def register_feedback(
        self,
        command: FeedbackCommand,
        *,
        actor_id: Any,
        actor_role: str,
        now: datetime,
        reminder_at: datetime | None,
        due_at: datetime | None,
    ) -> FeedbackResult:
        return self._execute(
            FEEDBACK_COMMAND,
            command.idempotency_key,
            FeedbackResult,
            now,
            lambda session, transaction_now: self._register_feedback(
                command,
                actor_id,
                actor_role,
                transaction_now,
                reminder_at,
                due_at,
                session,
            ),
        )

    def register_attempt(
        self,
        command: AttemptCommand,
        *,
        actor_id: Any,
        actor_role: str,
        now: datetime,
        business_date: date,
    ) -> AttemptResult:
        return self._execute(
            ATTEMPT_COMMAND,
            command.idempotency_key,
            AttemptResult,
            now,
            lambda session, transaction_now: self._register_attempt(
                command, actor_id, actor_role, transaction_now, business_date, session
            ),
        )

    def register_outcome(
        self,
        command: OutcomeCommand,
        *,
        actor_id: Any,
        actor_role: str,
        now: datetime,
    ) -> OutcomeResult:
        return self._execute(
            OUTCOME_COMMAND,
            command.idempotency_key,
            OutcomeResult,
            now,
            lambda session, transaction_now: self._register_outcome(
                command, actor_id, actor_role, transaction_now, session
            ),
        )

    def _execute(
        self,
        command_name: str,
        idempotency_key: str,
        result_type: type[ResultT],
        now: datetime,
        operation: Callable[[Any, datetime], ResultT],
    ) -> ResultT:
        receipt = self._receipt(command_name, idempotency_key)
        if receipt is not None:
            return result_type.from_document(receipt["result"])

        def callback(session: Any) -> ResultT:
            existing = self._receipt(command_name, idempotency_key, session=session)
            if existing is not None:
                return result_type.from_document(existing["result"])
            transaction_now = self._clock.now(session)
            result = operation(session, transaction_now)
            self._command_results.insert_one(
                {
                    "commandName": command_name,
                    "idempotencyKey": idempotency_key,
                    "result": result.to_document(),
                    "createdAt": transaction_now,
                },
                session=session,
            )
            return result

        try:
            with self._database.client.start_session() as session:
                return session.with_transaction(callback)
        except DuplicateKeyError:
            receipt = self._receipt(command_name, idempotency_key)
            if receipt is None:
                raise OperationsStateError("operation conflicted with a concurrent command") from None
            return result_type.from_document(receipt["result"])

    def _receipt(
        self,
        command_name: str,
        idempotency_key: str,
        *,
        session: Any | None = None,
    ) -> dict[str, Any] | None:
        options = {} if session is None else {"session": session}
        receipt = self._command_results.find_one(
            {"idempotencyKey": idempotency_key}, **options
        )
        if receipt is not None and receipt.get("commandName") != command_name:
            raise OperationsStateError("idempotency key already belongs to another command")
        return receipt

    def _register_feedback(
        self,
        command: FeedbackCommand,
        actor_id: Any,
        actor_role: str,
        now: datetime,
        reminder_at: datetime | None,
        due_at: datetime | None,
        session: Any,
    ) -> FeedbackResult:
        lead = self._lead(command.lead_id, session)
        lead_before = deepcopy(lead)
        feedback_id = ObjectId()
        if command.administrative_note:
            if actor_role != "admin":
                raise OperationsStateError("administrative note requires admin")
            self._feedbacks.insert_one(
                {
                    "_id": feedback_id,
                    "leadId": command.lead_id,
                    "actorId": actor_id,
                    "comment": command.comment,
                    "kind": "administrative_note",
                    "createdAt": now,
                },
                session=session,
            )
            self._audit_log.insert_one(
                self._audit_document(
                    actor_id,
                    "lead.administrative_note_added",
                    command.lead_id,
                    command.idempotency_key,
                    {},
                    {"feedbackId": feedback_id},
                    now,
                ),
                session=session,
            )
            return FeedbackResult(
                str(command.lead_id), str(feedback_id), None, "administrative_note", None, None
            )

        if self._business_clock is None:
            raise OperationsStateError("business clock is required for seller feedback")
        reminder_at = self._business_clock.add_business_hours(now, 20)
        due_at = self._business_clock.add_business_hours(now, 24)
        self._require_current_seller(lead, actor_id, actor_role)
        self._require_active(lead)
        cycle = self._feedback_cycles.find_one(
            {"leadId": command.lead_id, "closedAt": None}, session=session
        )
        cycle_before = deepcopy(cycle)
        if cycle is None:
            raise OperationsStateError("active lead does not have an open feedback cycle")
        closed = self._feedback_cycles.update_one(
            {"_id": cycle["_id"], "closedAt": None},
            {"$set": {"closedAt": now, "closedByFeedbackId": feedback_id}},
            session=session,
        )
        if closed.matched_count != 1:
            raise OperationsStateError("feedback cycle changed concurrently")

        cycle_id = ObjectId()
        self._feedbacks.insert_one(
            {
                "_id": feedback_id,
                "leadId": command.lead_id,
                "sellerId": actor_id,
                "comment": command.comment,
                "kind": "seller_feedback",
                "contactStarted": True,
                "createdAt": now,
            },
            session=session,
        )
        self._feedback_cycles.insert_one(
            {
                "_id": cycle_id,
                "leadId": command.lead_id,
                "startAt": now,
                "reminderAt": reminder_at,
                "dueAt": due_at,
                "closedAt": None,
            },
            session=session,
        )
        updated = self._leads.update_one(
            {"_id": command.lead_id},
            {
                "$set": {
                    "feedbackCycleId": cycle_id,
                    "feedbackReminderAt": reminder_at,
                    "feedbackDueAt": due_at,
                    "updatedAt": now,
                }
            },
            session=session,
        )
        if updated.matched_count != 1:
            raise OperationsStateError("lead changed concurrently")
        self._record_event(
            "lead.feedback_recorded",
            command.lead_id,
            actor_id,
            command.idempotency_key,
            {"lead": lead_before, "cycle": cycle_before},
            {"lead": self._leads.find_one({"_id": command.lead_id}, session=session), "cycle": self._feedback_cycles.find_one({"_id": cycle_id}, session=session)},
            now,
            session,
        )
        self._schedule_reminder(
            command.lead_id,
            cycle_id,
            reminder_at,
            due_at,
            actor_id,
            command.idempotency_key,
            now,
            session,
        )
        return FeedbackResult(
            str(command.lead_id),
            str(feedback_id),
            str(cycle_id),
            "recorded",
            reminder_at,
            due_at,
        )

    def _register_attempt(
        self,
        command: AttemptCommand,
        actor_id: Any,
        actor_role: str,
        now: datetime,
        business_date: date,
        session: Any,
    ) -> AttemptResult:
        lead = self._lead(command.lead_id, session)
        lead_before = deepcopy(lead)
        self._require_current_seller(lead, actor_id, actor_role)
        self._require_active(lead)
        date_key = business_date.isoformat()
        if self._contact_attempts.find_one(
            {"leadId": command.lead_id, "businessDate": date_key}, session=session
        ) is not None:
            raise OperationsStateError("only one attempt may count on the same business date")
        attempts = self._contact_attempts.count_documents(
            {"leadId": command.lead_id}, session=session
        )
        if attempts >= 5:
            raise OperationsStateError("contact attempt limit is five")

        attempt_id = ObjectId()
        sequence = attempts + 1
        self._contact_attempts.insert_one(
            {
                "_id": attempt_id,
                "leadId": command.lead_id,
                "sellerId": actor_id,
                "channel": "whatsapp",
                "comment": command.comment,
                "businessDate": date_key,
                "sequence": sequence,
                "createdAt": now,
            },
            session=session,
        )
        self._audit_log.insert_one(
            self._audit_document(
                actor_id,
                "lead.contact_attempt_recorded",
                command.lead_id,
                command.idempotency_key,
                {"lead": lead_before},
                {"lead": self._leads.find_one({"_id": command.lead_id}, session=session), "attempt": {"attempts": sequence, "businessDate": date_key}},
                now,
            ),
            session=session,
        )
        return AttemptResult(
            str(command.lead_id),
            str(attempt_id),
            sequence,
            business_date,
            sequence == 5,
            "recorded",
        )

    def _register_outcome(
        self,
        command: OutcomeCommand,
        actor_id: Any,
        actor_role: str,
        now: datetime,
        session: Any,
    ) -> OutcomeResult:
        lead = self._lead(command.lead_id, session)
        lead_before = deepcopy(lead)
        if actor_role == "seller":
            self._require_current_seller(lead, actor_id, actor_role)
        elif actor_role != "admin":
            raise OperationsStateError("outcome actor is not authorized")
        self._require_active(lead)
        if command.disqualification_reason == "no_answer_after_5_attempts":
            attempts = self._contact_attempts.count_documents(
                {"leadId": command.lead_id}, session=session
            )
            if attempts < 5:
                raise OperationsStateError("no-answer disqualification requires five attempts")

        outcome_event_id = ObjectId()
        qualification_status, conversion_status = self._statuses(command.outcome, lead)
        terminal = command.outcome != "qualified_follow_up"
        update: dict[str, Any] = {
            "qualificationStatus": qualification_status,
            "conversionStatus": conversion_status,
            "qualificationDecidedAt": now,
            "outcomeEventId": outcome_event_id,
            "updatedAt": now,
        }
        if terminal:
            update.update({"feedbackDueAt": None, "feedbackReminderAt": None})
            cycle = self._feedback_cycles.find_one(
                {"leadId": command.lead_id, "closedAt": None}, session=session
            )
            cycle_before = deepcopy(cycle)
            if cycle is not None:
                closed = self._feedback_cycles.update_one(
                    {"_id": cycle["_id"], "closedAt": None},
                    {"$set": {"closedAt": now, "closedByOutcomeId": outcome_event_id}},
                    session=session,
                )
                if closed.matched_count != 1:
                    raise OperationsStateError("feedback cycle changed concurrently")

        sale_id: ObjectId | None = None
        company_before = None
        if command.outcome == "won":
            company = self._companies.find_one({"_id": lead["companyId"]}, session=session)
            if company is None:
                raise OperationsStateError("lead company does not exist")
            company_before = deepcopy(company)
            sale_id = ObjectId()
            self._companies.update_one(
                {"_id": lead["companyId"], "clientSince": None},
                {"$set": {"clientSince": now, "updatedAt": now}},
                session=session,
            )
            self._sales.insert_one(
                {
                    "_id": sale_id,
                    "leadId": command.lead_id,
                    "creditedSellerId": lead["assigneeId"],
                    "wonAt": now,
                    "comment": command.comment,
                    "reversedAt": None,
                },
                session=session,
            )
            update["wonAt"] = now

        changed = self._leads.update_one(
            {"_id": command.lead_id}, {"$set": update}, session=session
        )
        if changed.matched_count != 1:
            raise OperationsStateError("lead changed concurrently")
        self._qualification_events.insert_one(
            {
                "_id": outcome_event_id,
                "leadId": command.lead_id,
                "actorId": actor_id,
                "outcome": command.outcome,
                "reason": command.disqualification_reason,
                "comment": command.comment,
                "createdAt": now,
            },
            session=session,
        )
        self._record_event(
            self._event_type(command.outcome),
            command.lead_id,
            actor_id,
            command.idempotency_key,
            {"lead": lead_before, "cycle": cycle_before if terminal else None, "company": company_before},
            {"lead": self._leads.find_one({"_id": command.lead_id}, session=session), "cycle": (self._feedback_cycles.find_one({"_id": cycle["_id"]}, session=session) if terminal and cycle is not None else None), "company": (self._companies.find_one({"_id": lead["companyId"]}, session=session) if company_before is not None else None), "outcomeEventId": outcome_event_id, "saleId": sale_id},
            now,
            session,
        )
        return OutcomeResult(
            str(command.lead_id),
            str(outcome_event_id),
            command.outcome,
            str(sale_id) if sale_id is not None else None,
            "recorded",
        )

    def _lead(self, lead_id: Any, session: Any) -> dict[str, Any]:
        lead = self._leads.find_one({"_id": lead_id}, session=session)
        if lead is None or lead.get("archivedAt") is not None:
            raise OperationsStateError("active lead does not exist")
        return lead

    @staticmethod
    def _require_current_seller(lead: dict[str, Any], actor_id: Any, actor_role: str) -> None:
        if actor_role != "seller" or lead.get("assigneeId") != actor_id:
            raise OperationsStateError("seller is not the current lead assignee")
        if lead.get("assignmentStatus") != "assigned":
            raise OperationsStateError("lead is not currently assigned")

    @staticmethod
    def _require_active(lead: dict[str, Any]) -> None:
        if lead.get("qualificationStatus") == "disqualified" or lead.get(
            "conversionStatus"
        ) in TERMINAL_CONVERSIONS:
            raise OperationsStateError("lead already has a final outcome")

    @staticmethod
    def _statuses(outcome: str, lead: dict[str, Any]) -> tuple[str, str]:
        if outcome == "qualified_follow_up":
            return "qualified", "qualified_follow_up"
        if outcome == "qualified_closed_no_conversion":
            return "qualified", "closed_no_conversion"
        if outcome == "disqualified":
            return "disqualified", str(lead.get("conversionStatus", "active"))
        return "qualified", "won"

    @staticmethod
    def _event_type(outcome: str) -> str:
        return {
            "qualified_follow_up": "lead.qualified",
            "qualified_closed_no_conversion": "lead.closed_without_conversion",
            "disqualified": "lead.disqualified",
            "won": "lead.won",
        }[outcome]

    @staticmethod
    def _audit_document(
        actor_id: Any,
        action: str,
        lead_id: Any,
        command_id: str,
        before: dict[str, Any],
        after: dict[str, Any],
        now: datetime,
    ) -> dict[str, Any]:
        return {
            "actorId": actor_id,
            "action": action,
            "entityType": "lead",
            "entityId": lead_id,
            "before": before,
            "after": after,
            "createdAt": now,
            "correlationId": command_id,
        }

    def _record_event(
        self,
        event_type: str,
        lead_id: Any,
        actor_id: Any,
        command_id: str,
        before: dict[str, Any],
        after: dict[str, Any],
        now: datetime,
        session: Any,
    ) -> None:
        self._audit_log.insert_one(
            self._audit_document(actor_id, event_type, lead_id, command_id, before, after, now),
            session=session,
        )
        self._notification_outbox.insert_one(
            {
                "_id": ObjectId(),
                "eventType": event_type,
                "aggregateId": lead_id,
                "actorId": actor_id,
                "idempotencyKey": f"{command_id}:{event_type}",
                "payload": after,
                "status": "pending",
                "createdAt": now,
            },
            session=session,
        )

    def _schedule_reminder(
        self,
        lead_id: Any,
        cycle_id: Any,
        reminder_at: datetime | None,
        due_at: datetime | None,
        actor_id: Any,
        command_id: str,
        now: datetime,
        session: Any,
    ) -> None:
        if reminder_at is None:
            return
        self._notification_outbox.insert_one(
            {
                "_id": ObjectId(),
                "eventType": "lead.feedback_due_soon",
                "aggregateId": lead_id,
                "actorId": actor_id,
                "idempotencyKey": f"{lead_id}:{cycle_id}:feedback_due_soon",
                "cycleId": cycle_id,
                "scheduledFor": reminder_at,
                "dueAt": due_at,
                "status": "scheduled",
                "payload": {"leadId": lead_id, "cycleId": cycle_id},
                "createdAt": now,
            },
            session=session,
        )

    @property
    def _leads(self):
        return self._database[MongoCollections.LEADS]

    @property
    def _companies(self):
        return self._database[MongoCollections.COMPANIES]

    @property
    def _feedback_cycles(self):
        return self._database[MongoCollections.FEEDBACK_CYCLES]

    @property
    def _feedbacks(self):
        return self._database[MongoCollections.FEEDBACKS]

    @property
    def _contact_attempts(self):
        return self._database[MongoCollections.CONTACT_ATTEMPTS]

    @property
    def _qualification_events(self):
        return self._database[MongoCollections.QUALIFICATION_EVENTS]

    @property
    def _sales(self):
        return self._database[MongoCollections.SALES]

    @property
    def _notification_outbox(self):
        return self._database[MongoCollections.NOTIFICATION_OUTBOX]

    @property
    def _audit_log(self):
        return self._database[MongoCollections.AUDIT_LOG]

    @property
    def _command_results(self):
        return self._database[MongoCollections.COMMAND_RESULTS]
