"""Integration coverage for the MongoDB schema bootstrap."""

import importlib.util
import os
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from bson import ObjectId
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError, PyMongoError, ServerSelectionTimeoutError, WriteError

from gerec_api.domain.documents import InvalidDocumentError, prepare_company_for_persistence
from gerec_api.infrastructure.mongo import collections as collection_contracts
from gerec_api.infrastructure.mongo.bootstrap import ensure_schema
from gerec_api.infrastructure.mongo.collections import MongoCollections
from gerec_api.infrastructure.mongo.indexes import INDEXES


def test_canonical_collection_registry_exposes_users() -> None:
    """Breaks if code can no longer use the canonical users collection name."""
    assert collection_contracts.MongoCollections.USERS == "users"


def test_document_validator_is_available_to_guard_persistence() -> None:
    """Breaks if company writes lack the domain document-validation boundary."""
    assert importlib.util.find_spec("gerec_api.domain.documents") is not None


def test_document_domain_validation_normalizes_valid_values_and_rejects_invalid_ones() -> None:
    """Breaks if an invalid CPF/CNPJ can reach a company persistence payload."""
    prepared = prepare_company_for_persistence({"documentNormalized": "04.252.011/0001-10", "name": "WTG"})

    assert prepared == {"documentNormalized": "04252011000110", "name": "WTG"}
    with pytest.raises(InvalidDocumentError):
        prepare_company_for_persistence({"documentNormalized": "11.111.111/1111-11"})


def test_index_contract_covers_each_persisted_identity_and_active_lifecycle() -> None:
    """Breaks if the schema stops declaring a required unique or partial invariant."""
    definitions = {definition.name: definition for definition in INDEXES}

    assert definitions["users_email_normalized_unique"].keys == (("emailNormalized", 1),)
    assert definitions["source_records_source_lead_id_unique"].keys == (("sourceLeadId", 1),)
    assert definitions["companies_document_normalized_present_unique"].partial_filter == {
        "documentNormalized": {"$exists": True}
    }
    assert definitions["leads_active_company_campaign_unique"].keys == (("companyId", 1), ("campaignId", 1))
    assert definitions["leads_active_company_campaign_unique"].partial_filter == {"archivedAt": None}
    assert definitions["sales_active_lead_unique"].partial_filter == {"reversedAt": None}
    assert definitions["sessions_token_hash_unique"].keys == (("tokenHash", 1),)
    assert all(definition.unique for definition in INDEXES)


@pytest.fixture
def mongo_db():
    """Provides an isolated database only when the local replica set is reachable."""
    client = MongoClient(
        os.getenv("MONGODB_URI", "mongodb://localhost:27017/?replicaSet=rs0"),
        serverSelectionTimeoutMS=1_500,
    )
    try:
        client.admin.command("ping")
    except (PyMongoError, ServerSelectionTimeoutError) as error:
        pytest.skip(f"MongoDB replica set indispon\u00edvel: {error}")

    database = client[f"gerec_indexes_test_{uuid4().hex}"]
    try:
        yield database
    finally:
        client.drop_database(database.name)
        client.close()


def test_ensure_schema_creates_canonical_collections_and_is_idempotent(mongo_db) -> None:
    """Breaks if a repeated bootstrap changes or omits the required MongoDB schema."""
    ensure_schema(mongo_db)
    ensure_schema(mongo_db)

    assert set(MongoCollections.ALL).issubset(set(mongo_db.list_collection_names()))
    indexes = {name: mongo_db[name].index_information() for name in MongoCollections.ALL}
    assert indexes[MongoCollections.USERS]["users_email_normalized_unique"]["unique"] is True
    assert indexes[MongoCollections.SOURCE_RECORDS]["source_records_source_lead_id_unique"]["unique"] is True
    assert indexes[MongoCollections.COMPANIES]["companies_document_normalized_present_unique"] == {
        "v": 2,
        "key": [("documentNormalized", 1)],
        "unique": True,
        "partialFilterExpression": {"documentNormalized": {"$exists": True}},
    }
    assert indexes[MongoCollections.LEADS]["leads_active_company_campaign_unique"] == {
        "v": 2,
        "key": [("companyId", 1), ("campaignId", 1)],
        "unique": True,
        "partialFilterExpression": {"archivedAt": None},
    }
    assert indexes[MongoCollections.SALES]["sales_active_lead_unique"] == {
        "v": 2,
        "key": [("leadId", 1)],
        "unique": True,
        "partialFilterExpression": {"reversedAt": None},
    }
    assert indexes[MongoCollections.SESSIONS]["sessions_token_hash_unique"]["unique"] is True


def test_unique_indexes_protect_active_records_without_blocking_archived_or_reversed_ones(mongo_db) -> None:
    """Breaks if a duplicate active identity or sale can be persisted."""
    ensure_schema(mongo_db)
    mongo_db[MongoCollections.USERS].insert_one({"emailNormalized": "yago@wtgseguros.com.br"})
    mongo_db[MongoCollections.SOURCE_RECORDS].insert_one({"sourceLeadId": "source-1"})
    mongo_db[MongoCollections.COMPANIES].insert_one({"documentNormalized": "04252011000110"})
    lead_id = ObjectId()
    company_id = ObjectId()
    campaign_id = ObjectId()
    mongo_db[MongoCollections.LEADS].insert_one(
        {"companyId": company_id, "campaignId": campaign_id, "archivedAt": None}
    )
    mongo_db[MongoCollections.SALES].insert_one({"leadId": lead_id, "reversedAt": None})
    mongo_db[MongoCollections.SESSIONS].insert_one({"tokenHash": "sha256-token"})

    with pytest.raises(DuplicateKeyError):
        mongo_db[MongoCollections.USERS].insert_one({"emailNormalized": "yago@wtgseguros.com.br"})
    with pytest.raises(DuplicateKeyError):
        mongo_db[MongoCollections.SOURCE_RECORDS].insert_one({"sourceLeadId": "source-1"})
    with pytest.raises(DuplicateKeyError):
        mongo_db[MongoCollections.COMPANIES].insert_one({"documentNormalized": "04252011000110"})
    with pytest.raises(DuplicateKeyError):
        mongo_db[MongoCollections.LEADS].insert_one(
            {"companyId": company_id, "campaignId": campaign_id, "archivedAt": None}
        )
    with pytest.raises(DuplicateKeyError):
        mongo_db[MongoCollections.SALES].insert_one({"leadId": lead_id, "reversedAt": None})
    with pytest.raises(DuplicateKeyError):
        mongo_db[MongoCollections.SESSIONS].insert_one({"tokenHash": "sha256-token"})

    mongo_db[MongoCollections.LEADS].insert_one(
        {"companyId": company_id, "campaignId": campaign_id, "archivedAt": datetime.now(UTC)}
    )
    mongo_db[MongoCollections.SALES].insert_one({"leadId": lead_id, "reversedAt": datetime.now(UTC)})


def test_company_schema_rejects_malformed_normalized_document(mongo_db) -> None:
    """Breaks if the database safety net accepts a malformed company document."""
    ensure_schema(mongo_db)

    with pytest.raises(WriteError):
        mongo_db[MongoCollections.COMPANIES].insert_one({"documentNormalized": "invalid"})
