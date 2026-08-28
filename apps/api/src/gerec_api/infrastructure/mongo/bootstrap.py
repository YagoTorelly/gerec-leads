"""Bootstrap n\u00e3o destrutivo do schema MongoDB."""

from typing import Any, Final

from pymongo.errors import CollectionInvalid
from pymongo.database import Database

from gerec_api.infrastructure.mongo.collections import MongoCollections, collection
from gerec_api.infrastructure.mongo.indexes import INDEXES
from gerec_api.infrastructure.mongo.migrations.runner import run_migrations


SCHEMA_VALIDATORS: Final[dict[str, dict[str, Any]]] = {
    MongoCollections.USERS: {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["emailNormalized"],
            "properties": {"emailNormalized": {"bsonType": "string", "minLength": 1}},
        }
    },
    MongoCollections.SOURCE_RECORDS: {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["sourceLeadId"],
            "properties": {"sourceLeadId": {"bsonType": "string", "minLength": 1}},
        }
    },
    MongoCollections.COMPANIES: {
        "$jsonSchema": {
            "bsonType": "object",
            "properties": {
                "documentNormalized": {"bsonType": "string", "pattern": "^(?:[0-9]{11}|[0-9]{14})$"}
            },
        }
    },
    MongoCollections.SKIP_BALANCES: {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["sellerId", "balance"],
            "properties": {
                "sellerId": {"bsonType": "objectId"},
                "balance": {"bsonType": "int", "minimum": 0},
            },
        }
    },
    MongoCollections.LEADS: {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["companyId", "campaignId", "archivedAt"],
            "properties": {
                "companyId": {"bsonType": "objectId"},
                "campaignId": {"bsonType": "objectId"},
                "archivedAt": {"bsonType": ["date", "null"]},
                "commercialStatus": {"enum": ["undefined", "negotiation", "won"]},
                "isDisqualified": {"bsonType": "bool"},
                "commentCount": {"bsonType": "int", "minimum": 0},
                "lastCommentAt": {"bsonType": ["date", "null"]},
                "feedbackDueAt": {"bsonType": ["date", "null"]},
                "feedbackReminderAt": {"bsonType": ["date", "null"]},
            },
        }
    },
    MongoCollections.LEAD_TREATMENTS: {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["leadId", "comment", "createdAt", "idempotencyKey"],
            "properties": {
                "leadId": {"bsonType": "objectId"},
                "comment": {"bsonType": "string", "minLength": 6},
                "createdAt": {"bsonType": "date"},
                "idempotencyKey": {"bsonType": "string", "minLength": 1},
            },
        }
    },
    MongoCollections.SALES: {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["leadId", "reversedAt"],
            "properties": {
                "leadId": {"bsonType": "objectId"},
                "reversedAt": {"bsonType": ["date", "null"]},
            },
        }
    },
    MongoCollections.SESSIONS: {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["tokenHash"],
            "properties": {"tokenHash": {"bsonType": "string", "minLength": 1}},
        }
    },
    MongoCollections.COMMAND_RESULTS: {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["commandName", "idempotencyKey", "result", "createdAt"],
            "properties": {
                "commandName": {"bsonType": "string", "minLength": 1},
                "idempotencyKey": {"bsonType": "string", "minLength": 1},
                "result": {"bsonType": "object"},
                "createdAt": {"bsonType": "date"},
            },
        }
    },
}


def ensure_schema(db: Database) -> None:
    """Cria cole\u00e7\u00f5es, valida\u00e7\u00f5es e \u00edndices de modo idempotente e sem exclus\u00f5es."""
    for name in MongoCollections.ALL:
        validator = SCHEMA_VALIDATORS.get(name)
        if validator is None:
            _ensure_collection(db, name)
        else:
            _ensure_collection_validator(db, name, validator)

    for index in INDEXES:
        index.apply(collection(db, index.collection_name))

    run_migrations(db)


def _ensure_collection_validator(db: Database, name: str, validator: dict[str, Any]) -> None:
    try:
        db.create_collection(
            name,
            validator=validator,
            validationLevel="strict",
            validationAction="error",
        )
    except CollectionInvalid:
        db.command(
            {
                "collMod": name,
                "validator": validator,
                "validationLevel": "strict",
                "validationAction": "error",
            }
        )


def _ensure_collection(db: Database, name: str) -> None:
    try:
        db.create_collection(name)
    except CollectionInvalid:
        return
