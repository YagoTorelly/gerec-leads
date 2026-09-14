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
    TreatmentCommand,
    TreatmentResult,
    Clock,
    SystemClock,
)
from gerec_api.infrastructure.mongo.collections import MongoCollections


FEEDBACK_COMMAND = "operations.register_feedback"
ATTEMPT_COMMAND = "operations.register_attempt"
OUTCOME_COMMAND = "operations.register_outcome"
TREATMENT_COMMAND = "operations.register_treatment"
TERMINAL_CONVERSIONS = frozenset({"closed_no_conversion", "won"})
ResultT = TypeVar("ResultT", FeedbackResult, AttemptResult, OutcomeResult, TreatmentResult)


class OperationsStateError(RuntimeError):
    """Raised when an operations command would violate a domain invariant."""


class OperationsPermissionError(OperationsStateError, PermissionError):
    """Raised when an authenticated actor is outside a command's allowed scope."""


class MongoOperationsRepository:
    """Commit each operational command and all its effects in one Mongo transaction."""

    def __init__(
        self,
        database: Any,
        *,
        clock: Clock | None = None,
    ) -> None:
        self._database = database
        self._clock = clock or SystemClock()

    def register_feedback(
        self,
        command: FeedbackCommand,
        *,
        actor_id: Any,
        actor_role: str,
        now: datetime,
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
                session,
            ),
        )

    def register_treatment(
        self,
        command: TreatmentCommand,
        *,
        actor_id: Any,
        actor_role: str,
        now: datetime,
    ) -> TreatmentResult:
        return self._execute(
            TREATMENT_COMMAND,
            command.idempotency_key,
            TreatmentResult,
            now,
            lambda session, transaction_now: self._register_treatment(
                command,
                actor_id,
                actor_role,
                transaction_now,
                session,
            ),
            actor_id=actor_id,
            aggregate_id=command.lead_id,
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
        *,
        actor_id: Any | None = None,
        aggregate_id: Any | None = None,
    ) -> ResultT:
        receipt = self._receipt(command_name, idempotency_key)
        if receipt is not None:
            return self._replay_result(
                receipt,
                result_type,
                actor_id=actor_id,
                aggregate_id=aggregate_id,
            )

        def callback(session: Any) -> ResultT:
            existing = self._receipt(command_name, idempotency_key, session=session)
            if existing is not None:
                return self._replay_result(
                    existing,
                    result_type,
                    actor_id=actor_id,
                    aggregate_id=aggregate_id,
                )
            # `now` is MongoDB server time captured once before the transaction.
            # Reusing it avoids the forbidden `hello` command inside a transaction
            # and gives retryable callbacks one stable timestamp.
            transaction_now = now
            result = operation(session, transaction_now)
            self._command_results.insert_one(
                {
                    "commandName": command_name,
                    "idempotencyKey": idempotency_key,
                    "result": result.to_document(),
                    "createdAt": transaction_now,
                    **({"actorId": actor_id} if actor_id is not None else {}),
                    **({"aggregateId": aggregate_id} if aggregate_id is not None else {}),
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
            return self._replay_result(
                receipt,
                result_type,
                actor_id=actor_id,
                aggregate_id=aggregate_id,
            )

    @staticmethod
    def _replay_result(
        receipt: dict[str, Any],
        result_type: type[ResultT],
        *,
        actor_id: Any | None,
        aggregate_id: Any | None,
    ) -> ResultT:
        if actor_id is not None:
            if "actorId" not in receipt or "aggregateId" not in receipt:
                raise OperationsStateError("idempotency receipt lacks actor binding")
            if receipt["actorId"] != actor_id:
                raise OperationsPermissionError("idempotency receipt belongs to another actor")
            if receipt["aggregateId"] != aggregate_id:
                raise OperationsStateError("idempotency key belongs to another aggregate")
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
                    {"lead": lead_before},
                    {
                        "lead": self._leads.find_one({"_id": command.lead_id}, session=session),
                        "feedbackId": feedback_id,
                    },
                    now,
                ),
                session=session,
            )
            return FeedbackResult(str(command.lead_id), str(feedback_id), "administrative_note")

        self._require_current_seller(lead, actor_id, actor_role)
        self._require_active(lead)
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
        updated = self._leads.update_one(
            {"_id": command.lead_id},
            {"$set": {"updatedAt": now}},
            session=session,
        )
        if updated.matched_count != 1:
            raise OperationsStateError("lead changed concurrently")
        self._record_event(
            "lead.feedback_recorded",
            command.lead_id,
            actor_id,
            command.idempotency_key,
            {"lead": lead_before},
            {"lead": self._leads.find_one({"_id": command.lead_id}, session=session)},
            now,
            session,
        )
        return FeedbackResult(str(command.lead_id), str(feedback_id), "recorded")

    def _register_treatment(
        self,
        command: TreatmentCommand,
        actor_id: Any,
        actor_role: str,
        now: datetime,
        session: Any,
    ) -> TreatmentResult:
        lead = self._lead(command.lead_id, session)
        self._require_current_seller(lead, actor_id, actor_role)
        lead_before = deepcopy(lead)
        treatment_id = ObjectId()
        comment_count = int(lead.get("commentCount", 0)) + 1

        self._lead_treatments.insert_one(
            {
                "_id": treatment_id,
                "leadId": command.lead_id,
                "sellerId": actor_id,
                "comment": command.comment,
                "commercialStatus": command.commercial_status,
                "isDisqualified": command.is_disqualified,
                "idempotencyKey": command.idempotency_key,
                "createdAt": now,
            },
            session=session,
        )

        update: dict[str, Any] = {
            "commercialStatus": command.commercial_status,
            "isDisqualified": command.is_disqualified,
            "commentCount": comment_count,
            "lastCommentAt": now,
            "updatedAt": now,
        }
        changed = self._leads.update_one(
            {
                "_id": command.lead_id
            },
            {"$set": update},
            session=session,
        )
        if changed.matched_count != 1:
            raise OperationsStateError("lead changed concurrently")
        lead_after = self._leads.find_one({"_id": command.lead_id}, session=session)
        self._record_event(
            "lead.treatment_recorded",
            command.lead_id,
            actor_id,
            command.idempotency_key,
            {"lead": lead_before},
            {"lead": lead_after, "treatmentId": treatment_id},
            now,
            session,
        )
        return TreatmentResult(
            str(command.lead_id),
            str(treatment_id),
            "recorded",
            command.commercial_status,
            command.is_disqualified,
            comment_count,
            lead_after["updatedAt"],
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
        elif command.disqualification_reason == "outside_sp":
            if str(lead.get("state", "")).strip().upper() == "SP":
                raise OperationsStateError("outside SP reason requires a lead outside SP")
        elif command.disqualification_reason == "no_cnpj":
            company = self._companies.find_one({"_id": lead["companyId"]}, session=session)
            document = "" if company is None else str(company.get("documentNormalized", ""))
            if len(document) == 14:
                raise OperationsStateError("company already has CNPJ")

        outcome_event_id = ObjectId()
        qualification_status, conversion_status = self._statuses(command.outcome, lead)
        update: dict[str, Any] = {
            "qualificationStatus": qualification_status,
            "conversionStatus": conversion_status,
            "qualificationDecidedAt": now,
            "outcomeEventId": outcome_event_id,
            "updatedAt": now,
        }

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
            {
                "_id": command.lead_id
            },
            {"$set": update},
            session=session,
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
            {"lead": lead_before, "company": company_before},
            {"lead": self._leads.find_one({"_id": command.lead_id}, session=session), "company": (self._companies.find_one({"_id": lead["companyId"]}, session=session) if company_before is not None else None), "outcomeEventId": outcome_event_id, "saleId": sale_id},
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
            raise OperationsPermissionError("seller is not the current lead assignee")
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
                "attempts": 0,
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

    @property
    def _lead_treatments(self):
        return self._database[MongoCollections.LEAD_TREATMENTS]
