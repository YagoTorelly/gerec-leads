"""Integration coverage for authentication HTTP boundaries and opaque sessions."""

from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from typing import Any

from bson import ObjectId
from fastapi.testclient import TestClient

from gerec_api.auth.passwords import hash_password
from gerec_api.auth.sessions import AuthService, InvalidSessionError
from gerec_api.config import Settings
from gerec_api.main import create_app


class FakeCollection:
    """Small Mongo-shaped collection used only to exercise the HTTP integration."""

    def __init__(self) -> None:
        self.documents: list[dict[str, Any]] = []

    def insert_one(self, document: dict[str, Any]) -> None:
        self.documents.append(deepcopy(document))

    def find_one(self, query: dict[str, Any]) -> dict[str, Any] | None:
        for document in self.documents:
            if _matches(document, query):
                return deepcopy(document)
        return None

    def update_one(self, query: dict[str, Any], update: dict[str, Any]) -> None:
        for document in self.documents:
            if _matches(document, query):
                document.update(deepcopy(update["$set"]))
                return

    def update_many(self, query: dict[str, Any], update: dict[str, Any]) -> None:
        for document in self.documents:
            if _matches(document, query):
                document.update(deepcopy(update["$set"]))


class FakeDatabase:
    def __init__(self) -> None:
        self.collections: dict[str, FakeCollection] = {}

    def __getitem__(self, name: str) -> FakeCollection:
        return self.collections.setdefault(name, FakeCollection())


def _matches(document: dict[str, Any], query: dict[str, Any]) -> bool:
    for key, expected in query.items():
        actual = document.get(key)
        if isinstance(expected, dict):
            if "$gt" in expected and not actual > expected["$gt"]:
                return False
            continue
        if actual != expected:
            return False
    return True


def _settings() -> Settings:
    return Settings(
        MONGODB_URI="mongodb://localhost:27017/?replicaSet=rs0",
        MONGODB_DATABASE="gerec_leads",
        APP_SECRET="test-only-secret",
    )


def _seed_active_user(database: FakeDatabase, *, active: bool = True) -> ObjectId:
    user_id = ObjectId()
    database["users"].insert_one(
        {
            "_id": user_id,
            "emailNormalized": "yago@wtgseguros.com.br",
            "passwordHash": hash_password("Senha-inicial-2026!"),
            "role": "admin",
            "active": active,
        }
    )
    return user_id


def test_login_persists_only_a_hash_and_sets_a_secure_http_only_cookie() -> None:
    """Breaks if login leaks a secret or stores a reusable raw session token."""
    database = FakeDatabase()
    user_id = _seed_active_user(database)
    client = TestClient(create_app(settings=_settings(), database=database))

    response = client.post(
        "/auth/login",
        json={"email": "YAGO@WTGSEGUROS.COM.BR", "password": "Senha-inicial-2026!"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "user": {"id": str(user_id), "email": "yago@wtgseguros.com.br", "role": "admin"}
    }
    set_cookie = response.headers["set-cookie"].lower()
    assert "httponly" in set_cookie
    assert "secure" in set_cookie
    session = database["sessions"].documents[0]
    assert set(session) == {"tokenHash", "userId", "expiresAt", "revokedAt", "createdAt", "updatedAt"}
    assert session["userId"] == user_id
    assert session["revokedAt"] is None
    assert "senha" not in repr(session).lower()
    assert "rawToken" not in session
    assert "passwordHash" not in response.text
    assert "Senha-inicial-2026!" not in response.text


def test_invalid_credentials_have_the_same_generic_response() -> None:
    """Breaks if bad passwords or unknown accounts reveal which account exists."""
    database = FakeDatabase()
    _seed_active_user(database)
    client = TestClient(create_app(settings=_settings(), database=database))

    wrong_password = client.post(
        "/auth/login",
        json={"email": "yago@wtgseguros.com.br", "password": "errada"},
    )
    unknown_account = client.post(
        "/auth/login",
        json={"email": "inexistente@wtgseguros.com.br", "password": "errada"},
    )

    assert wrong_password.status_code == unknown_account.status_code == 401
    assert wrong_password.json() == unknown_account.json() == {"detail": "Invalid credentials"}


def test_me_returns_only_the_public_identity_for_a_valid_session() -> None:
    """Breaks if a valid opaque cookie cannot resolve the authenticated identity."""
    database = FakeDatabase()
    user_id = _seed_active_user(database)
    client = TestClient(create_app(settings=_settings(), database=database))
    login = client.post(
        "/auth/login",
        json={"email": "yago@wtgseguros.com.br", "password": "Senha-inicial-2026!"},
    )
    raw_token = login.cookies.get("gerec_session")

    response = client.get("/auth/me", headers={"cookie": f"gerec_session={raw_token}"})

    assert response.status_code == 200
    assert response.json() == {"id": str(user_id), "email": "yago@wtgseguros.com.br", "role": "admin"}


def test_expired_or_revoked_sessions_cannot_resolve_a_current_user() -> None:
    """Breaks if expiry or logout revocation can be bypassed with an old token."""
    database = FakeDatabase()
    user_id = _seed_active_user(database)
    now = datetime(2026, 8, 27, 12, tzinfo=UTC)
    service = AuthService(database, now=lambda: now)
    raw_token = "expired-session-token"
    database["sessions"].insert_one(
        {
            "tokenHash": sha256(raw_token.encode()).hexdigest(),
            "userId": user_id,
            "expiresAt": now - timedelta(seconds=1),
            "revokedAt": None,
            "createdAt": now - timedelta(hours=1),
            "updatedAt": now - timedelta(hours=1),
        }
    )

    try:
        service.current_user(raw_token)
    except InvalidSessionError:
        pass
    else:
        raise AssertionError("an expired session must not authenticate")

    valid_session = service.login("yago@wtgseguros.com.br", "Senha-inicial-2026!")
    service.logout(valid_session.raw_token)
    try:
        service.current_user(valid_session.raw_token)
    except InvalidSessionError:
        pass
    else:
        raise AssertionError("a logged-out session must not authenticate")


def test_disabled_user_cannot_login_or_use_an_existing_session() -> None:
    """Breaks if an account deactivation leaves an authentication path open."""
    database = FakeDatabase()
    user_id = _seed_active_user(database, active=False)
    now = datetime(2026, 8, 27, 12, tzinfo=UTC)
    raw_token = "session-for-disabled-user"
    database["sessions"].insert_one(
        {
            "tokenHash": sha256(raw_token.encode()).hexdigest(),
            "userId": user_id,
            "expiresAt": now + timedelta(hours=1),
            "revokedAt": None,
            "createdAt": now,
            "updatedAt": now,
        }
    )
    service = AuthService(database, now=lambda: now)
    client = TestClient(create_app(settings=_settings(), database=database, auth_service=service))

    login = client.post(
        "/auth/login",
        json={"email": "yago@wtgseguros.com.br", "password": "Senha-inicial-2026!"},
    )
    current_user = client.get("/auth/me", headers={"cookie": f"gerec_session={raw_token}"})

    assert login.status_code == 401
    assert current_user.status_code == 401
    assert database["sessions"].documents[0]["revokedAt"] == now


def test_logout_clears_the_cookie_and_revokes_its_persisted_session() -> None:
    """Breaks if logout only removes a browser cookie while leaving the token usable."""
    database = FakeDatabase()
    _seed_active_user(database)
    client = TestClient(create_app(settings=_settings(), database=database))
    login = client.post(
        "/auth/login",
        json={"email": "yago@wtgseguros.com.br", "password": "Senha-inicial-2026!"},
    )
    raw_token = login.cookies.get("gerec_session")

    response = client.post("/auth/logout", headers={"cookie": f"gerec_session={raw_token}"})

    assert response.status_code == 204
    assert "max-age=0" in response.headers["set-cookie"].lower()
    assert database["sessions"].documents[0]["revokedAt"] is not None


def test_revoke_all_for_user_invalidates_every_active_session() -> None:
    """Breaks if a password reset cannot revoke all sessions for one account."""
    database = FakeDatabase()
    user_id = _seed_active_user(database)
    now = datetime(2026, 8, 27, 12, tzinfo=UTC)
    service = AuthService(database, now=lambda: now)
    first = service.login("yago@wtgseguros.com.br", "Senha-inicial-2026!")
    second = service.login("yago@wtgseguros.com.br", "Senha-inicial-2026!")

    service.revoke_all_for_user(user_id)

    for token in (first.raw_token, second.raw_token):
        try:
            service.current_user(token)
        except InvalidSessionError:
            pass
        else:
            raise AssertionError("every active session must be revoked")
    assert all(session["revokedAt"] == now for session in database["sessions"].documents)
