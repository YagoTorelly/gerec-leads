"""Seller-only HTTP boundaries for internal new-lead notification windows."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from gerec_api.auth.dependencies import SESSION_COOKIE_NAME, get_current_user
from gerec_api.auth.sessions import CurrentUser
from gerec_api.domain.lead_notifications import LeadNotificationService
from gerec_api.infrastructure.mongo.lead_notification_repository import LeadNotificationStateError


router = APIRouter(tags=["lead-notifications"])


class AcknowledgeNewLeadNotificationsRequest(BaseModel):
    watermark: datetime
    acknowledgement_token: str = Field(alias="acknowledgementToken", min_length=1, max_length=200)
    watermark_sequence: int = Field(alias="watermarkSequence", ge=0)


def get_lead_notification_service(request: Request) -> LeadNotificationService:
    service = getattr(request.app.state, "lead_notification_service", None)
    if not isinstance(service, LeadNotificationService):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Lead notification service unavailable",
        )
    return service


@router.get("/api/lead-notifications/new")
def new_lead_notifications(
    request: Request,
    service: LeadNotificationService = Depends(get_lead_notification_service),
    current_user: CurrentUser = Depends(get_current_user),
) -> dict[str, object]:
    return _snapshot(service, current_user, _session_token(request))


@router.post("/api/lead-notifications/new/acknowledge")
def acknowledge_new_lead_notifications(
    request: Request,
    payload: AcknowledgeNewLeadNotificationsRequest,
    service: LeadNotificationService = Depends(get_lead_notification_service),
    current_user: CurrentUser = Depends(get_current_user),
) -> dict[str, str]:
    _require_seller(current_user)
    try:
        watermark = service.acknowledge(
            current_user,
            payload.watermark,
            payload.acknowledgement_token,
            _session_token(request),
            payload.watermark_sequence,
        )
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)) from error
    except LeadNotificationStateError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error
    return {"watermark": watermark.isoformat()}


def _snapshot(
    service: LeadNotificationService,
    current_user: CurrentUser,
    session_token: str,
) -> dict[str, object]:
    _require_seller(current_user)
    try:
        return service.for_seller(current_user, session_token).to_document()
    except LeadNotificationStateError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error


def _require_seller(user: CurrentUser) -> None:
    if user.role != "seller":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")


def _session_token(request: Request) -> str:
    return request.cookies.get(SESSION_COOKIE_NAME, "")
