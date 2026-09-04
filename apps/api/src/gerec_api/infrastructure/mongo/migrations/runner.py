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
_remove_operational_sla = import_module(
    "gerec_api.infrastructure.mongo.migrations.20260904_remove_operational_sla"
)
MIGRATIONS: Final[tuple[Migration, ...]] = (
    (_operacao_comercial.VERSION, _operacao_comercial.apply),
    (_remove_operational_sla.VERSION, _remove_operational_sla.apply),
)


class ReplicaSetRequiredError(RuntimeError):
    """Raised when a migration cannot be protected by a MongoDB transaction."""


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

    _require_replica_set(database)
    try:
        with database.client.start_session() as session:
            return session.with_transaction(operation)
    except DuplicateKeyError:
        if database[MongoCollections.SCHEMA_MIGRATIONS].find_one({"_id": version}) is not None:
            return False
        raise


def _require_replica_set(database: Any) -> None:
    """Reject standalone MongoDB before a migration can mutate data without a transaction."""
    hello = database.client.admin.command("hello")
    if not hello.get("setName"):
        raise ReplicaSetRequiredError(
            "MongoDB replica set is required to apply schema migrations transactionally"
        )


def _session_options(session: Any | None) -> dict[str, Any]:
    return {} if session is None else {"session": session}
