"""Transactional integration coverage for queue, ownership, credits and receipts."""

from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from typing import Any

import pytest
from bson import ObjectId
from fastapi.testclient import TestClient

from gerec_api.config import Settings
from gerec_api.domain.queue import QueueService
from gerec_api.infrastructure.mongo.queue_repository import QueueRepository, QueueStateError
from gerec_api.main import create_app


NOW = datetime(2026, 8, 27, 15, tzinfo=UTC)


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


def _service(database: FakeDatabase) -> QueueService:
    return QueueService(QueueRepository(database, now=lambda: NOW))


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
    assert len(database["audit_log"].documents) == 4
    assert len(database["notification_outbox"].documents) == 4
    for lead_id in leads:
        lead = database["leads"].find_one({"_id": lead_id})
        company = database["companies"].find_one({"_id": lead["companyId"]})
        assert lead["assignmentStatus"] == "assigned"
        assert company["ownerId"] == lead["assigneeId"]


def test_ac02_ac04_blocked_seller_loses_turn_and_one_overdue_lead_is_enough() -> None:
    """Breaks if overdue eligibility is cached or evaluated incompletely."""
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
    incoming, _ = _seed_lead(database)

    result = _service(database).distribute_normal(incoming, "blocked-renato")

    assert result.seller_id == str(sandra)
    assert database["queue_state"].documents[0]["nextSellerId"] not in (renato, sandra)


def test_ac05_ac06_all_blocked_parks_and_fifo_cannot_be_bypassed_after_release() -> None:
    """Breaks if parked leads are dropped or a newer normal lead jumps the FIFO."""
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
    service = _service(database)

    parked = service.distribute_normal(oldest, "park-oldest")
    with pytest.raises(QueueStateError, match="FIFO"):
        service.distribute_normal(newest, "jump-fifo")

    assert parked.status == "parked"
    assert parked.seller_id is None
    assert database["leads"].find_one({"_id": oldest})["parkReason"] == "no_eligible_seller"


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


def test_ac09_ac10_ac11_blocked_owner_waits_and_temporary_assignment_preserves_owner() -> None:
    """Breaks if recurrence leaks to the rotation or temporary work transfers ownership."""
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
    service = _service(database)

    waiting = service.assign_recurring(recurring, "blocked-owner")
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
