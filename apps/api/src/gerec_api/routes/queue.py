"""HTTP boundaries for internal distribution and administrative queue commands."""

from typing import Any

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from gerec_api.auth.dependencies import get_current_user
from gerec_api.auth.sessions import CurrentUser
from gerec_api.domain.queue import QueueService
from gerec_api.infrastructure.mongo.queue_repository import QueueStateError
from gerec_api.routes.leads import require_internal_key


router = APIRouter(tags=["queue"])


class CommandRequest(BaseModel):
    command_id: str = Field(min_length=1, max_length=200)


class TemporaryAssignmentRequest(CommandRequest):
    seller_id: str
    reason: str = Field(min_length=1, max_length=2_000)


class TransferOwnerRequest(CommandRequest):
    seller_id: str
    reason: str = Field(min_length=1, max_length=2_000)
    confirmed: bool


def get_queue_service(request: Request) -> QueueService:
    service = getattr(request.app.state, "queue_service", None)
    if not isinstance(service, QueueService):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Queue service unavailable",
        )
    return service


def require_admin(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return current_user


@router.post(
    "/api/internal/queue/leads/{lead_id}/distribute-normal",
    dependencies=[Depends(require_internal_key)],
)
def distribute_normal(
    lead_id: str,
    payload: CommandRequest,
    service: QueueService = Depends(get_queue_service),
) -> dict[str, Any]:
    return _run(
        lambda: service.with_actor("system").distribute_normal(
            _object_id(lead_id), payload.command_id
        )
    )


@router.post(
    "/api/internal/queue/leads/{lead_id}/assign-recurring",
    dependencies=[Depends(require_internal_key)],
)
def assign_recurring(
    lead_id: str,
    payload: CommandRequest,
    service: QueueService = Depends(get_queue_service),
) -> dict[str, Any]:
    return _run(
        lambda: service.with_actor("system").assign_recurring(
            _object_id(lead_id), payload.command_id
        )
    )


@router.post(
    "/api/admin/leads/{lead_id}/temporary-assignment",
)
def assign_temporarily(
    lead_id: str,
    payload: TemporaryAssignmentRequest,
    service: QueueService = Depends(get_queue_service),
    current_user: CurrentUser = Depends(require_admin),
) -> dict[str, Any]:
    return _run(
        lambda: service.with_actor(_object_id(current_user.id)).assign_temporarily(
            _object_id(lead_id),
            _object_id(payload.seller_id),
            payload.reason,
            payload.command_id,
        )
    )


@router.post(
    "/api/admin/companies/{company_id}/transfer-owner",
)
def transfer_owner(
    company_id: str,
    payload: TransferOwnerRequest,
    service: QueueService = Depends(get_queue_service),
    current_user: CurrentUser = Depends(require_admin),
) -> dict[str, Any]:
    if payload.confirmed is not True:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Permanent owner transfer requires explicit confirmation",
        )
    return _run(
        lambda: service.with_actor(_object_id(current_user.id)).transfer_owner(
            _object_id(company_id),
            _object_id(payload.seller_id),
            payload.reason,
            payload.command_id,
        )
    )


def _object_id(value: str) -> ObjectId:
    try:
        return ObjectId(value)
    except InvalidId as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid object id",
        ) from error


def _run(operation):
    try:
        return operation().to_document()
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)) from error
    except QueueStateError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error
