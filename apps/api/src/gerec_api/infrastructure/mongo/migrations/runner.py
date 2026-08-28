"""Transactional runner for versioned MongoDB migrations."""

from __future__ import annotations

from importlib import import_module
from typing import Any, Callable, Final

from pymongo.errors import DuplicateKeyError

from gerec_api.infrastructure.mongo.collections import MongoCollections


Migration = tuple[str, Callable[..., None]]

_operacao_comercial = import_module(
    "gerec_api.infrastructure.mongo.migrations.20260828_operacao_comercial"
)
MIGRATIONS: Final[tuple[Migration, ...]] = (
    (_operacao_comercial.VERSION, _operacao_comercial.apply),
)


def run_migrations(database: Any) -> list[str]:
    """Apply each pending migration once, preserving historical documents on replay."""
    applied: list[str] = []
    for version, migration in MIGRATIONS:
        if database[MongoCollections.SCHEMA_MIGRATIONS].find_one({"_id": version}) is not None:
            continue
        if _apply_once(database, version, migration):
            applied.append(version)
    return applied


def _apply_once(database: Any, version: str, migration: Callable[..., None]) -> bool:
    def operation(session: Any | None) -> bool:
        migrations = database[MongoCollections.SCHEMA_MIGRATIONS]
        if migrations.find_one({"_id": version}, **_session_options(session)) is not None:
            return False
        migration(database, session=session)
        migrations.insert_one({"_id": version}, **_session_options(session))
        return True

    try:
        if _transactions_available(database):
            with database.client.start_session() as session:
                return session.with_transaction(operation)
        return operation(None)
    except DuplicateKeyError:
        if database[MongoCollections.SCHEMA_MIGRATIONS].find_one({"_id": version}) is not None:
            return False
        raise


def _transactions_available(database: Any) -> bool:
    """Use a transaction on replica sets while retaining a safe local bootstrap path."""
    hello = database.client.admin.command("hello")
    return bool(hello.get("setName") or hello.get("msg") == "isdbgrid")


def _session_options(session: Any | None) -> dict[str, Any]:
    return {} if session is None else {"session": session}
