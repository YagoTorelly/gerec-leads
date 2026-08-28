"""Integration coverage for administrative user commands and session revocation."""

from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any

from bson import ObjectId
from fastapi.testclient import TestClient

from gerec_api.auth.dependencies import get_current_user
from gerec_api.auth.passwords import hash_password
from gerec_api.auth.sessions import (
    AuthService,
    CurrentUser,
    InvalidCredentialsError,
    InvalidSessionError,
)
from gerec_api.config import Settings
from gerec_api.main import create_app


NOW = datetime(2026, 8, 28, 15, tzinfo=UTC)


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
                _apply_update(document, update, inserted=False)
                return SimpleNamespace(matched_count=1, modified_count=1, upserted_id=None)
        if not upsert:
            return SimpleNamespace(matched_count=0, modified_count=0, upserted_id=None)
        stored = {key: deepcopy(value) for key, value in query.items() if not isinstance(value, dict)}
        _apply_update(stored, update, inserted=True)
        stored.setdefault("_id", ObjectId())
        self.documents.append(stored)
        return SimpleNamespace(matched_count=0, modified_count=0, upserted_id=stored["_id"])

    def update_many(self, query: dict[str, Any], update: dict[str, Any], **_: Any):
        matched = 0
        for document in self.documents:
            if _matches(document, query):
                _apply_update(document, update, inserted=False)
                matched += 1
        return SimpleNamespace(matched_count=matched, modified_count=matched)


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
            if "$in" in expected and actual not in expected["$in"]:
                return False
            if "$ne" in expected and actual == expected["$ne"]:
                return False
            if "$gt" in expected and not (actual is not None and actual > expected["$gt"]):
                return False
            continue
        if actual != expected:
            return False
    return True


def _apply_update(document: dict[str, Any], update: dict[str, Any], *, inserted: bool) -> None:
    if inserted:
        document.update(deepcopy(update.get("$setOnInsert", {})))
    document.update(deepcopy(update.get("$set", {})))
    for key, amount in update.get("$inc", {}).items():
        document[key] = document.get(key, 0) + amount


def _contains_sensitive_key(value: Any) -> bool:
    if isinstance(value, dict):
        return any(
            str(key).casefold()
            in {"password", "passwordhash", "token", "tokenhash", "secret", "appsecret"}
            or _contains_sensitive_key(item)
            for key, item in value.items()
        )
    if isinstance(value, (list, tuple)):
        return any(_contains_sensitive_key(item) for item in value)
    return False


def _settings() -> Settings:
    return Settings(
        MONGODB_URI="mongodb://localhost:27017/?replicaSet=rs0",
        MONGODB_DATABASE="gerec_leads",
        APP_SECRET="task-six-test-secret",
    )


def _seed_admin(database: FakeDatabase) -> ObjectId:
    user_id = ObjectId()
    database["users"].insert_one(
        {
            "_id": user_id,
            "fullName": "Yago",
            "emailNormalized": "yago@wtgseguros.com.br",
            "passwordHash": hash_password("senha-admin"),
            "role": "admin",
            "active": True,
        }
    )
    return user_id


def _seed_queue(database: FakeDatabase) -> list[ObjectId]:
    sellers = [ObjectId(), ObjectId()]
    for position, seller_id in enumerate(sellers, start=1):
        database["users"].insert_one(
            {
                "_id": seller_id,
                "fullName": f"Vendedor {position}",
                "emailNormalized": f"seller{position}@example.test",
                "passwordHash": hash_password("senha-vendedor"),
                "role": "seller",
                "active": True,
            }
        )
        database["seller_queue"].insert_one(
            {"sellerId": seller_id, "position": position, "paused": False}
        )
    database["queue_state"].insert_one(
        {"_id": "global", "nextSellerId": sellers[0], "version": 0, "updatedAt": NOW}
    )
    return sellers


def _client(database: FakeDatabase, role: str = "admin") -> TestClient:
    app = create_app(settings=_settings(), database=database)
    app.dependency_overrides[get_current_user] = lambda: CurrentUser(
        "admin-id" if role == "admin" else "seller-id", f"{role}@example.test", role
    )
    return TestClient(app)


def test_admin_creates_a_seller_at_the_end_without_exposing_password_material() -> None:
    """Breaks if creation is decorative, leaks password data, or breaks queue order."""
    database = FakeDatabase()
    _seed_admin(database)
    existing = _seed_queue(database)

    response = _client(database).post(
        "/api/admin/users",
        json={
            "fullName": "Nova Vendedora",
            "email": "NOVA@EXAMPLE.TEST",
            "role": "seller",
            "password": "x",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body == {
        "id": body["id"],
        "fullName": "Nova Vendedora",
        "email": "nova@example.test",
        "role": "seller",
        "active": True,
        "paused": False,
    }
    assert "password" not in response.text.casefold()
    assert "hash" not in response.text.casefold()
    user_id = ObjectId(body["id"])
    assert database["users"].find_one({"_id": user_id})["passwordHash"] != "x"
    queue = sorted(database["seller_queue"].documents, key=lambda item: item["position"])
    assert [item["sellerId"] for item in queue] == [*existing, user_id]
    assert [item["position"] for item in queue] == [1, 2, 3]


def test_admin_creation_rejects_duplicate_email_and_blank_password() -> None:
    """Breaks if account uniqueness or the approved non-empty password rule is bypassed."""
    database = FakeDatabase()
    _seed_admin(database)
    client = _client(database)
    payload = {"fullName": "André", "email": "andre@example.test", "role": "admin", "password": "x"}

    assert client.post("/api/admin/users", json=payload).status_code == 201
    assert client.post("/api/admin/users", json=payload).status_code == 409
    blank = client.post(
        "/api/admin/users",
        json={**payload, "email": "other@example.test", "password": "   "},
    )
    assert blank.status_code == 422


def test_new_admin_never_enters_seller_queue() -> None:
    """Breaks if an administrative account receives a seller turn."""
    database = FakeDatabase()
    _seed_admin(database)
    _seed_queue(database)

    response = _client(database).post(
        "/api/admin/users",
        json={"fullName": "André", "email": "andre@example.test", "role": "admin", "password": "x"},
    )

    assert response.status_code == 201
    assert response.json()["role"] == "admin"
    assert len(database["seller_queue"].documents) == 2


def test_admin_pause_and_activation_only_change_manual_availability() -> None:
    """Breaks if pause transfers historical lead responsibility or mutates another state."""
    database = FakeDatabase()
    _seed_admin(database)
    seller_id = _seed_queue(database)[0]
    lead_id = ObjectId()
    database["leads"].insert_one({"_id": lead_id, "assigneeId": seller_id, "assignmentStatus": "assigned"})
    client = _client(database)

    paused = client.patch(f"/api/admin/users/{seller_id}/availability", json={"paused": True})
    active = client.patch(f"/api/admin/users/{seller_id}/availability", json={"paused": False})

    assert paused.status_code == 200
    assert paused.json()["paused"] is True
    assert active.status_code == 200
    assert active.json()["paused"] is False
    assert database["leads"].find_one({"_id": lead_id})["assigneeId"] == seller_id


def test_seller_cannot_execute_administrative_user_commands() -> None:
    """Breaks if hiding controls in the UI becomes the only administrative protection."""
    database = FakeDatabase()
    _seed_admin(database)
    response = _client(database, role="seller").post(
        "/api/admin/users",
        json={"fullName": "Não autorizado", "email": "no@example.test", "role": "seller", "password": "x"},
    )

    assert response.status_code == 403
    assert database["users"].find_one({"emailNormalized": "no@example.test"}) is None


def test_password_reset_revokes_every_existing_session_and_invalidates_old_password() -> None:
    """Breaks if a reset leaves a prior browser session or password usable."""
    database = FakeDatabase()
    admin_id = _seed_admin(database)
    auth = AuthService(database, now=lambda: NOW)
    first = auth.login("yago@wtgseguros.com.br", "senha-admin")
    second = auth.login("yago@wtgseguros.com.br", "senha-admin")
    client = _client(database)

    response = client.patch(f"/api/admin/users/{admin_id}/password", json={"password": "nova senha"})

    assert response.status_code == 200
    assert response.json()["id"] == str(admin_id)
    assert "password" not in response.text.casefold()
    for token in (first.raw_token, second.raw_token):
        try:
            auth.current_user(token)
        except InvalidSessionError:
            pass
        else:
            raise AssertionError("password reset must revoke every existing session")
    try:
        auth.login("yago@wtgseguros.com.br", "senha-admin")
    except InvalidCredentialsError:
        pass
    else:
        raise AssertionError("previous password must not authenticate after reset")
    assert auth.login("yago@wtgseguros.com.br", "nova senha").user.id == str(admin_id)


def test_admin_accepts_unbounded_nonempty_passwords_without_auditing_secrets() -> None:
    """Breaks if HTTP imposes an unapproved password limit or audit stores credentials."""
    database = FakeDatabase()
    admin_id = _seed_admin(database)
    client = _client(database)
    initial_password = "senha-inicial-" + ("a" * 2_000)
    replacement_password = "senha-nova-" + ("b" * 2_000)

    created = client.post(
        "/api/admin/users",
        json={
            "fullName": "Senha Longa",
            "email": "senha-longa@example.test",
            "role": "admin",
            "password": initial_password,
        },
    )
    reset = client.patch(
        f"/api/admin/users/{admin_id}/password",
        json={"password": replacement_password},
    )

    assert created.status_code == 201
    assert reset.status_code == 200
    audited = [
        item
        for item in database["audit_log"].documents
        if item["action"] in {"user.created", "user.password_reset"}
    ]
    assert {item["action"] for item in audited} == {"user.created", "user.password_reset"}
    for item in audited:
        rendered = repr(item).casefold()
        assert initial_password not in rendered
        assert replacement_password not in rendered
        assert "passwordhash" not in rendered
        assert not _contains_sensitive_key(item["before"])
        assert not _contains_sensitive_key(item["after"])


def test_blank_after_trim_passwords_return_safe_http_validation_errors() -> None:
    """Breaks if an invalid credential is reflected while creating or resetting a user."""
    database = FakeDatabase()
    admin_id = _seed_admin(database)
    client = _client(database)
    creation_password = " \t \n "
    reset_password = "\r\t  "

    created = client.post(
        "/api/admin/users",
        json={
            "fullName": "Senha Inválida",
            "email": "senha-invalida@example.test",
            "role": "seller",
            "password": creation_password,
        },
    )
    reset = client.patch(
        f"/api/admin/users/{admin_id}/password",
        json={"password": reset_password},
    )

    for response, password in ((created, creation_password), (reset, reset_password)):
        assert response.status_code == 422
        assert password not in response.text
        assert response.json() == {"detail": "password is required"}
