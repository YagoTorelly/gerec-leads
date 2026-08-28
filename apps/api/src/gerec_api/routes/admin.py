"""Administrative read endpoints; mutations remain explicit domain commands."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status

from gerec_api.auth.dependencies import get_current_user
from gerec_api.auth.permissions import PermissionDenied, PermissionService
from gerec_api.auth.sessions import CurrentUser
from gerec_api.infrastructure.mongo.collections import MongoCollections


router = APIRouter(prefix="/api/admin", tags=["admin"])


def _admin(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    try:
        PermissionService.require_admin(user)
    except PermissionDenied as error:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden") from error
    return user


def _page(request: Request, collection_name: str, query: dict[str, Any] | None = None) -> dict[str, Any]:
    query = query or {}
    collection = request.app.state.database[collection_name]
    cursor = collection.find(query)
    if hasattr(cursor, "sort"):
        cursor = cursor.sort("createdAt", -1)
    if hasattr(cursor, "limit"):
        cursor = cursor.limit(50)
    items = []
    for item in cursor:
        item = dict(item)
        if "_id" in item:
            item["id"] = str(item.pop("_id"))
        items.append(item)
    total = collection.count_documents(query) if hasattr(collection, "count_documents") else len(items)
    return {"items": items, "page": 1, "pageSize": 50, "total": total}


@router.get("/users")
def users(request: Request, _: CurrentUser = Depends(_admin)) -> dict[str, Any]:
    return _page(request, MongoCollections.USERS)


@router.get("/audit")
def audit(request: Request, _: CurrentUser = Depends(_admin)) -> dict[str, Any]:
    return _page(request, MongoCollections.AUDIT_LOG)
