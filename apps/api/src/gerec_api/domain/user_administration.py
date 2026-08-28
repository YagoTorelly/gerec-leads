"""Application commands for administrative user management."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Protocol

from gerec_api.auth.passwords import hash_password


UserRole = Literal["admin", "seller"]


class UserAdministrationError(RuntimeError):
    """Base error raised when an administrative user command cannot complete."""


class UserAlreadyExistsError(UserAdministrationError):
    """Raised when an e-mail is already owned by an account."""


class UserNotFoundError(UserAdministrationError):
    """Raised when the command target does not exist."""


@dataclass(frozen=True)
class CreateUserCommand:
    full_name: str
    email: str
    role: UserRole
    password: str


@dataclass(frozen=True)
class ManagedUser:
    id: str
    full_name: str
    email: str
    role: UserRole
    active: bool
    paused: bool | None

    def to_public(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "id": self.id,
            "fullName": self.full_name,
            "email": self.email,
            "role": self.role,
            "active": self.active,
        }
        if self.paused is not None:
            payload["paused"] = self.paused
        return payload


class UserAdministrationPersistence(Protocol):
    def create_user(
        self,
        command: CreateUserCommand,
        *,
        password_hash: str,
        actor_id: Any,
    ) -> ManagedUser: ...

    def set_manual_pause(
        self, user_id: Any, *, paused: bool, actor_id: Any
    ) -> ManagedUser: ...

    def reset_password(
        self, user_id: Any, *, password_hash: str, actor_id: Any
    ) -> ManagedUser: ...


class UserAdministrationService:
    """Validates commands before delegating every state change to persistence."""

    def __init__(self, persistence: UserAdministrationPersistence, *, actor_id: Any = "system") -> None:
        self._persistence = persistence
        self._actor_id = actor_id

    def with_actor(self, actor_id: Any) -> "UserAdministrationService":
        if actor_id is None or (isinstance(actor_id, str) and not actor_id.strip()):
            raise ValueError("actor id is required")
        return UserAdministrationService(self._persistence, actor_id=actor_id)

    def create_user(self, command: CreateUserCommand) -> ManagedUser:
        normalized = CreateUserCommand(
            full_name=_required(command.full_name, "full name"),
            email=_email(command.email),
            role=_role(command.role),
            password=_password(command.password),
        )
        return self._persistence.create_user(
            normalized,
            password_hash=hash_password(normalized.password),
            actor_id=self._actor_id,
        )

    def set_manual_pause(self, user_id: Any, paused: bool) -> ManagedUser:
        if not isinstance(paused, bool):
            raise ValueError("paused must be a boolean")
        return self._persistence.set_manual_pause(
            user_id,
            paused=paused,
            actor_id=self._actor_id,
        )

    def reset_password(self, user_id: Any, password: str) -> ManagedUser:
        return self._persistence.reset_password(
            user_id,
            password_hash=hash_password(_password(password)),
            actor_id=self._actor_id,
        )


def _required(value: str, label: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{label} is required")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{label} is required")
    return normalized


def _email(value: str) -> str:
    return _required(value, "email").casefold()


def _role(value: str) -> UserRole:
    if value not in {"admin", "seller"}:
        raise ValueError("role is invalid")
    return value


def _password(value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("password is required")
    return value
