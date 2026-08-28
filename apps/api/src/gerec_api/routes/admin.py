"""Administrative read endpoints; mutations remain explicit domain commands."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

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


def _page(request: Request, current_user: CurrentUser, collection_name: str, query: dict[str, Any], page: int, limit: int) -> dict[str, Any]:
    PermissionService.require_admin(current_user)
    if query is None:
        raise PermissionDenied("scoped query is required")
    collection = request.app.state.database[collection_name]
    cursor = collection.find(query)
    if hasattr(cursor, "sort"):
        cursor = cursor.sort("createdAt", -1)
    if hasattr(cursor, "limit"):
        cursor = cursor.skip((page - 1) * limit).limit(limit)
    items = []
    for item in cursor:
        item = dict(item)
        if "_id" in item:
            item["id"] = str(item.pop("_id"))
        items.append(item)
    total = collection.count_documents(query) if hasattr(collection, "count_documents") else len(items)
    return {"items": items, "page": page, "pageSize": limit, "total": total}


@router.get("/users")
def users(request: Request, current_user: CurrentUser = Depends(_admin), page: int = Query(1, ge=1), limit: int = Query(50, ge=1, le=200)) -> dict[str, Any]:
    return _page(request, current_user, MongoCollections.USERS, PermissionService.scope_query(current_user, "users"), page, limit)


@router.get("/audit")
def audit(request: Request, current_user: CurrentUser = Depends(_admin), page: int = Query(1, ge=1), limit: int = Query(50, ge=1, le=200)) -> dict[str, Any]:
    return _page(request, current_user, MongoCollections.AUDIT_LOG, PermissionService.scope_query(current_user, "audit"), page, limit)
