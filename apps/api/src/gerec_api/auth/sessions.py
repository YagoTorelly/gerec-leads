"""Opaque MongoDB-backed authentication sessions."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from secrets import token_urlsafe
from typing import Any

from gerec_api.auth.passwords import verify_password, verify_unknown_password
from gerec_api.infrastructure.mongo.collections import MongoCollections


SESSION_DURATION = timedelta(hours=8)


class InvalidCredentialsError(ValueError):
    """Login failed without revealing whether the account exists."""


class InvalidSessionError(ValueError):
    """A session token is missing, expired, revoked, or belongs to an inactive user."""


@dataclass(frozen=True)
class CurrentUser:
    """The public identity resolved from an active persisted session."""

    id: str
    email: str
    role: str


@dataclass(frozen=True)
class SessionResult:
    """Server-side login result; the raw token is for the HTTP-only cookie only."""

    raw_token: str
    expires_at: datetime
    user: CurrentUser


class AuthService:
    """Owns password verification and the opaque-session lifecycle."""

    def __init__(
        self,
        database: Any,
        *,
        now: Callable[[], datetime] | None = None,
        session_duration: timedelta = SESSION_DURATION,
    ) -> None:
        self._users = database[MongoCollections.USERS]
        self._sessions = database[MongoCollections.SESSIONS]
        self._now = now or _utcnow
        self._session_duration = session_duration

    def login(self, email: str, password: str) -> SessionResult:
        """Authenticate an active user and persist only the token SHA-256 digest."""
        user = self._users.find_one(
            {"emailNormalized": _normalize_email(email), "active": True}
        )
        digest = user.get("passwordHash") if user is not None else None
        if not isinstance(digest, str):
            verify_unknown_password(password)
            raise InvalidCredentialsError("Invalid credentials")
        if not verify_password(password, digest):
            raise InvalidCredentialsError("Invalid credentials")

        now = _as_utc(self._now())
        raw_token = token_urlsafe(32)
        expires_at = now + self._session_duration
        self._sessions.insert_one(
            {
                "tokenHash": _token_hash(raw_token),
                "userId": user["_id"],
                "expiresAt": expires_at,
                "revokedAt": None,
                "createdAt": now,
                "updatedAt": now,
            }
        )
        return SessionResult(
            raw_token=raw_token,
            expires_at=expires_at,
            user=_current_user_from_document(user),
        )

    def logout(self, raw_token: str) -> None:
        """Idempotently revoke the server-side session identified by an opaque token."""
        if not raw_token:
            return
        now = _as_utc(self._now())
        self._sessions.update_one(
            {"tokenHash": _token_hash(raw_token), "revokedAt": None},
            {"$set": {"revokedAt": now, "updatedAt": now}},
        )

    def revoke_all_for_user(self, user_id: Any) -> None:
        """Invalidate every currently active session for one account."""
        revoke_sessions_for_user(self._sessions, user_id, now=_as_utc(self._now()))

    def current_user(self, raw_token: str) -> CurrentUser:
        """Resolve a current user only from an unrevoked, unexpired opaque session."""
        if not raw_token:
            raise InvalidSessionError("Invalid session")
        now = _as_utc(self._now())
        token_hash = _token_hash(raw_token)
        session = self._sessions.find_one(
            {
                "tokenHash": token_hash,
                "revokedAt": None,
                "expiresAt": {"$gt": now},
            }
        )
        if session is None:
            raise InvalidSessionError("Invalid session")

        user = self._users.find_one({"_id": session["userId"], "active": True})
        if user is None:
            self._sessions.update_one(
                {"tokenHash": token_hash, "revokedAt": None},
                {"$set": {"revokedAt": now, "updatedAt": now}},
            )
            raise InvalidSessionError("Invalid session")
        return _current_user_from_document(user)


def _normalize_email(email: str) -> str:
    return email.strip().casefold()


def _token_hash(raw_token: str) -> str:
    return sha256(raw_token.encode("utf-8")).hexdigest()


def revoke_sessions_for_user(
    sessions: Any,
    user_id: Any,
    *,
    now: datetime,
    session: Any | None = None,
) -> None:
    """Revoke all active sessions, optionally in the caller's Mongo transaction."""
    options = {} if session is None else {"session": session}
    sessions.update_many(
        {"userId": user_id, "revokedAt": None},
        {"$set": {"revokedAt": now, "updatedAt": now}},
        **options,
    )


def _current_user_from_document(user: Mapping[str, Any]) -> CurrentUser:
    return CurrentUser(
        id=str(user["_id"]),
        email=str(user["emailNormalized"]),
        role=str(user.get("role", "seller")),
    )


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)
