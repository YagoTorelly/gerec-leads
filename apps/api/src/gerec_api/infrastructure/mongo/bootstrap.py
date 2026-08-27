"""Bootstrap n\u00e3o destrutivo do schema MongoDB."""

from typing import Any, Final

from pymongo.errors import CollectionInvalid
from pymongo.database import Database

from gerec_api.infrastructure.mongo.collections import MongoCollections, collection
from gerec_api.infrastructure.mongo.indexes import INDEXES


SCHEMA_VALIDATORS: Final[dict[str, dict[str, Any]]] = {
    MongoCollections.USERS: {
        "$jsonSchema": {
            "bsonType": "object",
            "properties": {"emailNormalized": {"bsonType": "string", "minLength": 1}},
        }
    },
    MongoCollections.SOURCE_RECORDS: {
        "$jsonSchema": {
            "bsonType": "object",
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
    MongoCollections.LEADS: {
        "$jsonSchema": {
            "bsonType": "object",
            "properties": {
                "companyId": {"bsonType": "objectId"},
                "campaignId": {"bsonType": "objectId"},
                "archivedAt": {"bsonType": ["date", "null"]},
            },
        }
    },
    MongoCollections.SALES: {
        "$jsonSchema": {
            "bsonType": "object",
            "properties": {
                "leadId": {"bsonType": "objectId"},
                "reversedAt": {"bsonType": ["date", "null"]},
            },
        }
    },
    MongoCollections.SESSIONS: {
        "$jsonSchema": {
            "bsonType": "object",
            "properties": {"tokenHash": {"bsonType": "string", "minLength": 1}},
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
