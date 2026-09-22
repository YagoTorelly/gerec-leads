"""Integration coverage for manual lead creation and its independent queue."""

from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime, timedelta
from importlib import import_module
from types import SimpleNamespace
from typing import Any
from uuid import UUID

from bson import ObjectId

from gerec_api.domain.manual_leads import ManualLeadCommand, ManualLeadService
from gerec_api.infrastructure.mongo.lead_repository import LeadRepository
from gerec_api.infrastructure.mongo.indexes import INDEXES
from gerec_api.infrastructure.mongo.migrations.runner import MIGRATIONS
from gerec_api.domain.queue import QueueService
from gerec_api.infrastructure.mongo.queue_repository import QueueRepository


NOW = datetime(2026, 9, 22, 15, tzinfo=UTC)


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
        stored = {key: deepcopy(value) for key, value in query.items() if not isinstance(value, dict)}
        stored.update(deepcopy(update.get("$setOnInsert", {})))
        stored.update(deepcopy(update.get("$set", {})))
        stored.setdefault("_id", ObjectId())
        self.documents.append(stored)
        return SimpleNamespace(matched_count=0, modified_count=0, upserted_id=stored["_id"])

    def find_one_and_update(self, query: dict[str, Any], update: dict[str, Any], **_: Any):
        for document in self.documents:
            if _matches(document, query):
                document.update(deepcopy(update.get("$set", {})))
                for key, delta in update.get("$inc", {}).items():
                    document[key] = document.get(key, 0) + delta
                return deepcopy(document)
        return None


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
            if "$exists" in expected and (key in document) is not expected["$exists"]:
                return False
            if "$ne" in expected and actual == expected["$ne"]:
                return False
            if "$in" in expected and actual not in expected["$in"]:
                return False
            continue
        if actual != expected:
            return False
    return True


def _seed_queue(database: FakeDatabase) -> list[ObjectId]:
    sellers = [ObjectId() for _ in range(4)]
    for position, seller_id in enumerate(sellers, start=1):
        database["users"].insert_one({"_id": seller_id, "active": True})
        database["seller_queue"].insert_one(
            {"sellerId": seller_id, "position": position, "paused": False}
        )
        database["skip_balances"].insert_one({"sellerId": seller_id, "balance": 0})
    database["queue_state"].insert_one(
        {
            "_id": "global",
            "nextSellerId": sellers[2],
            "version": 7,
            "assignmentSequence": 10,
            "updatedAt": NOW,
        }
    )
    database["queue_state"].insert_one(
        {"_id": "manual", "nextSellerId": sellers[0], "version": 0, "updatedAt": NOW}
    )
    return sellers


def _service(database: FakeDatabase) -> ManualLeadService:
    return ManualLeadService(LeadRepository(database))


def _command(key: str, **overrides: Any) -> ManualLeadCommand:
    values = {
        "name": "Contato manual",
        "email": "Contato@Example.com",
        "phone": "+55 11 99999-1234",
        "campaign": None,
        "source": None,
        "idempotency_key": key,
    }
    values.update(overrides)
    return ManualLeadCommand(**values)


def test_manual_creation_sets_undefined_status_and_a_backend_uuid4_identifier() -> None:
    """Breaks if a manual lead reuses source identity or starts with a treated status."""
    database = FakeDatabase()
    sellers = _seed_queue(database)

    result = _service(database).create_manual_lead("admin-yago", _command("manual-1"), NOW)

    lead = database["leads"].find_one({"_id": ObjectId(result.lead_id)})
    assert result.assignee_id == str(sellers[0])
    assert result.commercial_status == "undefined"
    assert result.source == "manual"
    assert result.manual_queue_lead_id.startswith("MAN-")
    assert UUID(result.manual_queue_lead_id.removeprefix("MAN-")).version == 4
    assert lead["commercialStatus"] == "undefined"
    assert lead["source"] == "manual"
    assert lead["manualQueueLeadId"] == result.manual_queue_lead_id
    assert "sourceLeadId" not in lead


def test_manual_queue_skips_paused_seller_without_changing_automatic_state_or_credits() -> None:
    """Breaks if manual rotation leaks into the automatic cursor or compensatory credits."""
    database = FakeDatabase()
    sellers = _seed_queue(database)
    database["seller_queue"].update_one(
        {"sellerId": sellers[0]}, {"$set": {"paused": True}}
    )
    database["skip_balances"].update_one(
        {"sellerId": sellers[1]}, {"$set": {"balance": 3}}
    )
    automatic_before = deepcopy(database["queue_state"].find_one({"_id": "global"}))

    result = _service(database).create_manual_lead("admin-yago", _command("manual-2"), NOW)

    assert result.assignee_id == str(sellers[1])
    assert database["queue_state"].find_one({"_id": "manual"})["nextSellerId"] == sellers[2]
    automatic_after = database["queue_state"].find_one({"_id": "global"})
    assert automatic_after["nextSellerId"] == automatic_before["nextSellerId"]
    assert automatic_after["version"] == automatic_before["version"]
    assert database["skip_balances"].find_one({"sellerId": sellers[1]})["balance"] == 3


def test_manual_creation_inherits_only_campaign_and_origin_from_latest_automatic_lead() -> None:
    """Breaks if fallback inheritance copies identity or PII from an automatic lead."""
    database = FakeDatabase()
    _seed_queue(database)
    older_campaign = ObjectId()
    latest_campaign = ObjectId()
    database["campaigns"].insert_one(
        {"_id": older_campaign, "displayName": "Campanha antiga"}
    )
    database["campaigns"].insert_one(
        {"_id": latest_campaign, "displayName": "Campanha vigente"}
    )
    database["leads"].insert_one(
        {
            "companyId": ObjectId(),
            "campaignId": older_campaign,
            "adName": "Meta antiga",
            "contactName": "Pessoa antiga",
            "phoneNormalized": "5511000000000",
            "emailNormalized": "antigo@example.com",
            "sourceEnteredAt": NOW - timedelta(days=2),
            "sourceLeadId": "AUTO-1",
            "archivedAt": None,
        }
    )
    database["leads"].insert_one(
        {
            "companyId": ObjectId(),
            "campaignId": latest_campaign,
            "adName": "Meta Ads",
            "contactName": "Pessoa automática",
            "phoneNormalized": "5511888888888",
            "emailNormalized": "automatico@example.com",
            "sourceEnteredAt": NOW - timedelta(days=1),
            "sourceLeadId": "AUTO-2",
            "archivedAt": None,
        }
    )

    result = _service(database).create_manual_lead("admin-yago", _command("manual-3"), NOW)

    lead = database["leads"].find_one({"_id": ObjectId(result.lead_id)})
    assert lead["campaignId"] == latest_campaign
    assert lead["campaignName"] == "Campanha vigente"
    assert lead["origin"] == "Meta Ads"
    assert lead["contactName"] == "Contato manual"
    assert lead["phone"] == "+55 11 99999-1234"
    assert lead["emailNormalized"] == "contato@example.com"
    assert "sourceLeadId" not in lead


def test_manual_creation_without_automatic_lead_keeps_campaign_and_origin_empty() -> None:
    """Breaks if missing inheritance fabricates campaign/origin data."""
    database = FakeDatabase()
    _seed_queue(database)

    result = _service(database).create_manual_lead("admin-yago", _command("manual-4"), NOW)

    lead = database["leads"].find_one({"_id": ObjectId(result.lead_id)})
    assert lead["campaignId"] is None
    assert lead["campaignName"] is None
    assert lead["origin"] is None


def test_manual_creation_is_idempotent_and_each_command_gets_a_unique_manual_id() -> None:
    """Breaks if retries duplicate a lead or separate commands reuse the manual identity."""
    database = FakeDatabase()
    _seed_queue(database)
    service = _service(database)

    first = service.create_manual_lead("admin-yago", _command("manual-same"), NOW)
    replay = service.create_manual_lead("admin-yago", _command("manual-same"), NOW)
    second = service.create_manual_lead("admin-yago", _command("manual-other"), NOW)

    assert replay == first
    assert second.manual_queue_lead_id != first.manual_queue_lead_id
    assert len([lead for lead in database["leads"].documents if lead.get("source") == "manual"]) == 2
    assert len(database["assignments"].documents) == 2
    assert len(database["command_results"].documents) == 2


def test_select_next_seller_exposes_the_explicit_manual_queue_contract() -> None:
    """Breaks if queue selection cannot address the independent manual cursor."""
    database = FakeDatabase()
    sellers = _seed_queue(database)

    selection = QueueService(QueueRepository(database)).select_next_seller("manual", NOW)

    assert selection.queue_kind == "manual"
    assert selection.seller_id == sellers[0]
    assert selection.next_seller_id == sellers[1]


def test_manual_queue_migration_initializes_an_independent_cursor_idempotently() -> None:
    """Breaks if deployment lacks a replay-safe initial state for the manual queue."""
    migration = import_module(
        "gerec_api.infrastructure.mongo.migrations.20260922_manual_queue_exportations"
    )
    database = FakeDatabase()
    sellers = _seed_queue(database)
    database["queue_state"].documents = [
        state for state in database["queue_state"].documents if state["_id"] == "global"
    ]

    migration.apply(database, now=lambda: NOW)
    migration.apply(database, now=lambda: NOW + timedelta(hours=1))

    manual_states = [
        state for state in database["queue_state"].documents if state["_id"] == "manual"
    ]
    assert manual_states == [
        {
            "_id": "manual",
            "nextSellerId": sellers[0],
            "version": 0,
            "createdAt": NOW,
            "updatedAt": NOW,
        }
    ]
    assert migration.VERSION in {version for version, _ in MIGRATIONS}


def test_manual_identifier_has_a_unique_partial_index_contract() -> None:
    """Breaks if concurrent manual commands can persist the same generated identity."""
    definitions = {definition.name: definition for definition in INDEXES}

    index = definitions["leads_manual_queue_lead_id_unique"]
    assert index.keys == (("manualQueueLeadId", 1),)
    assert index.unique is True
    assert index.partial_filter == {"manualQueueLeadId": {"$exists": True}}
