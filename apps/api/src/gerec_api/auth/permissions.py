"""Centralized authorization and read-scope policies for the API."""

from __future__ import annotations

from typing import Any, Mapping

from bson import ObjectId

from gerec_api.auth.sessions import CurrentUser
from gerec_api.infrastructure.mongo.collections import MongoCollections


class PermissionDenied(PermissionError):
    """Raised when a command or query is outside the current user's scope."""


class PermissionService:
    """Pure policy boundary; callers must provide the authenticated user."""

    @staticmethod
    def require_current_user(user: CurrentUser | None) -> CurrentUser:
        if not isinstance(user, CurrentUser) or not user.id or user.role not in {"admin", "seller"}:
            raise PermissionDenied("authenticated user is required")
        return user

    @classmethod
    def require_admin(cls, user: CurrentUser | None) -> None:
        current = cls.require_current_user(user)
        if current.role != "admin":
            raise PermissionDenied("administrator role is required")

    @classmethod
    def scope_query(cls, user: CurrentUser | None, resource: str) -> dict[str, Any]:
        """Return an immutable server-side Mongo filter for a read resource.

        Seller identity is always derived from the session. A caller cannot pass a
        seller id to widen this filter.
        """
        current = cls.require_current_user(user)
        if resource not in {
            "leads", "history", "queue", "skip_balance", "companies", "campaigns",
            "users", "audit",
        }:
            raise ValueError(f"unknown protected resource: {resource}")
        if current.role == "admin":
            return {}
        ids = _identity_values(current.id)
        if resource in {"leads", "companies"}:
            return {"$or": [{"assigneeId": {"$in": ids}}, {"historicalSellerIds": {"$in": ids}}]}
        if resource == "history":
            return {"sellerId": {"$in": ids}}
        if resource in {"queue", "skip_balance"}:
            return {"sellerId": {"$in": ids}}
        # Sellers must not receive user, campaign or audit data.
        raise PermissionDenied(f"seller cannot read {resource}")


class DashboardService:
    """Paginated dashboard reads with scope applied before every collection query."""

    def __init__(self, database: Any, *, page_size: int = 50) -> None:
        self._database = database
        self._page_size = max(1, min(page_size, 200))

    def for_user(self, user: CurrentUser | None) -> dict[str, Any]:
        current = PermissionService.require_current_user(user)
        leads = self._page(MongoCollections.LEADS, PermissionService.scope_query(current, "leads"))
        history = self._page(
            MongoCollections.ASSIGNMENTS,
            PermissionService.scope_query(current, "history"),
        )
        queue = self._page(
            MongoCollections.SELLER_QUEUE,
            PermissionService.scope_query(current, "queue"),
        )
        balance = self._first(
            MongoCollections.SKIP_BALANCES,
            PermissionService.scope_query(current, "skip_balance"),
        )
        return {
            "user": {"id": current.id, "email": current.email, "role": current.role},
            "leads": leads,
            "history": history,
            "queue": queue,
            "skipBalance": balance,
        }

    def _page(self, collection_name: str, query: Mapping[str, Any]) -> dict[str, Any]:
        collection = self._database[collection_name]
        cursor = collection.find(dict(query))
        if hasattr(cursor, "sort"):
            cursor = cursor.sort("createdAt", -1)
        if hasattr(cursor, "skip"):
            cursor = cursor.skip(0)
        if hasattr(cursor, "limit"):
            cursor = cursor.limit(self._page_size)
        items = [_public_document(item) for item in cursor]
        total = collection.count_documents(dict(query)) if hasattr(collection, "count_documents") else len(items)
        return {"items": items, "page": 1, "pageSize": self._page_size, "total": total}

    def _first(self, collection_name: str, query: Mapping[str, Any]) -> dict[str, Any] | None:
        item = self._database[collection_name].find_one(dict(query))
        return _public_document(item) if item is not None else None


def _identity_values(value: str) -> list[Any]:
    values: list[Any] = [value]
    if ObjectId.is_valid(value):
        values.append(ObjectId(value))
    return values


def _public_document(document: Mapping[str, Any]) -> dict[str, Any]:
    result = dict(document)
    if "_id" in result:
        result["id"] = str(result.pop("_id"))
    return result
