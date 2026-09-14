"""Integration coverage for seller-only persistent new-lead notifications."""

from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
import os
from typing import Any

from bson import ObjectId
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pymongo import MongoClient
from pymongo.errors import PyMongoError, ServerSelectionTimeoutError

from gerec_api.auth.dependencies import get_current_user
from gerec_api.auth.sessions import CurrentUser
from gerec_api.domain.lead_notifications import LeadNotificationService
from gerec_api.infrastructure.mongo.lead_notification_repository import MongoLeadNotificationRepository
from gerec_api.routes.lead_notifications import router


NOW = datetime(2026, 9, 14, 15, tzinfo=UTC)


class Cursor:
    def __init__(self, values: list[dict[str, Any]]) -> None:
        self.values = values

    def sort(self, keys: list[tuple[str, int]]) -> "Cursor":
        for field, direction in reversed(keys):
            self.values.sort(key=lambda item: item[field], reverse=direction < 0)
        return self

    def __iter__(self):
        return iter(deepcopy(self.values))


class Collection:
    def __init__(self, documents: list[dict[str, Any]] | None = None) -> None:
        self.documents = documents or []

    def find_one(self, query: dict[str, Any], **_: Any) -> dict[str, Any] | None:
        return next((deepcopy(item) for item in self.documents if _matches(item, query)), None)

    def find(self, query: dict[str, Any], **_: Any) -> Cursor:
        return Cursor([item for item in self.documents if _matches(item, query)])

    def find_one_and_update(self, query: dict[str, Any], update: dict[str, Any], **_: Any) -> dict[str, Any] | None:
        for item in self.documents:
            if _matches(item, query):
                for key, value in update["$max"].items():
                    if item.get(key) is None or item[key] < value:
                        item[key] = value
                return deepcopy(item)
        return None


class Database(dict[str, Collection]):
    def __getitem__(self, name: str) -> Collection:
        return super().setdefault(name, Collection())


def _matches(document: dict[str, Any], query: dict[str, Any]) -> bool:
    for field, expected in query.items():
        actual = document.get(field)
        if isinstance(expected, dict):
            if "$in" in expected and actual not in expected["$in"]:
                return False
            if "$gt" in expected and not actual > expected["$gt"]:
                return False
            if "$lte" in expected and not actual <= expected["$lte"]:
                return False
        elif actual != expected:
            return False
    return True


def _seller(identifier: ObjectId | None = None) -> CurrentUser:
    return CurrentUser(str(identifier or ObjectId()), "seller@example.test", "seller")


def _service(database: Database) -> LeadNotificationService:
    return LeadNotificationService(
        MongoLeadNotificationRepository(database),
        signing_key="test-notification-secret",
        now=lambda: NOW,
    )


def test_seller_sees_only_current_leads_after_cursor_and_acknowledges() -> None:
    """Breaks if another seller's lead, old lead, or an unacknowledged item leaks into the window."""
    seller_id = ObjectId()
    other_seller_id = ObjectId()
    old_lead = ObjectId()
    new_lead = ObjectId()
    database = Database(
        users=Collection([{"_id": seller_id, "role": "seller", "newLeadsSeenAt": NOW - timedelta(minutes=5)}]),
        leads=Collection(
            [
                {"_id": old_lead, "assigneeId": seller_id, "assignedAt": NOW - timedelta(minutes=6), "contactName": "Antigo"},
                {"_id": new_lead, "assigneeId": seller_id, "assignedAt": NOW - timedelta(minutes=1), "contactName": "Novo"},
                {"_id": ObjectId(), "assigneeId": other_seller_id, "assignedAt": NOW - timedelta(minutes=1), "contactName": "Outro"},
            ]
        ),
    )
    service = _service(database)

    snapshot = service.for_seller(_seller(seller_id), "seller-session")

    assert [item.lead_id for item in snapshot.items] == [str(new_lead)]
    assert snapshot.items[0].contact_name == "Novo"
    assert service.acknowledge(_seller(seller_id), snapshot.watermark, snapshot.acknowledgement_token, "seller-session") == snapshot.watermark
    assert service.for_seller(_seller(seller_id), "seller-session").items == ()


def test_transfer_is_visible_to_new_owner_and_later_assignment_survives_ack() -> None:
    """Breaks if an acknowledgement can close over an assignment made after the returned watermark."""
    new_owner_id = ObjectId()
    old_owner_id = ObjectId()
    transferred_lead = ObjectId()
    later_lead = ObjectId()
    database = Database(
        users=Collection([{"_id": new_owner_id, "role": "seller", "newLeadsSeenAt": NOW - timedelta(minutes=5)}]),
        leads=Collection(
            [
                {"_id": transferred_lead, "assigneeId": new_owner_id, "assignedAt": NOW - timedelta(minutes=1), "contactName": "Transferido"},
                {"_id": ObjectId(), "assigneeId": old_owner_id, "assignedAt": NOW - timedelta(minutes=1), "contactName": "Antigo proprietário"},
            ]
        ),
    )
    service = _service(database)

    snapshot = service.for_seller(_seller(new_owner_id), "new-owner-session")
    database["leads"].documents.append(
        {"_id": later_lead, "assigneeId": new_owner_id, "assignedAt": snapshot.watermark + timedelta(seconds=1), "contactName": "Posterior"}
    )

    service.acknowledge(_seller(new_owner_id), snapshot.watermark, snapshot.acknowledgement_token, "new-owner-session")

    later_service = LeadNotificationService(
        MongoLeadNotificationRepository(database),
        signing_key="test-notification-secret",
        now=lambda: NOW + timedelta(seconds=2),
    )
    assert [item.lead_id for item in later_service.for_seller(_seller(new_owner_id), "new-owner-session").items] == [str(later_lead)]


def test_acknowledgement_uses_monotonic_max_and_rejects_future_watermarks() -> None:
    """Breaks if a stale tab can rewind the cursor or a client can acknowledge unseen future work."""
    seller_id = ObjectId()
    database = Database(
        users=Collection([{"_id": seller_id, "role": "seller", "newLeadsSeenAt": NOW - timedelta(minutes=5)}])
    )
    service = _service(database)

    recent_service = LeadNotificationService(
        MongoLeadNotificationRepository(database),
        signing_key="test-notification-secret",
        now=lambda: NOW - timedelta(minutes=1),
    )
    recent = recent_service.for_seller(_seller(seller_id), "seller-session")
    assert service.acknowledge(_seller(seller_id), recent.watermark, recent.acknowledgement_token, "seller-session") == NOW - timedelta(minutes=1)
    stale_service = LeadNotificationService(
        MongoLeadNotificationRepository(database),
        signing_key="test-notification-secret",
        now=lambda: NOW - timedelta(minutes=3),
    )
    stale = stale_service.for_seller(_seller(seller_id), "seller-session")
    assert service.acknowledge(_seller(seller_id), stale.watermark, stale.acknowledgement_token, "seller-session") == NOW - timedelta(minutes=1)

    future_service = LeadNotificationService(
        MongoLeadNotificationRepository(database),
        signing_key="test-notification-secret",
        now=lambda: NOW + timedelta(seconds=1),
    )
    future = future_service.for_seller(_seller(seller_id), "seller-session")
    try:
        service.acknowledge(_seller(seller_id), future.watermark, future.acknowledgement_token, "seller-session")
    except ValueError as error:
        assert str(error) == "notification watermark cannot be in the future"
    else:
        raise AssertionError("future watermark must be rejected")


def test_notification_routes_deny_admin_and_other_seller() -> None:
    """Breaks if a caller can select another seller or an administrator receives the seller-only window."""
    seller_id = ObjectId()
    other_seller_id = ObjectId()
    database = Database(
        users=Collection(
            [
                {"_id": seller_id, "role": "seller", "newLeadsSeenAt": NOW - timedelta(minutes=5)},
                {"_id": other_seller_id, "role": "seller", "newLeadsSeenAt": NOW - timedelta(minutes=5)},
            ]
        ),
        leads=Collection([{"_id": ObjectId(), "assigneeId": seller_id, "assignedAt": NOW, "contactName": "Privado"}]),
    )
    app = FastAPI()
    app.state.lead_notification_service = _service(database)
    app.include_router(router)
    client = TestClient(app)

    app.dependency_overrides[get_current_user] = lambda: CurrentUser(str(ObjectId()), "admin@example.test", "admin")
    assert client.get("/api/lead-notifications/new").status_code == 403
    assert client.post(
        "/api/lead-notifications/new/acknowledge",
        json={"watermark": NOW.isoformat(), "acknowledgementToken": "not-for-admin", "watermarkSequence": 0},
    ).status_code == 403

    app.dependency_overrides[get_current_user] = lambda: _seller(other_seller_id)
    response = client.get("/api/lead-notifications/new")
    assert response.status_code == 200
    assert response.json()["items"] == []
    assert response.json()["watermark"] == NOW.isoformat()
    assert isinstance(response.json()["acknowledgementToken"], str)


def test_acknowledgement_requires_a_watermark_receipt_from_the_same_session() -> None:
    """Breaks if a seller can forge an ACK or reuse a window receipt from another session."""
    seller_id = ObjectId()
    database = Database(
        users=Collection([{"_id": seller_id, "role": "seller", "newLeadsSeenAt": NOW - timedelta(minutes=5)}]),
        leads=Collection([{"_id": ObjectId(), "assigneeId": seller_id, "assignedAt": NOW, "contactName": "Privado"}]),
    )
    app = FastAPI()
    app.state.lead_notification_service = _service(database)
    app.include_router(router)
    app.dependency_overrides[get_current_user] = lambda: _seller(seller_id)
    client = TestClient(app)
    client.cookies.set("gerec_session", "seller-session-a")

    issued = client.get("/api/lead-notifications/new").json()
    forged = client.post(
        "/api/lead-notifications/new/acknowledge",
        json={"watermark": issued["watermark"], "acknowledgementToken": "forged", "watermarkSequence": issued["watermarkSequence"]},
    )

    assert forged.status_code == 422
    client.cookies.set("gerec_session", "seller-session-b")
    wrong_session = client.post(
        "/api/lead-notifications/new/acknowledge",
        json={"watermark": issued["watermark"], "acknowledgementToken": issued["acknowledgementToken"], "watermarkSequence": issued["watermarkSequence"]},
    )
    assert wrong_session.status_code == 422
    client.cookies.set("gerec_session", "seller-session-a")
    accepted = client.post(
        "/api/lead-notifications/new/acknowledge",
        json={"watermark": issued["watermark"], "acknowledgementToken": issued["acknowledgementToken"], "watermarkSequence": issued["watermarkSequence"]},
    )
    assert accepted.status_code == 200


def test_same_tick_assignment_after_snapshot_survives_the_prior_acknowledgement() -> None:
    """Breaks if an assignment committed after a snapshot shares its timestamp and is still acknowledged."""
    seller_id = ObjectId()
    first_lead = ObjectId()
    later_lead = ObjectId()
    database = Database(
        users=Collection(
            [
                {
                    "_id": seller_id,
                    "role": "seller",
                    "newLeadsSeenAt": NOW - timedelta(minutes=5),
                    "newLeadsSeenAssignmentSequence": 0,
                }
            ]
        ),
        queue_state=Collection([{"_id": "global", "assignmentSequence": 1}]),
        leads=Collection(
            [
                {
                    "_id": first_lead,
                    "assigneeId": seller_id,
                    "assignedAt": NOW,
                    "assignmentSequence": 1,
                    "contactName": "Primeiro",
                }
            ]
        ),
    )
    service = _service(database)

    snapshot = service.for_seller(_seller(seller_id), "seller-session")
    database["leads"].documents.append(
        {
            "_id": later_lead,
            "assigneeId": seller_id,
            "assignedAt": NOW,
            "assignmentSequence": 2,
            "contactName": "Posterior no mesmo tick",
        }
    )
    database["queue_state"].documents[0]["assignmentSequence"] = 2

    service.acknowledge(
        _seller(seller_id),
        snapshot.watermark,
        snapshot.acknowledgement_token,
        "seller-session",
        snapshot.watermark_sequence,
    )

    assert snapshot.watermark_sequence == 1
    assert [item.lead_id for item in service.for_seller(_seller(seller_id), "seller-session").items] == [str(later_lead)]


def test_replica_set_acknowledgements_keep_max_and_same_tick_assignment_pending() -> None:
    """Uses MongoDB when available to prove atomic $max and the persistent assignment sequence fence."""
    client = MongoClient(
        os.getenv("MONGODB_URI", "mongodb://localhost:27017/?replicaSet=rs0"),
        serverSelectionTimeoutMS=1_500,
    )
    try:
        hello = client.admin.command("hello")
    except (PyMongoError, ServerSelectionTimeoutError) as error:
        import pytest

        pytest.skip(f"MongoDB replica set indisponível externamente: {error}")
    if not hello.get("setName"):
        import pytest

        pytest.skip("MongoDB replica set indisponível externamente")

    database = client[f"gerec_notifications_test_{ObjectId()}"]
    seller_id = ObjectId()
    try:
        database["users"].insert_one(
            {
                "_id": seller_id,
                "role": "seller",
                "newLeadsSeenAt": NOW - timedelta(minutes=5),
                "newLeadsSeenAssignmentSequence": 0,
            }
        )
        database["queue_state"].insert_one({"_id": "global", "assignmentSequence": 1})
        database["leads"].insert_one(
            {"_id": ObjectId(), "assigneeId": seller_id, "assignedAt": NOW, "assignmentSequence": 1}
        )
        service = _service(database)
        first = service.for_seller(_seller(seller_id), "seller-session")
        later_lead_id = ObjectId()
        database["leads"].insert_one(
            {"_id": later_lead_id, "assigneeId": seller_id, "assignedAt": NOW, "assignmentSequence": 2}
        )
        database["queue_state"].update_one({"_id": "global"}, {"$set": {"assignmentSequence": 2}})
        service.acknowledge(
            _seller(seller_id),
            first.watermark,
            first.acknowledgement_token,
            "seller-session",
            first.watermark_sequence,
        )
        second = service.for_seller(_seller(seller_id), "seller-session")
        assert [item.lead_id for item in second.items] == [str(later_lead_id)]

        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [
                executor.submit(
                    service.acknowledge,
                    _seller(seller_id),
                    current.watermark,
                    current.acknowledgement_token,
                    "seller-session",
                    current.watermark_sequence,
                )
                for current in (second, first)
            ]
            [future.result() for future in futures]

        assert database["users"].find_one({"_id": seller_id})["newLeadsSeenAssignmentSequence"] == 2
    finally:
        client.drop_database(database.name)
        client.close()
