"""Transactional MongoDB persistence for administrative user commands."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Callable

from bson import ObjectId
from pymongo.errors import DuplicateKeyError

from gerec_api.auth.sessions import revoke_sessions_for_user
from gerec_api.domain.user_administration import (
    CreateUserCommand,
    ManagedUser,
    UserAdministrationError,
    UserAlreadyExistsError,
    UserNotFoundError,
)
from gerec_api.infrastructure.mongo.collections import MongoCollections


QUEUE_STATE_ID = "global"


class _ConcurrentQueueChange(UserAdministrationError):
    """Abort a transaction whose queue version changed before the insert committed."""


class UserRepository:
    """Keep user, queue, audit and session changes inside one Mongo transaction."""

    def __init__(self, database: Any, *, now: Callable[[], datetime] | None = None) -> None:
        self._database = database
        self._now = now or (lambda: datetime.now(UTC))

    def create_user(
        self,
        command: CreateUserCommand,
        *,
        password_hash: str,
        actor_id: Any,
    ) -> ManagedUser:
        for _ in range(3):
            try:
                return self._run_transaction(
                    lambda session: self._create_user(command, password_hash, actor_id, session)
                )
            except _ConcurrentQueueChange:
                continue
            except DuplicateKeyError as error:
                if self._users.find_one({"emailNormalized": command.email}) is not None:
                    raise UserAlreadyExistsError("email is already registered") from error
                raise
        raise UserAdministrationError("queue changed concurrently; retry user creation")

    def set_manual_pause(
        self, user_id: Any, *, paused: bool, actor_id: Any
    ) -> ManagedUser:
        return self._run_transaction(
            lambda session: self._set_manual_pause(user_id, paused, actor_id, session)
        )

    def reset_password(self, user_id: Any, *, password_hash: str, actor_id: Any) -> ManagedUser:
        return self._run_transaction(
            lambda session: self._reset_password(user_id, password_hash, actor_id, session)
        )

    def _create_user(
        self,
        command: CreateUserCommand,
        password_hash: str,
        actor_id: Any,
        session: Any,
    ) -> ManagedUser:
        if self._users.find_one({"emailNormalized": command.email}, session=session) is not None:
            raise UserAlreadyExistsError("email is already registered")
        now = self._aware_now()
        user_id = ObjectId()
        document = {
            "_id": user_id,
            "fullName": command.full_name,
            "emailNormalized": command.email,
            "passwordHash": password_hash,
            "role": command.role,
            "active": True,
            "createdAt": now,
            "updatedAt": now,
        }
        if command.role == "seller":
            document["newLeadsSeenAt"] = now
        self._users.insert_one(document, session=session)
        paused: bool | None = None
        if command.role == "seller":
            position = self._append_seller(user_id, now, session)
            paused = False
            self._seller_queue.insert_one(
                {
                    "sellerId": user_id,
                    "position": position,
                    "paused": False,
                    "createdAt": now,
                    "updatedAt": now,
                },
                session=session,
            )
            self._skip_balances.update_one(
                {"sellerId": user_id},
                {
                    "$setOnInsert": {
                        "sellerId": user_id,
                        "balance": 0,
                        "createdAt": now,
                    },
                    "$set": {"updatedAt": now},
                },
                upsert=True,
                session=session,
            )
        result = ManagedUser(
            id=str(user_id),
            full_name=command.full_name,
            email=command.email,
            role=command.role,
            active=True,
            paused=paused,
        )
        self._audit(
            action="user.created",
            actor_id=actor_id,
            entity_id=user_id,
            before=None,
            after=result.to_public(),
            now=now,
            session=session,
        )
        return result

    def _set_manual_pause(
        self, user_id: Any, paused: bool, actor_id: Any, session: Any
    ) -> ManagedUser:
        user = self._user_or_error(user_id, session)
        if user.get("role") != "seller":
            raise UserAdministrationError("only sellers have manual availability")
        queue = self._seller_queue.find_one({"sellerId": user["_id"]}, session=session)
        if queue is None:
            raise UserAdministrationError("seller is not in the queue")
        now = self._aware_now()
        self._seller_queue.update_one(
            {"_id": queue["_id"]},
            {"$set": {"paused": paused, "updatedAt": now}},
            session=session,
        )
        result = _managed_user(user, paused=paused)
        self._audit(
            action="user.availability_changed",
            actor_id=actor_id,
            entity_id=user["_id"],
            before={"paused": bool(queue.get("paused", False))},
            after={"paused": paused},
            now=now,
            session=session,
        )
        return result

    def _reset_password(
        self, user_id: Any, password_hash: str, actor_id: Any, session: Any
    ) -> ManagedUser:
        user = self._user_or_error(user_id, session)
        now = self._aware_now()
        self._users.update_one(
            {"_id": user["_id"]},
            {"$set": {"passwordHash": password_hash, "updatedAt": now}},
            session=session,
        )
        revoke_sessions_for_user(self._sessions, user["_id"], now=now, session=session)
        queue = self._seller_queue.find_one({"sellerId": user["_id"]}, session=session)
        result = _managed_user(user, paused=(bool(queue.get("paused", False)) if queue else None))
        self._audit(
            action="user.password_reset",
            actor_id=actor_id,
            entity_id=user["_id"],
            before={"passwordChanged": False},
            after={"passwordChanged": True},
            now=now,
            session=session,
        )
        return result

    def _append_seller(self, user_id: ObjectId, now: datetime, session: Any) -> int:
        """Reserve a final queue position while holding the queue-state version."""
        state = self._queue_state.find_one({"_id": QUEUE_STATE_ID}, session=session)
        entries = self._seller_queue.find({}, session=session)
        positions = [
            int(entry["position"])
            for entry in entries
            if isinstance(entry.get("position"), int) and not isinstance(entry["position"], bool)
        ]
        position = max(positions, default=0) + 1
        if state is None:
            self._queue_state.insert_one(
                {
                    "_id": QUEUE_STATE_ID,
                    "nextSellerId": user_id,
                    "version": 0,
                    "createdAt": now,
                    "updatedAt": now,
                },
                session=session,
            )
            return position
        updated = self._queue_state.update_one(
            {"_id": QUEUE_STATE_ID, "version": state.get("version", 0)},
            {"$set": {"updatedAt": now}, "$inc": {"version": 1}},
            session=session,
        )
        if updated.matched_count != 1:
            raise _ConcurrentQueueChange("queue changed while appending seller")
        return position

    def _user_or_error(self, user_id: Any, session: Any) -> dict[str, Any]:
        candidate_ids = [user_id]
        if isinstance(user_id, str) and ObjectId.is_valid(user_id):
            candidate_ids.append(ObjectId(user_id))
        for candidate in candidate_ids:
            user = self._users.find_one({"_id": candidate}, session=session)
            if user is not None:
                return user
        raise UserNotFoundError("user not found")

    def _run_transaction(self, callback: Callable[[Any], ManagedUser]) -> ManagedUser:
        with self._database.client.start_session() as session:
            return session.with_transaction(callback)

    def _audit(
        self,
        *,
        action: str,
        actor_id: Any,
        entity_id: Any,
        before: dict[str, Any] | None,
        after: dict[str, Any],
        now: datetime,
        session: Any,
    ) -> None:
        self._audit_log.insert_one(
            {
                "actorId": actor_id,
                "action": action,
                "entityType": "user",
                "entityId": entity_id,
                "before": before,
                "after": after,
                "createdAt": now,
            },
            session=session,
        )

    def _aware_now(self) -> datetime:
        value = self._now()
        return value if value.tzinfo is not None else value.replace(tzinfo=UTC)

    @property
    def _users(self):
        return self._database[MongoCollections.USERS]

    @property
    def _seller_queue(self):
        return self._database[MongoCollections.SELLER_QUEUE]

    @property
    def _queue_state(self):
        return self._database[MongoCollections.QUEUE_STATE]

    @property
    def _skip_balances(self):
        return self._database[MongoCollections.SKIP_BALANCES]

    @property
    def _sessions(self):
        return self._database[MongoCollections.SESSIONS]

    @property
    def _audit_log(self):
        return self._database[MongoCollections.AUDIT_LOG]


def _managed_user(user: dict[str, Any], *, paused: bool | None) -> ManagedUser:
    role = str(user.get("role", "seller"))
    if role not in {"admin", "seller"}:
        raise UserAdministrationError("user role is invalid")
    return ManagedUser(
        id=str(user["_id"]),
        full_name=str(user.get("fullName") or user.get("name") or user["emailNormalized"]),
        email=str(user["emailNormalized"]),
        role=role,  # type: ignore[arg-type]
        active=bool(user.get("active", True)),
        paused=paused,
    )
