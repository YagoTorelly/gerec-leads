"""Administrative read endpoints and thin user-command HTTP boundaries."""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from pydantic import BaseModel, Field

from gerec_api.auth.dependencies import get_current_user
from gerec_api.auth.permissions import PermissionDenied, PermissionService
from gerec_api.auth.sessions import CurrentUser
from gerec_api.domain.manual_leads import ManualLeadCommand, ManualLeadResult, ManualLeadService
from gerec_api.domain.queue import QueueService
from gerec_api.infrastructure.mongo.clock import MongoClock
from gerec_api.infrastructure.mongo.collections import MongoCollections
from gerec_api.infrastructure.mongo.serialization import serialize_bson
from gerec_api.domain.user_administration import (
    CreateUserCommand,
    ManagedUser,
    UserAdministrationError,
    UserAdministrationService,
    UserAlreadyExistsError,
    UserNotFoundError,
)


router = APIRouter(prefix="/api/admin", tags=["admin"])
SENSITIVE_FIELDS = frozenset({"passwordHash", "tokenHash"})


def _admin(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    try:
        PermissionService.require_admin(user)
    except PermissionDenied as error:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden") from error
    return user


class CreateUserRequest(BaseModel):
    full_name: str = Field(alias="fullName", min_length=1, max_length=200)
    email: str = Field(min_length=1, max_length=320)
    role: str
    password: str


class AvailabilityRequest(BaseModel):
    paused: bool


class PasswordResetRequest(BaseModel):
    password: str


class ManualLeadRequest(BaseModel):
    name: str = Field(min_length=1)
    email: str = Field(min_length=1)
    phone: str = Field(min_length=1)
    campaign: str | None = None
    source: str | None = None


class ManualLeadResponse(BaseModel):
    lead_id: str = Field(alias="leadId")
    manual_queue_lead_id: str = Field(alias="manualQueueLeadId")
    assignee_id: str | None = Field(alias="assigneeId")
    assigned_at: datetime | None = Field(alias="assignedAt")
    commercial_status: str = Field(alias="commercialStatus")
    source: str

    model_config = {"populate_by_name": True}


class ManagedUserResponse(BaseModel):
    id: str
    full_name: str = Field(alias="fullName")
    email: str
    role: str
    active: bool
    paused: bool | None = None

    model_config = {"populate_by_name": True}


def _user_administration_service(request: Request) -> UserAdministrationService:
    service = getattr(request.app.state, "user_administration_service", None)
    if not isinstance(service, UserAdministrationService):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="User administration unavailable",
        )
    return service


def _manual_lead_service(request: Request) -> ManualLeadService:
    service = getattr(request.app.state, "manual_lead_service", None)
    if not isinstance(service, ManualLeadService):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Manual lead service unavailable",
        )
    return service


def _queue_service(request: Request) -> QueueService:
    service = getattr(request.app.state, "queue_service", None)
    if not isinstance(service, QueueService):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Queue service unavailable",
        )
    return service


def _database_clock(request: Request) -> MongoClock:
    clock = getattr(request.app.state, "database_clock", None)
    if not isinstance(clock, MongoClock):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database clock unavailable",
        )
    return clock


def _response(user: ManagedUser) -> ManagedUserResponse:
    return ManagedUserResponse.model_validate(user.to_public())


def _command_error(error: UserAdministrationError | ValueError) -> HTTPException:
    if isinstance(error, UserAlreadyExistsError):
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    if isinstance(error, UserNotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error))


def _manual_response(result: ManualLeadResult) -> ManualLeadResponse:
    return ManualLeadResponse.model_validate(result.to_document())


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
        for field in SENSITIVE_FIELDS:
            item.pop(field, None)
        items.append(serialize_bson(item))
    total = collection.count_documents(query) if hasattr(collection, "count_documents") else len(items)
    return {"items": items, "page": page, "pageSize": limit, "total": total}


@router.get("/users")
def users(request: Request, current_user: CurrentUser = Depends(_admin), page: int = Query(1, ge=1), limit: int = Query(50, ge=1, le=200)) -> dict[str, Any]:
    return _page(request, current_user, MongoCollections.USERS, PermissionService.scope_query(current_user, "users"), page, limit)


@router.post("/users", response_model=ManagedUserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: CreateUserRequest,
    request: Request,
    current_user: CurrentUser = Depends(_admin),
) -> ManagedUserResponse:
    try:
        user = _user_administration_service(request).with_actor(current_user.id).create_user(
            CreateUserCommand(payload.full_name, payload.email, payload.role, payload.password)
        )
    except (UserAdministrationError, ValueError) as error:
        raise _command_error(error) from error
    return _response(user)


@router.post(
    "/leads/manual",
    response_model=ManualLeadResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_manual_lead(
    payload: ManualLeadRequest,
    request: Request,
    idempotency_key: str = Header(
        ...,
        alias="Idempotency-Key",
        min_length=1,
        max_length=200,
    ),
    current_user: CurrentUser = Depends(_admin),
) -> ManualLeadResponse:
    try:
        result = _manual_lead_service(request).create_manual_lead(
            current_user,
            ManualLeadCommand(
                name=payload.name,
                email=payload.email,
                phone=payload.phone,
                campaign=payload.campaign,
                source=payload.source,
                idempotency_key=idempotency_key,
                original_payload={
                    "name": payload.name,
                    "email": payload.email,
                    "phone": payload.phone,
                    "campaign": payload.campaign,
                    "source": payload.source,
                },
            ),
            _database_clock(request).now(),
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error),
        ) from error
    return _manual_response(result)


@router.patch("/users/{user_id}/availability", response_model=ManagedUserResponse)
def set_user_availability(
    user_id: str,
    payload: AvailabilityRequest,
    request: Request,
    current_user: CurrentUser = Depends(_admin),
) -> ManagedUserResponse:
    try:
        user = _user_administration_service(request).with_actor(current_user.id).set_manual_pause(
            user_id, payload.paused
        )
    except (UserAdministrationError, ValueError) as error:
        raise _command_error(error) from error
    if payload.paused is False:
        _queue_service(request).with_actor(current_user.id).reconcile_pending_manual(
            f"admin:user:{user_id}:reactivated:manual"
        )
    return _response(user)


@router.patch("/users/{user_id}/password", response_model=ManagedUserResponse)
def reset_user_password(
    user_id: str,
    payload: PasswordResetRequest,
    request: Request,
    current_user: CurrentUser = Depends(_admin),
) -> ManagedUserResponse:
    try:
        user = _user_administration_service(request).with_actor(current_user.id).reset_password(
            user_id, payload.password
        )
    except (UserAdministrationError, ValueError) as error:
        raise _command_error(error) from error
    return _response(user)


@router.get("/audit")
def audit(request: Request, current_user: CurrentUser = Depends(_admin), page: int = Query(1, ge=1), limit: int = Query(50, ge=1, le=200)) -> dict[str, Any]:
    return _page(request, current_user, MongoCollections.AUDIT_LOG, PermissionService.scope_query(current_user, "audit"), page, limit)
