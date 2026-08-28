"""HTTP boundaries for seller operations and administrative notes."""

from datetime import date
from typing import Any, Callable

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from gerec_api.auth.dependencies import get_current_user
from gerec_api.auth.sessions import CurrentUser
from gerec_api.domain.operations import (
    AttemptCommand,
    FeedbackCommand,
    OperationsService,
    OutcomeCommand,
)
from gerec_api.infrastructure.mongo.operations_repository import OperationsStateError


router = APIRouter(tags=["operations"])


class FeedbackRequest(BaseModel):
    comment: str = Field(min_length=1, max_length=2_000)
    contact_started: bool
    idempotency_key: str = Field(min_length=1, max_length=200)


class AttemptRequest(BaseModel):
    comment: str = Field(min_length=1, max_length=2_000)
    idempotency_key: str = Field(min_length=1, max_length=200)
    business_date: date | None = None


class OutcomeRequest(BaseModel):
    outcome: str
    comment: str = Field(min_length=1, max_length=2_000)
    idempotency_key: str = Field(min_length=1, max_length=200)
    disqualification_reason: str | None = None


class AdministrativeNoteRequest(BaseModel):
    comment: str = Field(min_length=1, max_length=2_000)
    idempotency_key: str = Field(min_length=1, max_length=200)


def get_operations_service(request: Request) -> OperationsService:
    service = getattr(request.app.state, "operations_service", None)
    if not isinstance(service, OperationsService):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Operations service unavailable",
        )
    return service


def require_admin(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return current_user


@router.post("/api/leads/{lead_id}/feedbacks")
def register_feedback(
    lead_id: str,
    payload: FeedbackRequest,
    service: OperationsService = Depends(get_operations_service),
    current_user: CurrentUser = Depends(get_current_user),
) -> dict[str, Any]:
    return _run(
        lambda: service.with_actor(_object_id(current_user.id), current_user.role).register_feedback(
            FeedbackCommand(
                _object_id(lead_id),
                payload.comment,
                payload.contact_started,
                payload.idempotency_key,
            )
        )
    )


@router.post("/api/leads/{lead_id}/attempts")
def register_attempt(
    lead_id: str,
    payload: AttemptRequest,
    service: OperationsService = Depends(get_operations_service),
    current_user: CurrentUser = Depends(get_current_user),
) -> dict[str, Any]:
    return _run(
        lambda: service.with_actor(_object_id(current_user.id), current_user.role).register_attempt(
            AttemptCommand(
                _object_id(lead_id),
                payload.comment,
                payload.idempotency_key,
                payload.business_date,
            )
        )
    )


@router.post("/api/leads/{lead_id}/outcome")
def register_outcome(
    lead_id: str,
    payload: OutcomeRequest,
    service: OperationsService = Depends(get_operations_service),
    current_user: CurrentUser = Depends(get_current_user),
) -> dict[str, Any]:
    return _run(
        lambda: service.with_actor(_object_id(current_user.id), current_user.role).register_outcome(
            OutcomeCommand(
                _object_id(lead_id),
                payload.outcome,
                payload.comment,
                payload.idempotency_key,
                payload.disqualification_reason,
            )
        )
    )


@router.post("/api/admin/leads/{lead_id}/notes")
def register_administrative_note(
    lead_id: str,
    payload: AdministrativeNoteRequest,
    service: OperationsService = Depends(get_operations_service),
    current_user: CurrentUser = Depends(require_admin),
) -> dict[str, Any]:
    return _run(
        lambda: service.with_actor(_object_id(current_user.id), current_user.role).register_feedback(
            FeedbackCommand(
                _object_id(lead_id),
                payload.comment,
                False,
                payload.idempotency_key,
                administrative_note=True,
            )
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


def _run(operation: Callable[[], Any]) -> dict[str, Any]:
    try:
        return operation().to_document()
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)
        ) from error
    except OperationsStateError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error
