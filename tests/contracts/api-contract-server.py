"""Controlled FastAPI process used by the HTTP contract suite."""

from __future__ import annotations

import argparse
import os
from copy import deepcopy
from datetime import UTC, datetime
from typing import Any

import uvicorn
from bson import ObjectId

from gerec_api.auth.passwords import hash_password
from gerec_api.config import Settings
from gerec_api.domain.operations import OperationsService, TreatmentCommand, TreatmentResult
from gerec_api.infrastructure.mongo.operations_repository import OperationsStateError
from gerec_api.main import create_app


OWNER_ID = ObjectId("000000000000000000000002")
OTHER_SELLER_ID = ObjectId("000000000000000000000003")
LEAD_ID = ObjectId("000000000000000000000010")


class ContractOperationsService(OperationsService):
    """Minimal service double that makes the HTTP treatment contract executable."""

    def __init__(
        self,
        *,
        actor_id: ObjectId | None = None,
        actor_role: str | None = None,
        results: dict[str, TreatmentResult] | None = None,
    ) -> None:
        self._actor_id = actor_id
        self._actor_role = actor_role
        self._results = results if results is not None else {}

    def with_actor(self, actor_id: ObjectId, actor_role: str) -> "ContractOperationsService":
        return ContractOperationsService(
            actor_id=actor_id,
            actor_role=actor_role,
            results=self._results,
        )

    def register_treatment(self, command: TreatmentCommand) -> TreatmentResult:
        if self._actor_role != "seller" or self._actor_id != OWNER_ID:
            raise PermissionError("seller is not the current lead assignee")
        if command.lead_id != LEAD_ID:
            raise PermissionError("seller is not the current lead assignee")
        if command.idempotency_key == "contract-conflict":
            raise OperationsStateError("operation conflicted with a concurrent command")
        result = self._results.get(command.idempotency_key)
        if result is not None:
            return result
        result = TreatmentResult(
            lead_id=str(command.lead_id),
            treatment_id="000000000000000000000099",
            status="recorded",
            commercial_status=command.commercial_status,
            is_disqualified=command.is_disqualified,
            comment_count=1,
            last_updated_at=datetime(2026, 8, 28, 16, 3, 4, tzinfo=UTC),
            reminder_at=None,
            due_at=None,
        )
        self._results[command.idempotency_key] = result
        return result


class Cursor:
    def __init__(self, documents: list[dict[str, Any]]) -> None:
        self._documents = documents

    def sort(self, *_: Any) -> "Cursor":
        return self

    def skip(self, count: int) -> "Cursor":
        self._documents = self._documents[count:]
        return self

    def limit(self, count: int) -> "Cursor":
        self._documents = self._documents[:count]
        return self

    def __iter__(self):
        return iter(deepcopy(self._documents))


class Collection:
    def __init__(self) -> None:
        self.documents: list[dict[str, Any]] = []

    def insert_one(self, document: dict[str, Any], **_: Any) -> None:
        self.documents.append(deepcopy(document))

    def find_one(self, query: dict[str, Any], **_: Any) -> dict[str, Any] | None:
        return next((deepcopy(item) for item in self.documents if _matches(item, query)), None)

    def find(self, query: dict[str, Any], **_: Any) -> Cursor:
        return Cursor([item for item in self.documents if _matches(item, query)])

    def count_documents(self, query: dict[str, Any], **_: Any) -> int:
        return sum(_matches(item, query) for item in self.documents)

    def update_one(self, query: dict[str, Any], update: dict[str, Any], **_: Any) -> None:
        for item in self.documents:
            if _matches(item, query):
                item.update(deepcopy(update.get("$set", {})))
                return


class Database:
    def __init__(self) -> None:
        self._collections: dict[str, Collection] = {}

    def __getitem__(self, name: str) -> Collection:
        return self._collections.setdefault(name, Collection())


def _matches(document: dict[str, Any], query: dict[str, Any]) -> bool:
    for key, expected in query.items():
        actual = document.get(key)
        if isinstance(expected, dict):
            if "$gt" in expected and not actual > expected["$gt"]:
                return False
            if "$in" in expected and actual not in expected["$in"]:
                return False
        elif actual != expected:
            return False
    return True


def app():
    database = Database()
    user_id = ObjectId("000000000000000000000001")
    password_hash = hash_password(os.environ["CONTRACT_TEST_PASSWORD"])
    for account_id, email, role in (
        (user_id, "admin.contract@test", "admin"),
        (OWNER_ID, "seller.contract@test", "seller"),
        (OTHER_SELLER_ID, "other.contract@test", "seller"),
    ):
        database["users"].insert_one(
            {
                "_id": account_id,
                "emailNormalized": email,
                "passwordHash": password_hash,
                "role": role,
                "active": True,
                "createdAt": datetime(2026, 8, 28, tzinfo=UTC),
            }
        )
    settings = Settings(
        MONGODB_URI="mongodb://127.0.0.1:27017/?replicaSet=rs0",
        MONGODB_DATABASE="gerec_contracts",
        APP_SECRET=os.environ["CONTRACT_TEST_APP_SECRET"],
    )
    result = create_app(settings=settings, database=database)
    result.state.operations_service = ContractOperationsService()
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, required=True)
    args = parser.parse_args()
    uvicorn.run(app(), host="127.0.0.1", port=args.port, log_level="error")
