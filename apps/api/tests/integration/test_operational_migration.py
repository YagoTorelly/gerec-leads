"""Integration coverage for the idempotent commercial-operation migration."""

from __future__ import annotations

import os
from copy import deepcopy
from datetime import datetime
from uuid import uuid4
from zoneinfo import ZoneInfo

import pytest
from bson import ObjectId
from pymongo import MongoClient
from pymongo.errors import PyMongoError, ServerSelectionTimeoutError

from gerec_api.infrastructure.mongo.bootstrap import ensure_schema
from gerec_api.infrastructure.mongo.migrations.runner import run_migrations


SAO_PAULO = ZoneInfo("America/Sao_Paulo")
FRIDAY_AT_FIVE = datetime(2026, 8, 28, 17, 0, tzinfo=SAO_PAULO)
VALID_COMMENT_AT = datetime(2026, 8, 31, 10, 0, tzinfo=SAO_PAULO)


@pytest.fixture
def mongo_db():
    """Provide an isolated replica-set database for transactional migration coverage."""
    client = MongoClient(
        os.getenv("MONGODB_URI", "mongodb://localhost:27017/?replicaSet=rs0"),
        serverSelectionTimeoutMS=1_500,
        tz_aware=True,
    )
    try:
        client.admin.command("ping")
    except (PyMongoError, ServerSelectionTimeoutError) as error:
        pytest.skip(f"MongoDB replica set indisponível: {error}")

    database = client[f"gerec_operational_migration_test_{uuid4().hex}"]
    try:
        yield database
    finally:
        client.drop_database(database.name)
        client.close()


def test_operational_migration_materializes_projections_without_losing_history(mongo_db) -> None:
    """Breaks if replaying the operational migration changes or deletes legacy history."""
    seller_id = ObjectId()
    lead_id = ObjectId()
    cycle_id = ObjectId()
    session_id = ObjectId()

    mongo_db["leads"].insert_one(
        {
            "_id": lead_id,
            "companyId": ObjectId(),
            "campaignId": ObjectId(),
            "archivedAt": None,
            "assignmentStatus": "assigned",
            "assigneeId": seller_id,
            "qualificationStatus": "disqualified",
            "conversionStatus": "won",
        }
    )
    mongo_db["assignments"].insert_one(
        {"leadId": lead_id, "sellerId": seller_id, "current": True, "startedAt": FRIDAY_AT_FIVE}
    )
    mongo_db["feedbacks"].insert_many(
        [
            {
                "leadId": lead_id,
                "sellerId": seller_id,
                "kind": "seller_feedback",
                "contactStarted": True,
                "comment": "Cliente confirmou o retorno",
                "createdAt": VALID_COMMENT_AT,
            },
            {
                "leadId": lead_id,
                "sellerId": seller_id,
                "kind": "administrative_note",
                "comment": "Nota administrativa que não é tratativa",
                "createdAt": datetime(2026, 8, 31, 11, 0, tzinfo=SAO_PAULO),
            },
            {
                "leadId": lead_id,
                "sellerId": seller_id,
                "kind": "seller_feedback",
                "contactStarted": True,
                "comment": " curto ",
                "createdAt": datetime(2026, 8, 31, 12, 0, tzinfo=SAO_PAULO),
            },
        ]
    )
    mongo_db["qualification_events"].insert_one(
        {
            "leadId": lead_id,
            "actorId": seller_id,
            "outcome": "disqualified",
            "comment": "Sem enquadramento",
            "createdAt": datetime(2026, 8, 31, 13, 0, tzinfo=SAO_PAULO),
        }
    )
    mongo_db["feedback_cycles"].insert_one(
        {
            "_id": cycle_id,
            "leadId": lead_id,
            "startAt": FRIDAY_AT_FIVE,
            "reminderAt": datetime(2026, 8, 31, 13, 0, tzinfo=SAO_PAULO),
            "dueAt": datetime(2026, 9, 1, 17, 0, tzinfo=SAO_PAULO),
            "closedAt": None,
        }
    )
    mongo_db["sessions"].insert_one({"_id": session_id, "tokenHash": "historical-token"})
    mongo_db["seller_queue"].insert_one({"sellerId": seller_id, "position": 1, "paused": False})

    history_before = {
        name: deepcopy(list(mongo_db[name].find()))
        for name in ("assignments", "feedbacks", "qualification_events", "sessions")
    }

    ensure_schema(mongo_db)

    lead_after_first_run = mongo_db["leads"].find_one({"_id": lead_id})
    assert lead_after_first_run is not None
    assert lead_after_first_run["commercialStatus"] == "won"
    assert lead_after_first_run["isDisqualified"] is True
    assert lead_after_first_run["commentCount"] == 1
    assert lead_after_first_run["lastCommentAt"] == VALID_COMMENT_AT
    assert lead_after_first_run["feedbackDueAt"] is None
    assert lead_after_first_run["feedbackReminderAt"] is None
    assert mongo_db["feedback_cycles"].find_one({"_id": cycle_id})["closedAt"] is not None

    assert len(list(mongo_db["lead_treatments"].find({"leadId": lead_id}))) == 1
    assert mongo_db["schema_migrations"].count_documents({"_id": "20260828_operacao_comercial"}) == 1
    for name, expected in history_before.items():
        assert list(mongo_db[name].find()) == expected

    assert run_migrations(mongo_db) == []

    assert mongo_db["leads"].find_one({"_id": lead_id}) == lead_after_first_run
    assert len(list(mongo_db["lead_treatments"].find({"leadId": lead_id}))) == 1
    assert mongo_db["sessions"].find_one({"_id": session_id}) == history_before["sessions"][0]
    assert mongo_db["schema_migrations"].count_documents({"_id": "20260828_operacao_comercial"}) == 1

    treatments_indexes = mongo_db["lead_treatments"].index_information()
    queue_indexes = mongo_db["seller_queue"].index_information()
    assert treatments_indexes["lead_treatments_lead_created_at"]["key"] == [("leadId", 1), ("createdAt", 1)]
    assert treatments_indexes["lead_treatments_lead_idempotency_key_unique"]["unique"] is True
    assert queue_indexes["seller_queue_seller_unique"]["unique"] is True
    assert queue_indexes["seller_queue_position_present_unique"]["unique"] is True


def test_operational_migration_recalculates_open_legacy_cycle_in_business_hours(mongo_db) -> None:
    """Breaks if an open legacy cycle retains the pre-GOV-004 continuous deadline."""
    lead_id = ObjectId()
    cycle_id = ObjectId()
    mongo_db["leads"].insert_one(
        {
            "_id": lead_id,
            "companyId": ObjectId(),
            "campaignId": ObjectId(),
            "archivedAt": None,
            "assignmentStatus": "assigned",
            "qualificationStatus": "pending",
            "conversionStatus": "active",
        }
    )
    mongo_db["feedback_cycles"].insert_one(
        {
            "_id": cycle_id,
            "leadId": lead_id,
            "startAt": FRIDAY_AT_FIVE,
            "reminderAt": datetime(2026, 8, 31, 13, 0, tzinfo=SAO_PAULO),
            "dueAt": datetime(2026, 8, 31, 17, 0, tzinfo=SAO_PAULO),
            "closedAt": None,
        }
    )

    ensure_schema(mongo_db)

    lead = mongo_db["leads"].find_one({"_id": lead_id})
    cycle = mongo_db["feedback_cycles"].find_one({"_id": cycle_id})
    assert lead["commercialStatus"] == "undefined"
    assert lead["isDisqualified"] is False
    assert lead["commentCount"] == 0
    assert lead["lastCommentAt"] is None
    assert lead["feedbackDueAt"] == datetime(2026, 9, 2, 14, 0, tzinfo=SAO_PAULO)
    assert lead["feedbackReminderAt"] == datetime(2026, 9, 2, 10, 0, tzinfo=SAO_PAULO)
    assert cycle["dueAt"] == lead["feedbackDueAt"]
    assert cycle["reminderAt"] == lead["feedbackReminderAt"]
