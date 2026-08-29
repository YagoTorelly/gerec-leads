"""Integrated transaction coverage for feedback, attempts and outcomes."""

from copy import deepcopy
from datetime import date, datetime, timedelta
from types import SimpleNamespace
from typing import Any
from zoneinfo import ZoneInfo

import pytest
from bson import ObjectId
from fastapi.testclient import TestClient

from gerec_api.auth.dependencies import get_current_user
from gerec_api.auth.sessions import CurrentUser
from gerec_api.config import Settings
from gerec_api.domain.business_time import BusinessClock
from gerec_api.domain.operations import (
    AttemptCommand,
    FeedbackCommand,
    OperationsService,
    OutcomeCommand,
    TreatmentCommand,
)
from gerec_api.infrastructure.mongo.operations_repository import (
    MongoOperationsRepository,
    OperationsStateError,
)
from gerec_api.main import create_app


SAO_PAULO = ZoneInfo("America/Sao_Paulo")
NOW = datetime(2026, 9, 4, 14, 0, tzinfo=SAO_PAULO)


class NoHolidays:
    def is_holiday(self, day: date) -> bool:
        return False


class FixedClock:
    def now(self, session=None) -> datetime:
        return NOW


class SessionClock:
    def __init__(self, value: datetime) -> None:
        self.value = value
        self.sessions = []

    def now(self, session=None) -> datetime:
        self.sessions.append(session)
        return self.value


class FakeSession:
    def __init__(self, database: "FakeDatabase") -> None:
        self._database = database

    def __enter__(self):
        return self

    def __exit__(self, *_: Any) -> None:
        return None

    def with_transaction(self, callback):
        snapshot = {name: deepcopy(collection.documents) for name, collection in self._database.items()}
        try:
            return callback(self)
        except Exception:
            for name in set(self._database) - set(snapshot):
                del self._database[name]
            for name, documents in snapshot.items():
                self._database[name].documents = documents
            raise


class FakeClient:
    def __init__(self, database: "FakeDatabase") -> None:
        self._database = database

    def start_session(self) -> FakeSession:
        return FakeSession(self._database)


class FakeCollection:
    def __init__(self) -> None:
        self.documents: list[dict[str, Any]] = []
        self.fail_next_insert = False

    def find_one(self, query: dict[str, Any], **_: Any):
        return next((document for document in self.documents if _matches(document, query)), None)

    def count_documents(self, query: dict[str, Any], **_: Any) -> int:
        return sum(_matches(document, query) for document in self.documents)

    def insert_one(self, document: dict[str, Any], **_: Any):
        if self.fail_next_insert:
            self.fail_next_insert = False
            raise RuntimeError("injected insert failure")
        stored = deepcopy(document)
        stored.setdefault("_id", ObjectId())
        self.documents.append(stored)
        return SimpleNamespace(inserted_id=stored["_id"])

    def update_one(self, query: dict[str, Any], update: dict[str, Any], **_: Any):
        document = self.find_one(query)
        if document is None:
            return SimpleNamespace(matched_count=0, modified_count=0)
        before = deepcopy(document)
        document.update(deepcopy(update.get("$set", {})))
        for key, amount in update.get("$inc", {}).items():
            document[key] = document.get(key, 0) + amount
        return SimpleNamespace(matched_count=1, modified_count=int(document != before))


class FakeDatabase(dict):
    def __init__(self) -> None:
        super().__init__()
        self.client = FakeClient(self)

    def __getitem__(self, name: str) -> FakeCollection:
        if name not in self:
            self[name] = FakeCollection()
        return super().__getitem__(name)


def _matches(document: dict[str, Any], query: dict[str, Any]) -> bool:
    for key, expected in query.items():
        actual = document.get(key)
        if isinstance(expected, dict):
            if "$in" in expected and actual not in expected["$in"]:
                return False
            if "$ne" in expected and actual == expected["$ne"]:
                return False
            if "$gte" in expected and actual < expected["$gte"]:
                return False
        elif actual != expected:
            return False
    return True


def _seed_assigned_lead(database: FakeDatabase, *, state: str = "SP"):
    seller_id = ObjectId()
    company_id = ObjectId()
    lead_id = ObjectId()
    cycle_id = ObjectId()
    database["companies"].insert_one(
        {"_id": company_id, "ownerId": seller_id, "clientSince": None}
    )
    database["leads"].insert_one(
        {
            "_id": lead_id,
            "companyId": company_id,
            "assigneeId": seller_id,
            "assignmentStatus": "assigned",
            "qualificationStatus": "pending",
            "conversionStatus": "active",
            "feedbackDueAt": NOW - timedelta(hours=1),
            "feedbackCycleId": cycle_id,
            "state": state,
            "archivedAt": None,
        }
    )
    database["feedback_cycles"].insert_one(
        {
            "_id": cycle_id,
            "leadId": lead_id,
            "startAt": NOW - timedelta(days=2),
            "reminderAt": NOW - timedelta(hours=5),
            "dueAt": NOW - timedelta(hours=1),
            "closedAt": None,
        }
    )
    return lead_id, company_id, seller_id, cycle_id


def _service(database: FakeDatabase, seller_id: Any, *, role: str = "seller") -> OperationsService:
    repository = MongoOperationsRepository(
        database,
        clock=FixedClock(),
        business_clock=BusinessClock(NoHolidays()),
    )
    return OperationsService(
        repository,
        business_clock=BusinessClock(NoHolidays()),
        clock=FixedClock(),
    ).with_actor(seller_id, role)


def test_ac20_feedback_closes_previous_cycle_and_opens_the_next_atomically() -> None:
    """Breaks if a valid feedback leaves two open cycles or misses its operational event."""
    database = FakeDatabase()
    lead_id, _, seller_id, previous_cycle_id = _seed_assigned_lead(database)

    result = _service(database, seller_id).register_feedback(
        FeedbackCommand(lead_id, "Cliente pediu retorno", True, "feedback-cycle")
    )
    replay = _service(database, seller_id).register_feedback(
        FeedbackCommand(lead_id, "Cliente pediu retorno", True, "feedback-cycle")
    )

    previous = database["feedback_cycles"].find_one({"_id": previous_cycle_id})
    lead = database["leads"].find_one({"_id": lead_id})
    assert previous["closedAt"] == NOW
    assert result.cycle_id != str(previous_cycle_id)
    assert lead["feedbackDueAt"] == result.due_at
    assert len(database["feedbacks"].documents) == 1
    assert replay == result
    events = database["notification_outbox"].documents
    assert [event["eventType"] for event in events] == [
        "lead.feedback_recorded",
        "lead.feedback_due_soon",
    ]
    reminder = events[1]
    assert reminder["scheduledFor"] == result.reminder_at
    assert reminder["idempotencyKey"] == f"{lead_id}:{result.cycle_id}:feedback_due_soon"
    assert all(event["attempts"] == 0 for event in events)
    audit = database["audit_log"].documents[-1]
    assert audit["before"]["lead"]["feedbackDueAt"] == NOW - timedelta(hours=1)
    assert audit["after"]["lead"]["feedbackDueAt"] == result.due_at
    assert audit["before"]["cycle"]["closedAt"] is None
    assert audit["after"]["cycle"]["closedAt"] is None
    assert audit["correlationId"] == "feedback-cycle"


def test_ac21_five_distinct_attempts_enable_but_do_not_apply_manual_disqualification() -> None:
    """Breaks if duplicate dates count, six attempts pass, or the fifth auto-disqualifies."""
    database = FakeDatabase()
    lead_id, _, seller_id, _ = _seed_assigned_lead(database)
    service = _service(database, seller_id)
    weekdays = [date(2026, 8, 31) + timedelta(days=index) for index in range(5)]

    results = [
        service.register_attempt(
            AttemptCommand(lead_id, "Contato sem resposta", f"attempt-{index}", business_day)
        )
        for index, business_day in enumerate(weekdays)
    ]

    assert [result.sequence for result in results] == [1, 2, 3, 4, 5]
    assert results[-1].may_disqualify_no_answer is True
    attempt_audit = database["audit_log"].documents[0]
    assert attempt_audit["before"]["lead"]["qualificationStatus"] == "pending"
    assert attempt_audit["after"]["lead"]["qualificationStatus"] == "pending"
    assert database["leads"].find_one({"_id": lead_id})["qualificationStatus"] == "pending"
    with pytest.raises(OperationsStateError, match="same business date"):
        service.register_attempt(
            AttemptCommand(lead_id, "Nova tentativa", "attempt-duplicate", weekdays[-1])
        )
    with pytest.raises(OperationsStateError, match="limit"):
        service.register_attempt(
            AttemptCommand(lead_id, "Sexta tentativa", "attempt-six", date(2026, 8, 28))
        )


def test_ac21_no_answer_disqualification_is_manual_and_requires_five_attempts() -> None:
    """Breaks if no-answer can be selected early or is applied without an outcome command."""
    database = FakeDatabase()
    lead_id, _, seller_id, cycle_id = _seed_assigned_lead(database)
    service = _service(database, seller_id)
    command = OutcomeCommand(
        lead_id,
        "disqualified",
        "Não respondeu aos contatos",
        "manual-disqualification",
        "no_answer_after_5_attempts",
    )

    with pytest.raises(OperationsStateError, match="five"):
        service.register_outcome(command)
    for index in range(5):
        business_day = date(2026, 8, 31) + timedelta(days=index)
        service.register_attempt(
            AttemptCommand(lead_id, "Contato sem resposta", f"manual-attempt-{index}", business_day)
        )
    result = service.register_outcome(command)

    assert result.outcome == "disqualified"
    assert database["leads"].find_one({"_id": lead_id})["qualificationStatus"] == "disqualified"
    assert database["feedback_cycles"].find_one({"_id": cycle_id})["closedAt"] == NOW


def test_ac22_closed_without_conversion_stays_qualified_and_closes_sla() -> None:
    """Breaks if a refused proposal is counted as disqualified or keeps the SLA open."""
    database = FakeDatabase()
    lead_id, _, seller_id, cycle_id = _seed_assigned_lead(database)

    _service(database, seller_id).register_outcome(
        OutcomeCommand(
            lead_id,
            "qualified_closed_no_conversion",
            "Cliente recusou a proposta",
            "closed-no-conversion",
            None,
            True,
        )
    )

    lead = database["leads"].find_one({"_id": lead_id})
    assert lead["qualificationStatus"] == "qualified"
    assert lead["conversionStatus"] == "closed_no_conversion"
    assert database["feedback_cycles"].find_one({"_id": cycle_id})["closedAt"] == NOW


def test_ac23_outside_sp_remains_active_until_explicit_manual_outcome() -> None:
    """Breaks if an RJ source field automatically changes operational lead state."""
    database = FakeDatabase()
    lead_id, _, seller_id, _ = _seed_assigned_lead(database, state="RJ")
    assert database["leads"].find_one({"_id": lead_id})["qualificationStatus"] == "pending"

    _service(database, seller_id).register_outcome(
        OutcomeCommand(
            lead_id,
            "disqualified",
            "Empresa fora do estado atendido",
            "manual-outside-sp",
            "outside_sp",
        )
    )

    assert database["leads"].find_one({"_id": lead_id})["qualificationStatus"] == "disqualified"


def test_disqualification_reasons_must_match_the_lead_evidence() -> None:
    """Breaks if a seller can select an inapplicable canonical reason."""
    database = FakeDatabase()
    lead_id, company_id, seller_id, _ = _seed_assigned_lead(database, state="SP")
    database["companies"].update_one(
        {"_id": company_id}, {"$set": {"documentNormalized": "04252011000110"}}
    )
    service = _service(database, seller_id)

    with pytest.raises(OperationsStateError, match="outside SP"):
        service.register_outcome(
            OutcomeCommand(
                lead_id,
                "disqualified",
                "Motivo incompatÃ­vel com o cadastro",
                "invalid-outside-sp",
                "outside_sp",
            )
        )
    with pytest.raises(OperationsStateError, match="already has CNPJ"):
        service.register_outcome(
            OutcomeCommand(
                lead_id,
                "disqualified",
                "Motivo incompatÃ­vel com o cadastro",
                "invalid-no-cnpj",
                "no_cnpj",
            )
        )


def test_ac24_ac28_won_is_idempotent_marks_client_and_preserves_owner() -> None:
    """Breaks if replay creates two sales/events or temporary work changes company ownership."""
    database = FakeDatabase()
    lead_id, company_id, owner_id, cycle_id = _seed_assigned_lead(database)
    temporary_seller = ObjectId()
    database["leads"].update_one({"_id": lead_id}, {"$set": {"assigneeId": temporary_seller}})
    service = _service(database, temporary_seller)
    command = OutcomeCommand(lead_id, "won", "Venda confirmada", "won-idempotent")

    first = service.register_outcome(command)
    replay = service.register_outcome(command)

    assert replay == first
    assert len(database["sales"].documents) == 1
    assert len(database["qualification_events"].documents) == 1
    assert database["companies"].find_one({"_id": company_id})["ownerId"] == owner_id
    assert database["companies"].find_one({"_id": company_id})["clientSince"] == NOW
    assert database["sales"].documents[0]["creditedSellerId"] == temporary_seller
    assert database["feedback_cycles"].find_one({"_id": cycle_id})["closedAt"] == NOW
    outcome_audit = database["audit_log"].documents[-1]
    assert outcome_audit["before"]["company"]["clientSince"] is None
    assert outcome_audit["after"]["company"]["clientSince"] == NOW


def test_terminal_outcome_cancels_the_open_cycle_scheduled_reminder() -> None:
    """Breaks if a closed lead still sends its four-hour SLA reminder."""
    database = FakeDatabase()
    lead_id, _, seller_id, cycle_id = _seed_assigned_lead(database)
    database["notification_outbox"].insert_one(
        {
            "eventType": "lead.feedback_due_soon",
            "cycleId": cycle_id,
            "status": "scheduled",
        }
    )

    _service(database, seller_id).register_outcome(
        OutcomeCommand(lead_id, "won", "Venda confirmada", "won-cancels-reminder")
    )

    reminder = database["notification_outbox"].find_one({"cycleId": cycle_id})
    assert reminder["status"] == "cancelled"
    assert reminder["cancelledAt"] == NOW


def test_ac30_administrative_note_does_not_change_deadline_or_close_cycle() -> None:
    """Breaks if an administrator can regularize a seller through a note."""
    database = FakeDatabase()
    lead_id, _, _, cycle_id = _seed_assigned_lead(database)
    admin_id = ObjectId()
    before_due = database["leads"].find_one({"_id": lead_id})["feedbackDueAt"]

    result = _service(database, admin_id, role="admin").register_feedback(
        FeedbackCommand(
            lead_id,
            "Nota administrativa",
            False,
            "admin-note",
            administrative_note=True,
        )
    )

    assert result.status == "administrative_note"
    assert database["leads"].find_one({"_id": lead_id})["feedbackDueAt"] == before_due
    assert database["feedback_cycles"].find_one({"_id": cycle_id})["closedAt"] is None
    assert database["feedbacks"].documents[0]["kind"] == "administrative_note"
    audit = database["audit_log"].documents[-1]
    assert audit["before"]["lead"]["feedbackDueAt"] == before_due
    assert audit["after"]["lead"]["feedbackDueAt"] == before_due
    assert audit["before"]["cycle"]["closedAt"] is None
    assert audit["after"]["cycle"]["closedAt"] is None


def test_won_rolls_back_lead_company_cycle_and_event_when_sale_insert_fails() -> None:
    """Breaks if a partial won outcome can commit before its unique sale exists."""
    database = FakeDatabase()
    lead_id, company_id, seller_id, cycle_id = _seed_assigned_lead(database)
    database["sales"].fail_next_insert = True

    with pytest.raises(RuntimeError, match="injected"):
        _service(database, seller_id).register_outcome(
            OutcomeCommand(lead_id, "won", "Venda confirmada", "won-failure")
        )

    assert database["leads"].find_one({"_id": lead_id})["conversionStatus"] == "active"
    assert database["companies"].find_one({"_id": company_id})["clientSince"] is None
    assert database["feedback_cycles"].find_one({"_id": cycle_id})["closedAt"] is None
    assert database["qualification_events"].documents == []
    assert database["command_results"].documents == []


def test_public_feedback_reuses_the_server_timestamp_without_a_command_in_transaction() -> None:
    """Breaks if a transaction executes MongoDB `hello` or changes time between retries."""
    database = FakeDatabase()
    lead_id, _, seller_id, _ = _seed_assigned_lead(database)
    transaction_clock = SessionClock(NOW)
    process_clock = SessionClock(NOW)
    repository = MongoOperationsRepository(
        database,
        clock=transaction_clock,
        business_clock=BusinessClock(NoHolidays()),
    )
    service = OperationsService(
        repository,
        business_clock=BusinessClock(NoHolidays()),
        clock=process_clock,
    ).with_actor(seller_id, "seller")

    result = service.register_feedback(
        FeedbackCommand(lead_id, "Cliente pediu retorno", True, "database-clock")
    )

    assert result.due_at == datetime(2026, 9, 9, 11, 0, tzinfo=SAO_PAULO)
    assert process_clock.sessions == [None]
    assert transaction_clock.sessions == []


def test_operations_routes_bind_authenticated_actor_without_exposing_mongodb() -> None:
    """Breaks if HTTP handlers bypass the operational command seam or lose actor identity."""
    database = FakeDatabase()
    lead_id, _, seller_id, _ = _seed_assigned_lead(database)
    settings = Settings(
        MONGODB_URI="mongodb://localhost:27017/?replicaSet=rs0",
        MONGODB_DATABASE="gerec_leads",
        APP_SECRET="operations-route-secret",
    )
    app = create_app(settings=settings, database=database)
    app.state.operations_service = _service(database, seller_id)
    app.dependency_overrides[get_current_user] = lambda: CurrentUser(
        id=str(seller_id), email="seller@example.test", role="seller"
    )
    client = TestClient(app)

    feedback = client.post(
        f"/api/leads/{lead_id}/feedbacks",
        json={
            "comment": "Cliente pediu retorno",
            "contact_started": True,
            "idempotency_key": "route-feedback",
        },
    )
    attempt = client.post(
        f"/api/leads/{lead_id}/attempts",
        json={
            "comment": "Contato sem resposta",
            "business_date": "2026-09-04",
            "idempotency_key": "route-attempt",
        },
    )

    assert feedback.status_code == 200
    assert attempt.status_code == 200
    assert "mongodb" not in (feedback.text + attempt.text).casefold()
    assert all(item["actorId"] == seller_id for item in database["audit_log"].documents)


def test_treatment_route_accepts_only_the_current_seller_and_preserves_replay() -> None:
    """Breaks if the HTTP boundary bypasses the treatment command or maps permission as conflict."""
    database = FakeDatabase()
    lead_id, _, seller_id, _ = _seed_assigned_lead(database)
    settings = Settings(
        MONGODB_URI="mongodb://localhost:27017/?replicaSet=rs0",
        MONGODB_DATABASE="gerec_leads",
        APP_SECRET="operations-route-secret",
    )
    app = create_app(settings=settings, database=database)
    app.state.operations_service = _service(database, seller_id)
    client = TestClient(app)
    payload = {
        "comment": "Cliente pediu uma proposta comercial",
        "commercialStatus": "negotiation",
        "isDisqualified": False,
        "idempotencyKey": "route-treatment",
    }

    app.dependency_overrides[get_current_user] = lambda: CurrentUser(
        id=str(seller_id), email="seller@example.test", role="seller"
    )
    first = client.post(f"/api/leads/{lead_id}/treatments", json=payload)
    replay = client.post(f"/api/leads/{lead_id}/treatments", json=payload)

    app.dependency_overrides[get_current_user] = lambda: CurrentUser(
        id=str(ObjectId()), email="other@example.test", role="seller"
    )
    replay_by_other_seller = client.post(f"/api/leads/{lead_id}/treatments", json=payload)
    other_seller = client.post(
        f"/api/leads/{lead_id}/treatments",
        json={**payload, "idempotencyKey": "other-seller-treatment"},
    )
    app.dependency_overrides[get_current_user] = lambda: CurrentUser(
        id=str(seller_id), email="admin@example.test", role="admin"
    )
    admin = client.post(
        f"/api/leads/{lead_id}/treatments",
        json={**payload, "idempotencyKey": "admin-treatment"},
    )

    assert first.status_code == 201
    assert replay.status_code == 201
    assert replay.json() == first.json()
    assert first.json()["commercialStatus"] == "negotiation"
    assert replay_by_other_seller.status_code == 403
    assert replay_by_other_seller.json() == {"detail": "Forbidden"}
    assert "treatmentId" not in replay_by_other_seller.json()
    assert other_seller.status_code == 403
    assert other_seller.json() == {"detail": "Forbidden"}
    assert admin.status_code == 403
    assert admin.json() == {"detail": "Forbidden"}


def test_treatment_requires_the_current_seller_and_rejects_admin() -> None:
    """Breaks if a seller from another lead or an admin can create a treatment."""
    database = FakeDatabase()
    lead_id, _, seller_id, _ = _seed_assigned_lead(database)

    with pytest.raises(OperationsStateError, match="current lead assignee"):
        _service(database, ObjectId()).register_treatment(
            TreatmentCommand(lead_id, "Cliente pediu proposta", "negotiation", False, "other-seller")
        )
    with pytest.raises(ValueError, match="seller"):
        _service(database, seller_id, role="admin").register_treatment(
            TreatmentCommand(lead_id, "Cliente pediu proposta", "negotiation", False, "admin-treatment")
        )

    assert database["lead_treatments"].documents == []


def test_treatment_idempotency_key_cannot_replay_a_result_to_another_lead() -> None:
    """Breaks if a command receipt is returned for the right seller but wrong aggregate."""
    database = FakeDatabase()
    first_lead_id, _, seller_id, _ = _seed_assigned_lead(database)
    second_lead_id = ObjectId()
    second_cycle_id = ObjectId()
    database["leads"].insert_one(
        {
            "_id": second_lead_id,
            "assigneeId": seller_id,
            "assignmentStatus": "assigned",
            "qualificationStatus": "pending",
            "conversionStatus": "active",
            "feedbackDueAt": NOW - timedelta(hours=1),
            "feedbackCycleId": second_cycle_id,
            "archivedAt": None,
        }
    )
    database["feedback_cycles"].insert_one(
        {
            "_id": second_cycle_id,
            "leadId": second_lead_id,
            "startAt": NOW - timedelta(days=2),
            "reminderAt": NOW - timedelta(hours=5),
            "dueAt": NOW - timedelta(hours=1),
            "closedAt": None,
        }
    )
    command_key = "shared-treatment-key"

    _service(database, seller_id).register_treatment(
        TreatmentCommand(first_lead_id, "Cliente pediu proposta", "negotiation", False, command_key)
    )

    with pytest.raises(OperationsStateError, match="aggregate"):
        _service(database, seller_id).register_treatment(
            TreatmentCommand(second_lead_id, "Cliente pediu proposta", "negotiation", False, command_key)
        )


def test_treatment_materializes_projection_records_event_and_is_idempotent() -> None:
    """Breaks if replay duplicates the immutable event or comment projection."""
    database = FakeDatabase()
    lead_id, _, seller_id, previous_cycle_id = _seed_assigned_lead(database)
    command = TreatmentCommand(
        lead_id,
        "Cliente confirmou interesse na proposta",
        "negotiation",
        False,
        "treatment-idempotent",
    )

    first = _service(database, seller_id).register_treatment(command)
    replay = _service(database, seller_id).register_treatment(command)

    lead = database["leads"].find_one({"_id": lead_id})
    treatment = database["lead_treatments"].documents[0]
    assert replay == first
    assert first.comment_count == 1
    assert treatment["comment"] == "Cliente confirmou interesse na proposta"
    assert treatment["commercialStatus"] == "negotiation"
    assert treatment["isDisqualified"] is False
    assert lead["commercialStatus"] == "negotiation"
    assert lead["isDisqualified"] is False
    assert lead["commentCount"] == 1
    assert lead["lastCommentAt"] == NOW
    assert database["feedback_cycles"].find_one({"_id": previous_cycle_id})["closedAt"] == NOW
    assert len(database["lead_treatments"].documents) == 1
    assert len(database["audit_log"].documents) == 1
    assert [event["eventType"] for event in database["notification_outbox"].documents] == [
        "lead.treatment_recorded",
        "lead.feedback_due_soon",
    ]


def test_won_plus_disqualified_closes_sla_and_later_treatment_does_not_reopen_it() -> None:
    """Breaks if the marker overwrites won or permits a later SLA reactivation."""
    database = FakeDatabase()
    lead_id, _, seller_id, cycle_id = _seed_assigned_lead(database)

    result = _service(database, seller_id).register_treatment(
        TreatmentCommand(lead_id, "Venda confirmada e cadastro encerrado", "won", True, "won-marker")
    )
    later = _service(database, seller_id).register_treatment(
        TreatmentCommand(lead_id, "Cliente confirmou os dados finais", "won", False, "later-won")
    )

    lead = database["leads"].find_one({"_id": lead_id})
    assert result.commercial_status == "won"
    assert result.is_disqualified is True
    assert later.is_disqualified is True
    assert lead["commercialStatus"] == "won"
    assert lead["isDisqualified"] is True
    assert lead["feedbackDueAt"] is None
    assert lead["feedbackReminderAt"] is None
    assert database["feedback_cycles"].find_one({"_id": cycle_id})["closedAt"] == NOW
    assert len(database["feedback_cycles"].documents) == 1


def test_treatment_ignores_legacy_exclusive_statuses_when_materializing_projection() -> None:
    """Breaks if old terminal fields prevent the approved independent treatment projection."""
    database = FakeDatabase()
    lead_id, _, seller_id, _ = _seed_assigned_lead(database)
    database["leads"].update_one(
        {"_id": lead_id},
        {"$set": {"qualificationStatus": "disqualified", "conversionStatus": "won"}},
    )

    result = _service(database, seller_id).register_treatment(
        TreatmentCommand(lead_id, "Cliente pediu uma nova negociação", "negotiation", False, "legacy")
    )

    lead = database["leads"].find_one({"_id": lead_id})
    assert result.commercial_status == "negotiation"
    assert lead["commercialStatus"] == "negotiation"
    assert len(database["lead_treatments"].documents) == 1


def test_treatment_rolls_back_event_projection_audit_and_cycle_on_intermediate_failure() -> None:
    """Breaks if an audit failure can leave a treatment or closed SLA behind."""
    database = FakeDatabase()
    lead_id, _, seller_id, cycle_id = _seed_assigned_lead(database)
    database["audit_log"].fail_next_insert = True

    with pytest.raises(RuntimeError, match="injected"):
        _service(database, seller_id).register_treatment(
            TreatmentCommand(lead_id, "Cliente pediu retorno comercial", "negotiation", False, "rollback")
        )

    lead = database["leads"].find_one({"_id": lead_id})
    assert database["lead_treatments"].documents == []
    assert lead.get("commercialStatus") is None
    assert lead.get("commentCount") is None
    assert database["feedback_cycles"].find_one({"_id": cycle_id})["closedAt"] is None
    assert database["audit_log"].documents == []
    assert database["notification_outbox"].documents == []
    assert database["command_results"].documents == []
