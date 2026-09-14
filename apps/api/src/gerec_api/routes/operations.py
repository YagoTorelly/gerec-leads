"""HTTP boundaries for seller operational commands."""

from datetime import date
from typing import Any, Callable, Literal

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
    TreatmentCommand,
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
    response_confirmed: bool = False


class TreatmentRequest(BaseModel):
    comment: str = Field(min_length=6, max_length=2_000)
    commercial_status: Literal["undefined", "potential", "negotiation", "won"] = Field(
        alias="commercialStatus"
    )
    is_disqualified: bool = Field(alias="isDisqualified")
    idempotency_key: str = Field(alias="idempotencyKey", min_length=1, max_length=200)


def get_operations_service(request: Request) -> OperationsService:
    service = getattr(request.app.state, "operations_service", None)
    if not isinstance(service, OperationsService):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Operations service unavailable",
        )
    return service


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


@router.post(
    "/api/leads/{lead_id}/treatments",
    status_code=status.HTTP_201_CREATED,
)
def register_treatment(
    lead_id: str,
    payload: TreatmentRequest,
    service: OperationsService = Depends(get_operations_service),
    current_user: CurrentUser = Depends(get_current_user),
) -> dict[str, Any]:
    """Record the current seller's immutable commercial treatment only."""
    if current_user.role != "seller":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return _run_treatment(
        lambda: service.with_actor(
            _object_id(current_user.id), current_user.role
        ).register_treatment(
            TreatmentCommand(
                _object_id(lead_id),
                payload.comment,
                payload.commercial_status,
                payload.is_disqualified,
                payload.idempotency_key,
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
                payload.response_confirmed,
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


def _run_treatment(operation: Callable[[], Any]) -> dict[str, Any]:
    try:
        return operation().to_document()
    except PermissionError as error:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden") from error
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)
        ) from error
    except OperationsStateError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error
