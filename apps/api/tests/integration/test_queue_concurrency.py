"""Replica-set concurrency proof for serialized global queue assignments."""

from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
import os
from uuid import uuid4

import pytest
from bson import ObjectId
from pymongo import MongoClient
from pymongo.errors import PyMongoError, ServerSelectionTimeoutError

from gerec_api.domain.queue import QueueService
from gerec_api.infrastructure.mongo.bootstrap import ensure_schema
from gerec_api.infrastructure.mongo.collections import MongoCollections
from gerec_api.infrastructure.mongo.queue_repository import QueueRepository


@pytest.fixture
def mongo_queue_db():
    """Use an isolated real database and explicitly skip without a reachable replica set."""
    client = MongoClient(
        os.getenv("MONGODB_URI", "mongodb://localhost:27017/?replicaSet=rs0"),
        serverSelectionTimeoutMS=1_500,
    )
    try:
        client.admin.command("ping")
        hello = client.admin.command("hello")
        if not hello.get("setName"):
            pytest.skip("MongoDB real disponível, mas não está em replica set")
    except (PyMongoError, ServerSelectionTimeoutError) as error:
        pytest.skip(f"MongoDB replica set indisponível: {error}")
    database = client[f"gerec_queue_test_{uuid4().hex}"]
    ensure_schema(database)
    try:
        yield database
    finally:
        client.drop_database(database.name)
        client.close()


def test_ac29_concurrent_leads_have_unique_assignments_and_sequential_cursor(mongo_queue_db) -> None:
    """Breaks if concurrent transactions reuse the cursor, assignment, or a skip credit."""
    now = datetime(2026, 8, 27, 15, tzinfo=UTC)
    sellers = [ObjectId() for _ in range(4)]
    for position, seller_id in enumerate(sellers, start=1):
        mongo_queue_db[MongoCollections.USERS].insert_one(
            {
                "_id": seller_id,
                "emailNormalized": f"seller-{position}@example.test",
                "active": True,
            }
        )
        mongo_queue_db[MongoCollections.SELLER_QUEUE].insert_one(
            {"sellerId": seller_id, "position": position, "paused": False}
        )
        mongo_queue_db[MongoCollections.SKIP_BALANCES].insert_one(
            {"sellerId": seller_id, "balance": 0}
        )
    mongo_queue_db[MongoCollections.QUEUE_STATE].insert_one(
        {"_id": "global", "nextSellerId": sellers[0], "version": 0, "updatedAt": now}
    )
    blocked_company_id = mongo_queue_db[MongoCollections.COMPANIES].insert_one(
        {"ownerId": sellers[0]}
    ).inserted_id
    blocked_lead_id = mongo_queue_db[MongoCollections.LEADS].insert_one(
        {
            "companyId": blocked_company_id,
            "campaignId": ObjectId(),
            "archivedAt": None,
            "assignmentStatus": "assigned",
            "assigneeId": sellers[0],
            "currentAssignmentId": ObjectId(),
            "sourceEnteredAt": now - timedelta(seconds=1),
            "sourceLeadId": "overdue-seller-zero",
        }
    ).inserted_id
    mongo_queue_db[MongoCollections.FEEDBACK_CYCLES].insert_one(
        {"leadId": blocked_lead_id, "dueAt": now - timedelta(seconds=1), "closedAt": None}
    )
    campaign_id = ObjectId()
    leads = []
    for offset in range(2):
        company_id = mongo_queue_db[MongoCollections.COMPANIES].insert_one(
            {"ownerId": None}
        ).inserted_id
        lead_id = mongo_queue_db[MongoCollections.LEADS].insert_one(
            {
                "companyId": company_id,
                "campaignId": campaign_id,
                "archivedAt": None,
                "assignmentStatus": "ready",
                "assigneeId": None,
                "currentAssignmentId": None,
                "sourceEnteredAt": now + timedelta(seconds=offset),
                "sourceLeadId": f"concurrent-{offset}",
            }
        ).inserted_id
        leads.append(lead_id)

    service = QueueService(QueueRepository(mongo_queue_db, now=lambda: now))
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(
            pool.map(
                lambda item: service.distribute_normal(item[1], f"concurrent-{item[0]}"),
                enumerate(leads),
            )
        )

    assignments = list(mongo_queue_db[MongoCollections.ASSIGNMENTS].find({"current": True}))
    state = mongo_queue_db[MongoCollections.QUEUE_STATE].find_one({"_id": "global"})
    balances = list(mongo_queue_db[MongoCollections.SKIP_BALANCES].find({}))
    assert len(assignments) == 2
    assert {assignment["leadId"] for assignment in assignments} == set(leads)
    assert {result.seller_id for result in results} == {str(sellers[1]), str(sellers[2])}
    assert state["nextSellerId"] == sellers[3]
    assert state["version"] == 2
    assert all(balance["balance"] >= 0 for balance in balances)
