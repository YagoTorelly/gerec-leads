"""Unit coverage for replica-set-only schema migration execution."""

from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime, timedelta
from importlib import import_module
from types import SimpleNamespace
from typing import Any

import pytest

from gerec_api.infrastructure.mongo.migrations import runner
from gerec_api.infrastructure.mongo.migrations.runner import ReplicaSetRequiredError, run_migrations

initialize_new_lead_notification_cursor = import_module(
    "gerec_api.infrastructure.mongo.migrations.20260914_initialize_new_lead_notification_cursor"
).apply


class FakeCollection:
    def __init__(self) -> None:
        self.documents: list[dict[str, Any]] = []

    def find_one(self, query: dict[str, Any], **_: Any) -> dict[str, Any] | None:
        return next((item for item in self.documents if all(item.get(key) == value for key, value in query.items())), None)

    def insert_one(self, document: dict[str, Any], **_: Any) -> SimpleNamespace:
        self.documents.append(deepcopy(document))
        return SimpleNamespace(inserted_id=document.get("_id"))

    def update_many(self, query: dict[str, Any], update: dict[str, Any], **_: Any) -> SimpleNamespace:
        updated = 0
        for document in self.documents:
            if all(
                document.get(key) == value
                if not isinstance(value, dict)
                else value.get("$exists") is (key in document)
                for key, value in query.items()
            ):
                document.update(update["$set"])
                updated += 1
        return SimpleNamespace(matched_count=updated, modified_count=updated)


class FakeSession:
    def __init__(self, database: "FakeDatabase") -> None:
        self._database = database
        self.transactions = 0

    def __enter__(self) -> "FakeSession":
        return self

    def __exit__(self, *_: Any) -> None:
        return None

    def with_transaction(self, callback):
        self.transactions += 1
        snapshot = {name: deepcopy(collection.documents) for name, collection in self._database.items()}
        try:
            return callback(self)
        except Exception:
            for name in set(self._database).difference(snapshot):
                del self._database[name]
            for name, documents in snapshot.items():
                self._database[name].documents = documents
            raise


class FakeClient:
    def __init__(self, database: "FakeDatabase", hello: dict[str, Any]) -> None:
        self.admin = SimpleNamespace(command=self._command)
        self._database = database
        self._hello = hello
        self.commands: list[str] = []
        self.sessions = 0
        self.last_session: FakeSession | None = None

    def _command(self, command: str) -> dict[str, Any]:
        self.commands.append(command)
        return self._hello

    def start_session(self) -> FakeSession:
        self.sessions += 1
        self.last_session = FakeSession(self._database)
        return self.last_session


class FakeDatabase(dict[str, FakeCollection]):
    def __init__(self, hello: dict[str, Any]) -> None:
        super().__init__()
        self.client = FakeClient(self, hello)

    def __getitem__(self, name: str) -> FakeCollection:
        if name not in self:
            self[name] = FakeCollection()
        return super().__getitem__(name)


def test_runner_requires_hello_with_replica_set_before_executing_a_migration(monkeypatch) -> None:
    """Breaks if a standalone ping can make a migration run outside a transaction."""
    database = FakeDatabase({"ok": 1})
    monkeypatch.setattr(runner, "MIGRATIONS", (("test-version", lambda *_args, **_kwargs: None),))

    with pytest.raises(ReplicaSetRequiredError, match="replica set"):
        run_migrations(database)

    assert database.client.commands == ["hello"]
    assert database.client.sessions == 0
    assert database["schema_migrations"].documents == []


def test_runner_applies_and_records_a_migration_in_one_replica_set_transaction(monkeypatch) -> None:
    """Breaks if a migration write or receipt escapes the transaction or replays."""
    database = FakeDatabase({"ok": 1, "setName": "rs0"})

    def migration(target, *, session) -> None:
        target["projection"].insert_one({"_id": "rebuilt"}, session=session)

    monkeypatch.setattr(runner, "MIGRATIONS", (("test-version", migration),))

    assert run_migrations(database) == ["test-version"]
    assert database.client.commands == ["hello"]
    assert database.client.sessions == 1
    assert database.client.last_session is not None
    assert database.client.last_session.transactions == 1
    assert database["projection"].documents == [{"_id": "rebuilt"}]
    assert database["schema_migrations"].documents == [{"_id": "test-version"}]
    assert run_migrations(database) == []


def test_runner_rolls_back_migration_writes_when_the_callback_fails(monkeypatch) -> None:
    """Breaks if a failed migration leaves its projection or receipt partially applied."""
    database = FakeDatabase({"ok": 1, "setName": "rs0"})

    def failing_migration(target, *, session) -> None:
        target["projection"].insert_one({"_id": "partial"}, session=session)
        raise RuntimeError("injected migration failure")

    monkeypatch.setattr(runner, "MIGRATIONS", (("test-version", failing_migration),))

    with pytest.raises(RuntimeError, match="injected migration failure"):
        run_migrations(database)

    assert database["projection"].documents == []
    assert database["schema_migrations"].documents == []


def test_cursor_migration_initializes_only_missing_sellers_once() -> None:
    """Breaks if a replay overwrites an acknowledged cursor or initializes non-sellers."""
    database = FakeDatabase({"ok": 1, "setName": "rs0"})
    missing_cursor_seller = {"_id": "seller-missing", "role": "seller"}
    existing = datetime(2026, 9, 1, tzinfo=UTC)
    existing_cursor_seller = {"_id": "seller-existing", "role": "seller", "newLeadsSeenAt": existing}
    admin = {"_id": "admin", "role": "admin"}
    database["users"].documents.extend([missing_cursor_seller, existing_cursor_seller, admin])
    now = datetime(2026, 9, 14, tzinfo=UTC)

    initialize_new_lead_notification_cursor(database, session=None, now=lambda: now)
    initialize_new_lead_notification_cursor(database, session=None, now=lambda: now + timedelta(days=1))

    assert missing_cursor_seller["newLeadsSeenAt"] == now
    assert existing_cursor_seller["newLeadsSeenAt"] == existing
    assert "newLeadsSeenAt" not in admin
