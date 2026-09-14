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
from gerec_api.infrastructure.mongo.bootstrap import SCHEMA_VALIDATORS, ensure_schema
from gerec_api.infrastructure.mongo.companies import CompanyRepository
from gerec_api.infrastructure.mongo.collections import MongoCollections
from gerec_api.infrastructure.mongo.indexes import INDEXES, MongoIndex


def test_canonical_collection_registry_exposes_users() -> None:
    """Breaks if code can no longer use the canonical users collection name."""
    assert collection_contracts.MongoCollections.USERS == "users"


def test_canonical_collection_registry_uses_the_migration_contract_names() -> None:
    """Breaks if a legacy collection name leaks into new MongoDB queries."""
    assert collection_contracts.MongoCollections.SKIP_BALANCES == "skip_balances"
    assert collection_contracts.MongoCollections.HOLIDAYS == "holidays"
    assert collection_contracts.MongoCollections.COMMAND_RESULTS == "command_results"


def test_document_validator_is_available_to_guard_persistence() -> None:
    """Breaks if company writes lack the domain document-validation boundary."""
    assert importlib.util.find_spec("gerec_api.domain.documents") is not None


def test_company_repository_uses_the_document_validation_boundary() -> None:
    """Breaks if a MongoDB company write can bypass CPF/CNPJ checksum validation."""
    assert importlib.util.find_spec("gerec_api.infrastructure.mongo.companies") is not None


def test_document_domain_validation_normalizes_valid_values_and_rejects_invalid_ones() -> None:
    """Breaks if an invalid CPF/CNPJ can reach a company persistence payload."""
    prepared = prepare_company_for_persistence({"documentNormalized": "04.252.011/0001-10", "name": "WTG"})

    assert prepared == {"documentNormalized": "04252011000110", "name": "WTG"}
    with pytest.raises(InvalidDocumentError):
        prepare_company_for_persistence({"documentNormalized": "11.111.111/1111-11"})


def test_company_repository_rejects_a_checksum_invalid_document_before_any_write() -> None:
    """Breaks if the persistence adapter sends checksum-invalid CNPJ data to MongoDB."""

    class TrackingCollection:
        def __init__(self) -> None:
            self.documents = []

        def insert_one(self, document):
            self.documents.append(document)
            return document

    target = TrackingCollection()
    repository = CompanyRepository(target)

    with pytest.raises(InvalidDocumentError):
        repository.insert({"documentNormalized": "12.345.678/0001-00"})

    assert target.documents == []


def test_company_repository_allows_a_pending_company_without_document() -> None:
    """Breaks if an import with missing CPF/CNPJ cannot persist its pending company record."""

    class TrackingCollection:
        def __init__(self) -> None:
            self.documents = []

        def insert_one(self, document):
            self.documents.append(document)
            return document

    target = TrackingCollection()

    CompanyRepository(target).insert({"name": "Documento pendente"})

    assert target.documents == [{"name": "Documento pendente"}]


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
    assert definitions["command_results_idempotency_key_unique"].keys == (("idempotencyKey", 1),)
    assert definitions["notification_outbox_idempotency_key_unique"].keys == (("idempotencyKey", 1),)
    assert definitions["notification_incidents_outbox_event_unique"].keys == (("outboxEventId", 1),)
    assert definitions["lead_treatments_lead_created_at"].keys == (("leadId", 1), ("createdAt", 1))
    assert definitions["lead_treatments_lead_created_at"].unique is False
    assert definitions["leads_assignee_assigned_at"].keys == (("assigneeId", 1), ("assignedAt", 1))
    assert definitions["leads_assignee_assignment_sequence"].keys == (("assigneeId", 1), ("assignmentSequence", 1))
    assert definitions["lead_treatments_lead_idempotency_key_unique"].keys == (("leadId", 1), ("idempotencyKey", 1))
    assert definitions["seller_queue_seller_unique"].keys == (("sellerId", 1),)
    assert definitions["seller_queue_position_present_unique"].partial_filter == {
        "position": {"$exists": True}
    }
    assert MongoCollections.AUTOMATION_JOB_LOCKS in MongoCollections.ALL
    assert all(
        definition.unique
        for definition in INDEXES
        if definition.name
        not in {
            "lead_treatments_lead_created_at",
            "leads_assignee_created_at",
            "leads_assignee_assigned_at",
            "leads_assignee_assignment_sequence",
            "lead_treatments_seller_created_at",
        }
    )


def test_command_results_enforce_idempotency_key_and_command_receipt_shape() -> None:
    """Breaks if a repeated critical command can create another operational result."""
    definitions = {definition.name: definition for definition in INDEXES}

    assert definitions["command_results_idempotency_key_unique"].keys == (("idempotencyKey", 1),)
    assert SCHEMA_VALIDATORS[MongoCollections.COMMAND_RESULTS]["$jsonSchema"]["required"] == [
        "commandName",
        "idempotencyKey",
        "result",
        "createdAt",
    ]


def test_indexed_fields_are_required_except_for_the_explicitly_optional_document_identity() -> None:
    """Breaks if a document without an indexed identity joins an active unique index."""
    required_by_collection = {
        name: definition["$jsonSchema"].get("required", []) for name, definition in SCHEMA_VALIDATORS.items()
    }

    assert required_by_collection[MongoCollections.USERS] == ["emailNormalized"]
    assert required_by_collection[MongoCollections.SOURCE_RECORDS] == ["sourceLeadId"]
    assert required_by_collection[MongoCollections.LEADS] == ["companyId", "campaignId", "archivedAt"]
    assert required_by_collection[MongoCollections.SALES] == ["leadId", "reversedAt"]
    assert required_by_collection[MongoCollections.SESSIONS] == ["tokenHash"]
    assert "documentNormalized" not in required_by_collection[MongoCollections.COMPANIES]


def test_mongo_index_reconciles_a_conflicting_named_index_without_touching_documents() -> None:
    """Breaks if bootstrap cannot safely replace an obsolete index definition by name."""

    class IndexCollection:
        def __init__(self) -> None:
            self.documents = [{"emailNormalized": "yago@wtgseguros.com.br"}]
            self.indexes = {
                "users_email_normalized_unique": {"key": [("emailNormalized", 1)], "unique": False}
            }

        def index_information(self):
            return self.indexes

        def create_index(self, keys, **options):
            name = options["name"]
            expected = {"key": list(keys), "unique": options.get("unique", False)}
            if "partialFilterExpression" in options:
                expected["partialFilterExpression"] = options["partialFilterExpression"]
            existing = self.indexes.get(name)
            if existing is not None and existing != expected:
                raise RuntimeError("IndexOptionsConflict")
            self.indexes[name] = expected
            return name

        def drop_index(self, name):
            del self.indexes[name]

    target = IndexCollection()
    definition = MongoIndex(
        MongoCollections.USERS,
        (("emailNormalized", 1),),
        "users_email_normalized_unique",
        unique=True,
    )

    assert definition.apply(target) == "users_email_normalized_unique"
    assert target.documents == [{"emailNormalized": "yago@wtgseguros.com.br"}]
    assert target.indexes == {"users_email_normalized_unique": {"key": [("emailNormalized", 1)], "unique": True}}


def test_mongo_index_removes_a_stale_replacement_after_a_previous_attempt() -> None:
    """Breaks if a rerun leaves the name__replacement index after recovering the canonical index."""

    class IndexCollection:
        def __init__(self) -> None:
            expected = {"key": [("emailNormalized", 1)], "unique": True}
            self.indexes = {
                "users_email_normalized_unique": expected.copy(),
                "users_email_normalized_unique__replacement": expected.copy(),
            }

        def index_information(self):
            return self.indexes

        def create_index(self, keys, **options):
            self.indexes[options["name"]] = {"key": list(keys), "unique": options.get("unique", False)}
            return options["name"]

        def drop_index(self, name):
            del self.indexes[name]

    target = IndexCollection()
    definition = MongoIndex(
        MongoCollections.USERS,
        (("emailNormalized", 1),),
        "users_email_normalized_unique",
        unique=True,
    )

    definition.apply(target)

    assert target.indexes == {"users_email_normalized_unique": {"key": [("emailNormalized", 1)], "unique": True}}


def test_mongo_index_restores_the_previous_index_and_cleans_replacement_after_failure() -> None:
    """Breaks if a failed reconciliation leaves a temporary index or removes the prior protection."""

    class IndexCollection:
        def __init__(self) -> None:
            self.indexes = {"users_email_normalized_unique": {"key": [("emailNormalized", 1)], "unique": False}}

        def index_information(self):
            return self.indexes

        def create_index(self, keys, **options):
            name = options["name"]
            if name == "users_email_normalized_unique" and options.get("unique") is True:
                raise RuntimeError("IndexBuildFailed")
            self.indexes[name] = {"key": list(keys), "unique": options.get("unique", False)}
            return name

        def drop_index(self, name):
            del self.indexes[name]

    target = IndexCollection()
    definition = MongoIndex(
        MongoCollections.USERS,
        (("emailNormalized", 1),),
        "users_email_normalized_unique",
        unique=True,
    )

    with pytest.raises(RuntimeError, match="IndexBuildFailed"):
        definition.apply(target)

    assert target.indexes == {"users_email_normalized_unique": {"key": [("emailNormalized", 1)], "unique": False}}


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
    assert indexes[MongoCollections.COMMAND_RESULTS]["command_results_idempotency_key_unique"]["unique"] is True


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
    mongo_db[MongoCollections.COMMAND_RESULTS].insert_one(
        {
            "commandName": "lead.assign",
            "idempotencyKey": "command-1",
            "result": {"assignmentId": "assignment-1"},
            "createdAt": datetime.now(UTC),
        }
    )

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
    with pytest.raises(DuplicateKeyError):
        mongo_db[MongoCollections.COMMAND_RESULTS].insert_one(
            {
                "commandName": "lead.assign",
                "idempotencyKey": "command-1",
                "result": {"assignmentId": "assignment-1"},
                "createdAt": datetime.now(UTC),
            }
        )

    mongo_db[MongoCollections.LEADS].insert_one(
        {"companyId": company_id, "campaignId": campaign_id, "archivedAt": datetime.now(UTC)}
    )
    mongo_db[MongoCollections.SALES].insert_one({"leadId": lead_id, "reversedAt": datetime.now(UTC)})


def test_company_schema_rejects_malformed_normalized_document(mongo_db) -> None:
    """Breaks if the database safety net accepts a malformed company document."""
    ensure_schema(mongo_db)

    with pytest.raises(WriteError):
        mongo_db[MongoCollections.COMPANIES].insert_one({"documentNormalized": "invalid"})


def test_schema_rejects_missing_indexed_fields_but_allows_a_company_without_document(mongo_db) -> None:
    """Breaks if active records can be stored without their indexed identity fields."""
    ensure_schema(mongo_db)

    for name, payload in (
        (MongoCollections.USERS, {}),
        (MongoCollections.SOURCE_RECORDS, {}),
        (MongoCollections.LEADS, {"companyId": ObjectId(), "campaignId": ObjectId()}),
        (MongoCollections.SALES, {"leadId": ObjectId()}),
        (MongoCollections.SESSIONS, {}),
        (MongoCollections.COMMAND_RESULTS, {"commandName": "lead.assign"}),
    ):
        with pytest.raises(WriteError):
            mongo_db[name].insert_one(payload)

    mongo_db[MongoCollections.COMPANIES].insert_one({"name": "Documento pendente"})
