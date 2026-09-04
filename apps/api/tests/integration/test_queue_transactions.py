"""Transactional integration coverage for queue, ownership, credits and receipts."""

from __future__ import annotations

from copy import deepcopy
from datetime import UTC, date, datetime, timedelta
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
from gerec_api.domain.queue import QueueService
from gerec_api.infrastructure.mongo.queue_repository import QueueRepository, QueueStateError
from gerec_api.main import create_app


NOW = datetime(2026, 8, 27, 15, tzinfo=UTC)


class NoHolidays:
    def is_holiday(self, day: date) -> bool:
        return False


class FakeSession:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def with_transaction(self, callback):
        return callback(self)


class FakeClient:
    def start_session(self):
        return FakeSession()


class FakeCollection:
    def __init__(self) -> None:
        self.documents: list[dict[str, Any]] = []

    def find_one(self, query: dict[str, Any], **_: Any):
        return next((deepcopy(item) for item in self.documents if _matches(item, query)), None)

    def find(self, query: dict[str, Any], **_: Any):
        return [deepcopy(item) for item in self.documents if _matches(item, query)]

    def insert_one(self, document: dict[str, Any], **_: Any):
        stored = deepcopy(document)
        stored.setdefault("_id", ObjectId())
        self.documents.append(stored)
        return SimpleNamespace(inserted_id=stored["_id"])

    def update_one(self, query: dict[str, Any], update: dict[str, Any], *, upsert=False, **_: Any):
        for document in self.documents:
            if _matches(document, query):
                document.update(deepcopy(update.get("$set", {})))
                for key, delta in update.get("$inc", {}).items():
                    document[key] = document.get(key, 0) + delta
                return SimpleNamespace(matched_count=1, modified_count=1, upserted_id=None)
        if not upsert:
            return SimpleNamespace(matched_count=0, modified_count=0, upserted_id=None)
        stored = {
            key: deepcopy(value)
            for key, value in query.items()
            if not isinstance(value, dict)
        }
        stored.update(deepcopy(update.get("$setOnInsert", {})))
        stored.update(deepcopy(update.get("$set", {})))
        for key, delta in update.get("$inc", {}).items():
            stored[key] = stored.get(key, 0) + delta
        stored.setdefault("_id", ObjectId())
        self.documents.append(stored)
        return SimpleNamespace(matched_count=0, modified_count=0, upserted_id=stored["_id"])


class FakeDatabase:
    def __init__(self) -> None:
        self.client = FakeClient()
        self.collections: dict[str, FakeCollection] = {}

    def __getitem__(self, name: str):
        return self.collections.setdefault(name, FakeCollection())


def _matches(document: dict[str, Any], query: dict[str, Any]) -> bool:
    for key, expected in query.items():
        actual = document.get(key)
        if isinstance(expected, dict):
            if "$lt" in expected and not (actual is not None and actual < expected["$lt"]):
                return False
            if "$gte" in expected and not (actual is not None and actual >= expected["$gte"]):
                return False
            if "$in" in expected and actual not in expected["$in"]:
                return False
            if "$ne" in expected and actual == expected["$ne"]:
                return False
            continue
        if actual != expected:
            return False
    return True


def _seed_queue(database: FakeDatabase):
    sellers = [ObjectId() for _ in range(4)]
    for position, seller_id in enumerate(sellers, start=1):
        database["users"].insert_one({"_id": seller_id, "active": True})
        database["seller_queue"].insert_one(
            {"sellerId": seller_id, "position": position, "paused": False}
        )
        database["skip_balances"].insert_one({"sellerId": seller_id, "balance": 0})
    database["queue_state"].insert_one(
        {"_id": "global", "nextSellerId": sellers[0], "version": 0, "updatedAt": NOW}
    )
    return sellers


def _seed_lead(database: FakeDatabase, *, company_id=None, entered_offset=0):
    company_id = company_id or ObjectId()
    if database["companies"].find_one({"_id": company_id}) is None:
        database["companies"].insert_one({"_id": company_id, "ownerId": None})
    lead_id = ObjectId()
    database["leads"].insert_one(
        {
            "_id": lead_id,
            "companyId": company_id,
            "assignmentStatus": "ready",
            "assigneeId": None,
            "currentAssignmentId": None,
            "sourceEnteredAt": NOW + timedelta(minutes=entered_offset),
            "sourceLeadId": str(lead_id),
            "archivedAt": None,
        }
    )
    return lead_id, company_id


def _open_overdue_cycle(database: FakeDatabase, lead_id: ObjectId) -> ObjectId:
    cycle_id = ObjectId()
    database["feedback_cycles"].insert_one(
        {
            "_id": cycle_id,
            "leadId": lead_id,
            "dueAt": NOW - timedelta(seconds=1),
            "closedAt": None,
        }
    )
    return cycle_id


def _availability(snapshot, seller_id: ObjectId):
    return next(entry.availability for entry in snapshot.entries if entry.seller_id == seller_id)


def _service(database: FakeDatabase, *, actor_id: Any = "system") -> QueueService:
    return QueueService(
        QueueRepository(
            database,
            now=lambda: NOW,
        ),
        actor_id=actor_id,
    )


def test_ac01_normal_rotation_is_atomic_and_first_assignment_defines_owner() -> None:
    """Breaks if cursor, lead, assignment, owner, audit or outbox diverge."""
    database = FakeDatabase()
    sellers = _seed_queue(database)
    leads = [_seed_lead(database, entered_offset=index)[0] for index in range(4)]
    service = _service(database)

    results = [service.distribute_normal(lead, f"normal-{index}") for index, lead in enumerate(leads)]

    assert [result.seller_id for result in results] == [str(seller) for seller in sellers]
    assert database["queue_state"].documents[0]["nextSellerId"] == sellers[0]
    assert database["queue_state"].documents[0]["version"] == 4
    assert len(database["assignments"].documents) == 4
    assert database["feedback_cycles"].documents == []
    assert all(
        "feedbackDueAt" not in database["leads"].find_one({"_id": lead_id})
        and "feedbackReminderAt" not in database["leads"].find_one({"_id": lead_id})
        for lead_id in leads
    )
    reminders = [
        event
        for event in database["notification_outbox"].documents
        if event["eventType"] == "lead.feedback_due_soon"
    ]
    assert reminders == []
    assert len(database["audit_log"].documents) == 4
    assert len(database["notification_outbox"].documents) == 4
    for lead_id in leads:
        lead = database["leads"].find_one({"_id": lead_id})
        company = database["companies"].find_one({"_id": lead["companyId"]})
        assert lead["assignmentStatus"] == "assigned"
        assert company["ownerId"] == lead["assigneeId"]


def test_reconcile_pending_assigns_parked_leads_in_source_fifo_order() -> None:
    """Breaks if a later sync leaves no-eligible-seller leads stranded or reorders them."""
    database = FakeDatabase()
    sellers = _seed_queue(database)
    newer_lead, _ = _seed_lead(database, entered_offset=2)
    older_lead, _ = _seed_lead(database, entered_offset=1)
    for lead_id in (newer_lead, older_lead):
        database["leads"].update_one(
            {"_id": lead_id},
            {"$set": {"assignmentStatus": "parked", "parkReason": "no_eligible_seller"}},
        )

    results = _service(database).reconcile_pending("sync:retry-pending")

    assert [result.lead_id for result in results] == [str(older_lead), str(newer_lead)]
    assert [result.seller_id for result in results] == [str(sellers[0]), str(sellers[1])]
    assert all(
        database["leads"].find_one({"_id": lead_id})["assignmentStatus"] == "assigned"
        for lead_id in (older_lead, newer_lead)
    )


def test_reconcile_pending_does_not_block_normal_fifo_for_unavailable_recurring_owner() -> None:
    """Breaks if a parked recurring lead prevents the next normal lead from being assigned."""
    database = FakeDatabase()
    owner, next_seller, *_ = _seed_queue(database)
    recurring_lead, recurring_company = _seed_lead(database, entered_offset=1)
    normal_lead, _ = _seed_lead(database, entered_offset=2)
    database["companies"].update_one({"_id": recurring_company}, {"$set": {"ownerId": owner}})
    database["seller_queue"].update_one({"sellerId": owner}, {"$set": {"paused": True}})

    results = _service(database).reconcile_pending("sync:retry-pending")

    assert [(result.status, result.assignment_type) for result in results] == [
        ("parked", "recurring"),
        ("assigned", "normal"),
    ]
    assert database["leads"].find_one({"_id": recurring_lead})["parkReason"] == "owner_unavailable"
    assert database["leads"].find_one({"_id": normal_lead})["assigneeId"] == next_seller


def test_reconcile_pending_does_not_repeat_a_park_event_without_availability_change() -> None:
    """Breaks if each sync replay creates another parked audit event for the same lead."""
    database = FakeDatabase()
    _seed_queue(database)
    lead_id, _ = _seed_lead(database)
    for seller in database["seller_queue"].documents:
        seller["paused"] = True

    _service(database).reconcile_pending("sync:first")
    first_events = len(database["audit_log"].documents)
    first_version = database["queue_state"].documents[0]["version"]
    _service(database).reconcile_pending("sync:second")

    assert database["leads"].find_one({"_id": lead_id})["assignmentStatus"] == "parked"
    assert len(database["audit_log"].documents) == first_events
    assert database["queue_state"].documents[0]["version"] == first_version


def test_overdue_seller_remains_active_for_normal_distribution() -> None:
    """Historical overdue cycles do not remove a seller from FIFO eligibility."""
    database = FakeDatabase()
    renato, sandra, _, _ = _seed_queue(database)
    overdue_lead, _ = _seed_lead(database, entered_offset=-1)
    database["leads"].update_one(
        {"_id": overdue_lead},
        {
            "$set": {
                "assignmentStatus": "assigned",
                "assigneeId": renato,
                "feedbackDueAt": NOW - timedelta(seconds=1),
            }
        },
    )
    _open_overdue_cycle(database, overdue_lead)
    incoming, _ = _seed_lead(database)

    result = _service(database).distribute_normal(incoming, "overdue-renato")

    assert result.seller_id == str(renato)
    assert database["queue_state"].documents[0]["nextSellerId"] == sandra


def test_snapshot_ignores_overdue_cycle_and_orders_from_next_active_seller() -> None:
    """Open SLA cycles are historical and do not create blocked availability."""
    database = FakeDatabase()
    renato, sandra, jessica, nelma = _seed_queue(database)
    overdue_lead, _ = _seed_lead(database, entered_offset=-1)
    database["leads"].update_one(
        {"_id": overdue_lead},
        {
            "$set": {
                "assignmentStatus": "assigned",
                "assigneeId": sandra,
                "feedbackDueAt": NOW - timedelta(seconds=1),
            }
        },
    )
    _open_overdue_cycle(database, overdue_lead)
    database["seller_queue"].update_one({"sellerId": renato}, {"$set": {"paused": True}})

    snapshot = QueueRepository(database, now=lambda: NOW).snapshot()

    assert snapshot.cursor_seller_id == renato
    assert [entry.seller_id for entry in snapshot.entries] == [sandra, jessica, nelma, renato]
    assert [entry.availability.status for entry in snapshot.entries] == [
        "active",
        "active",
        "active",
        "paused",
    ]


def test_overdue_and_disqualified_cycles_never_change_manual_availability() -> None:
    """SLA history cannot change availability; manual pause remains authoritative."""
    database = FakeDatabase()
    renato, *_ = _seed_queue(database)
    overdue_lead, _ = _seed_lead(database, entered_offset=-1)
    database["leads"].update_one(
        {"_id": overdue_lead},
        {
            "$set": {
                "assignmentStatus": "assigned",
                "assigneeId": renato,
                "feedbackDueAt": NOW - timedelta(seconds=1),
                "isDisqualified": True,
            }
        },
    )

    disqualified_open_cycle = _open_overdue_cycle(database, overdue_lead)
    stale_only = QueueRepository(database, now=lambda: NOW).snapshot()
    assert _availability(stale_only, renato).status == "active"

    active_overdue_lead, _ = _seed_lead(database)
    database["leads"].update_one(
        {"_id": active_overdue_lead},
        {"$set": {"assignmentStatus": "assigned", "assigneeId": renato}},
    )
    _open_overdue_cycle(database, active_overdue_lead)
    still_active = QueueRepository(database, now=lambda: NOW).snapshot()
    assert _availability(still_active, renato).status == "active"

    database["feedback_cycles"].update_one(
        {"_id": disqualified_open_cycle}, {"$set": {"closedAt": NOW}}
    )
    regularized = QueueRepository(database, now=lambda: NOW).snapshot()
    assert _availability(regularized, renato).status == "active"

    database["seller_queue"].update_one({"sellerId": renato}, {"$set": {"paused": True}})
    paused_after_regularization = QueueRepository(database, now=lambda: NOW).snapshot()
    assert _availability(paused_after_regularization, renato).status == "paused"


def test_snapshot_and_distribution_follow_skip_credit_selection() -> None:
    """Breaks if the displayed next seller differs from the normal rotation after a credit."""
    database = FakeDatabase()
    renato, sandra, *_ = _seed_queue(database)
    database["skip_balances"].update_one({"sellerId": renato}, {"$set": {"balance": 1}})
    lead_id, _ = _seed_lead(database)
    service = _service(database)

    snapshot = QueueRepository(database, now=lambda: NOW).snapshot()
    assignment = service.distribute_normal(lead_id, "skip-credit-snapshot")

    assert snapshot.entries[0].seller_id == sandra
    assert assignment.seller_id == str(sandra)


def test_pause_preserves_existing_lead_and_consumes_its_natural_turn() -> None:
    """Breaks if pausing transfers a lead or leaves the paused seller eligible for rotation."""
    database = FakeDatabase()
    renato, sandra, *_ = _seed_queue(database)
    assigned_lead, _ = _seed_lead(database)
    next_lead, _ = _seed_lead(database, entered_offset=1)
    service = _service(database)

    assignment = service.distribute_normal(assigned_lead, "assign-renato")
    database["seller_queue"].update_one({"sellerId": renato}, {"$set": {"paused": True}})
    next_assignment = service.distribute_normal(next_lead, "skip-paused-renato")

    assert assignment.seller_id == str(renato)
    assert database["leads"].find_one({"_id": assigned_lead})["assigneeId"] == renato
    assert next_assignment.seller_id == str(sandra)


def test_overdue_sellers_do_not_park_normal_fifo_leads() -> None:
    """Normal leads continue through FIFO even when every seller has overdue history."""
    database = FakeDatabase()
    sellers = _seed_queue(database)
    oldest, _ = _seed_lead(database, entered_offset=0)
    newest, _ = _seed_lead(database, entered_offset=1)
    for seller_id in sellers:
        blocked, _ = _seed_lead(database, entered_offset=-10)
        database["leads"].update_one(
            {"_id": blocked},
            {
                "$set": {
                    "assignmentStatus": "assigned",
                    "assigneeId": seller_id,
                    "feedbackDueAt": NOW - timedelta(minutes=1),
                }
            },
        )
        _open_overdue_cycle(database, blocked)
    service = _service(database)

    first = service.distribute_normal(oldest, "fifo-oldest")
    second = service.distribute_normal(newest, "fifo-newest")

    assert first.seller_id == str(sellers[0])
    assert second.seller_id == str(sellers[1])
    assignment_leads = [item["leadId"] for item in database["assignments"].documents]
    assert assignment_leads[-2:] == [oldest, newest]


def test_ac07_ac08_recurring_preserves_cursor_and_adds_credit_consumed_later() -> None:
    """Breaks if recurrence moves the cursor, changes owner, or misses compensation."""
    database = FakeDatabase()
    renato, sandra, _, _ = _seed_queue(database)
    lead_id, company_id = _seed_lead(database)
    database["companies"].update_one({"_id": company_id}, {"$set": {"ownerId": renato}})
    service = _service(database)

    recurring = service.assign_recurring(lead_id, "recurring-1")
    next_lead, _ = _seed_lead(database, entered_offset=1)
    normal = service.distribute_normal(next_lead, "normal-after-recurring")

    assert recurring.seller_id == str(renato)
    assert normal.seller_id == str(sandra)
    assert database["queue_state"].documents[0]["version"] == 1
    assert database["skip_balances"].find_one({"sellerId": renato})["balance"] == 0
    assert database["companies"].find_one({"_id": company_id})["ownerId"] == renato


def test_paused_owner_waits_and_temporary_assignment_preserves_owner() -> None:
    """Only manual pause parks recurrence; temporary work preserves ownership."""
    database = FakeDatabase()
    renato, sandra, _, _ = _seed_queue(database)
    recurring, company_id = _seed_lead(database)
    database["companies"].update_one({"_id": company_id}, {"$set": {"ownerId": renato}})
    overdue, _ = _seed_lead(database, entered_offset=-5)
    database["leads"].update_one(
        {"_id": overdue},
        {
            "$set": {
                "assignmentStatus": "assigned",
                "assigneeId": renato,
                "feedbackDueAt": NOW - timedelta(seconds=1),
            }
        },
    )
    _open_overdue_cycle(database, overdue)
    database["seller_queue"].update_one({"sellerId": renato}, {"$set": {"paused": True}})
    service = _service(database)

    waiting = service.assign_recurring(recurring, "paused-owner")
    temporary = service.assign_temporarily(
        recurring,
        sandra,
        "Cobertura administrativa durante o atraso",
        "temporary-sandra",
    )

    assert waiting.status == "parked"
    assert temporary.assignment_type == "temporary"
    assert temporary.seller_id == str(sandra)
    assert database["leads"].find_one({"_id": recurring})["assigneeId"] == sandra
    assert database["companies"].find_one({"_id": company_id})["ownerId"] == renato
    assert database["skip_balances"].find_one({"sellerId": sandra})["balance"] == 1


def test_temporary_assignment_rejects_normal_or_ownerless_leads() -> None:
    """Breaks if the admin override can turn a normal lead into recurrence or claim ownership."""
    database = FakeDatabase()
    renato, sandra, _, _ = _seed_queue(database)
    normal, company_id = _seed_lead(database)
    service = _service(database)

    with pytest.raises(QueueStateError, match="recurring parked"):
        service.assign_temporarily(normal, sandra, "Tentativa inválida", "temp-normal")

    database["companies"].update_one({"_id": company_id}, {"$set": {"ownerId": renato}})
    database["leads"].update_one(
        {"_id": normal},
        {"$set": {"assignmentStatus": "parked", "parkReason": "no_eligible_seller"}},
    )
    with pytest.raises(QueueStateError, match="recurring parked"):
        service.assign_temporarily(normal, sandra, "Lead normal parado", "temp-normal-parked")

    database["companies"].update_one({"_id": company_id}, {"$set": {"ownerId": None}})
    database["leads"].update_one(
        {"_id": normal},
        {"$set": {"assignmentStatus": "parked", "parkReason": "owner_unavailable"}},
    )
    with pytest.raises(QueueStateError, match="owner"):
        service.assign_temporarily(normal, sandra, "Sem proprietário", "temp-ownerless")

    assert database["companies"].find_one({"_id": company_id})["ownerId"] is None
    assert database["assignments"].documents == []


def test_ac08_three_recurring_credits_are_audited_and_consumed_without_negative_balance() -> None:
    """Breaks if any of three credits is lost, unaudited, or consumed below zero."""
    database = FakeDatabase()
    renato, *_ = _seed_queue(database)
    actor_id = ObjectId()
    company_id = ObjectId()
    database["companies"].insert_one({"_id": company_id, "ownerId": renato})
    service = _service(database, actor_id=actor_id)
    for index in range(3):
        recurring, _ = _seed_lead(database, company_id=company_id, entered_offset=index)
        service.assign_recurring(recurring, f"recurring-credit-{index}")

    assert database["skip_balances"].find_one({"sellerId": renato})["balance"] == 3

    normal_results = []
    for index in range(7):
        normal, _ = _seed_lead(database, entered_offset=10 + index)
        normal_results.append(service.distribute_normal(normal, f"consume-credit-{index}"))

    assert all(result.seller_id != str(renato) for result in normal_results)
    assert database["skip_balances"].find_one({"sellerId": renato})["balance"] == 0
    credit_audits = [
        item for item in database["audit_log"].documents if item["action"].startswith("seller.skip_")
    ]
    assert [item["action"] for item in credit_audits].count("seller.skip_credited") == 3
    assert [item["action"] for item in credit_audits].count("seller.skip_consumed") == 3
    assert all(item["actorId"] == actor_id for item in credit_audits)
    credit_outbox = [
        item
        for item in database["notification_outbox"].documents
        if item["eventType"].startswith("seller.skip_")
    ]
    assert len(credit_outbox) == 6
    assert all(item["actorId"] == actor_id for item in credit_outbox)


def test_permanent_transfer_changes_future_owner_without_rewriting_assignments() -> None:
    """Breaks if transfer mutates historical assignment or omits the before/after audit."""
    database = FakeDatabase()
    renato, sandra, _, _ = _seed_queue(database)
    lead_id, company_id = _seed_lead(database)
    database["companies"].update_one({"_id": company_id}, {"$set": {"ownerId": renato}})
    database["assignments"].insert_one(
        {"leadId": lead_id, "sellerId": renato, "type": "normal", "current": False}
    )

    result = _service(database).transfer_owner(
        company_id,
        sandra,
        "Redistribuição permanente aprovada",
        "transfer-owner",
    )

    assert result.previous_owner_id == str(renato)
    assert result.owner_id == str(sandra)
    assert database["companies"].find_one({"_id": company_id})["ownerId"] == sandra
    assert database["assignments"].documents[0]["sellerId"] == renato
    audit = database["audit_log"].documents[-1]
    assert audit["before"] == {"ownerId": renato}
    assert audit["after"] == {"ownerId": sandra}


def test_lead_transfer_changes_only_current_assignment_and_preserves_queue_cursor() -> None:
    database = FakeDatabase()
    renato, sandra, *_ = _seed_queue(database)
    lead_id, _ = _seed_lead(database)
    service = _service(database)
    service.distribute_normal(lead_id, "lead-transfer-initial")
    cursor_before = database["queue_state"].find_one({"_id": "global"})["nextSellerId"]

    result = service.transfer_lead(lead_id, sandra, "Cobertura administrativa", "lead-transfer")

    lead = database["leads"].find_one({"_id": lead_id})
    assert result.seller_id == str(sandra)
    assert lead["assigneeId"] == sandra
    assert database["queue_state"].find_one({"_id": "global"})["nextSellerId"] == cursor_before
    assert any(item["action"] == "lead.owner_transferred" for item in database["audit_log"].documents)
    assert database["assignments"].documents[0]["sellerId"] == renato
    assert database["assignments"].documents[0]["current"] is False


def test_command_replay_returns_original_result_without_duplicate_side_effects() -> None:
    """Breaks if an idempotent retry creates another assignment/audit/outbox event."""
    database = FakeDatabase()
    _seed_queue(database)
    lead_id, _ = _seed_lead(database)
    service = _service(database)

    first = service.distribute_normal(lead_id, "same-command")
    replay = service.distribute_normal(lead_id, "same-command")

    assert replay == first
    assert len(database["assignments"].documents) == 1
    assert len(database["audit_log"].documents) == 1
    assert len(database["notification_outbox"].documents) == 1


def test_internal_queue_route_calls_the_transactional_service_without_exposing_mongodb() -> None:
    """Breaks if the HTTP boundary bypasses queue commands or accepts unauthenticated calls."""
    database = FakeDatabase()
    first_seller, *_ = _seed_queue(database)
    lead_id, _ = _seed_lead(database)
    settings = Settings(
        MONGODB_URI="mongodb://localhost:27017/?replicaSet=rs0",
        MONGODB_DATABASE="gerec_leads",
        APP_SECRET="queue-route-secret",
    )
    app = create_app(settings=settings, database=database)
    app.state.queue_service = _service(database)
    client = TestClient(app)

    unauthorized = client.post(
        f"/api/internal/queue/leads/{lead_id}/distribute-normal",
        json={"command_id": "route-command"},
    )
    response = client.post(
        f"/api/internal/queue/leads/{lead_id}/distribute-normal",
        headers={"X-Internal-Key": "queue-route-secret"},
        json={"command_id": "route-command"},
    )

    assert unauthorized.status_code == 422
    assert response.status_code == 200
    assert response.json()["sellerId"] == str(first_seller)
    assert "mongodb" not in response.text.casefold()
    assert database["audit_log"].documents[-1]["actorId"] == "system"


def test_admin_routes_propagate_actor_and_require_transfer_confirmation() -> None:
    """Breaks if admin identity is lost or an accidental transfer can be submitted unconfirmed."""
    database = FakeDatabase()
    renato, sandra, _, _ = _seed_queue(database)
    lead_id, company_id = _seed_lead(database)
    database["companies"].update_one({"_id": company_id}, {"$set": {"ownerId": renato}})
    database["leads"].update_one(
        {"_id": lead_id},
        {"$set": {"assignmentStatus": "parked", "parkReason": "owner_unavailable"}},
    )
    admin_id = ObjectId()
    settings = Settings(
        MONGODB_URI="mongodb://localhost:27017/?replicaSet=rs0",
        MONGODB_DATABASE="gerec_leads",
        APP_SECRET="queue-route-secret",
    )
    app = create_app(settings=settings, database=database)
    app.state.queue_service = _service(database)
    app.dependency_overrides[get_current_user] = lambda: CurrentUser(
        id=str(admin_id), email="admin@example.test", role="admin"
    )
    client = TestClient(app)

    temporary = client.post(
        f"/api/admin/leads/{lead_id}/temporary-assignment",
        json={
            "seller_id": str(sandra),
            "reason": "Cobertura administrativa",
            "command_id": "route-temporary",
        },
    )
    unconfirmed = client.post(
        f"/api/admin/companies/{company_id}/transfer-owner",
        json={
            "seller_id": str(sandra),
            "reason": "Transferência aprovada",
            "command_id": "route-transfer-no",
            "confirmed": False,
        },
    )
    lead_unconfirmed = client.post(
        f"/api/admin/leads/{lead_id}/transfer-owner",
        json={
            "seller_id": str(sandra),
            "reason": "Transferência do lead",
            "command_id": "route-lead-transfer-no",
            "confirmed": False,
        },
    )
    confirmed = client.post(
        f"/api/admin/companies/{company_id}/transfer-owner",
        json={
            "seller_id": str(sandra),
            "reason": "Transferência aprovada",
            "command_id": "route-transfer-yes",
            "confirmed": True,
        },
    )

    assert temporary.status_code == 200
    assert unconfirmed.status_code == 422
    assert lead_unconfirmed.status_code == 422
    assert confirmed.status_code == 200
    assert all(item["actorId"] == admin_id for item in database["audit_log"].documents)


def test_admin_lead_transfer_route_returns_assignment_result_when_confirmed() -> None:
    """The production admin action must receive the assignment result, not crash at HTTP serialization."""
    database = FakeDatabase()
    renato, sandra, _, _ = _seed_queue(database)
    lead_id, _ = _seed_lead(database)
    service = _service(database)
    service.distribute_normal(lead_id, "route-lead-initial")
    admin_id = ObjectId()
    settings = Settings(
        MONGODB_URI="mongodb://localhost:27017/?replicaSet=rs0",
        MONGODB_DATABASE="gerec_leads",
        APP_SECRET="queue-route-secret",
    )
    app = create_app(settings=settings, database=database)
    app.state.queue_service = service
    app.dependency_overrides[get_current_user] = lambda: CurrentUser(
        id=str(admin_id), email="admin@example.test", role="admin"
    )
    client = TestClient(app)

    response = client.post(
        f"/api/admin/leads/{lead_id}/transfer-owner",
        json={
            "seller_id": str(sandra),
            "reason": "Cobertura administrativa",
            "command_id": "route-lead-transfer-yes",
            "confirmed": True,
        },
    )

    assert response.status_code == 200
    assert response.json()["leadId"] == str(lead_id)
    assert response.json()["sellerId"] == str(sandra)
