"""Seller-only HTTP boundaries for internal new-lead notification windows."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel

from gerec_api.auth.dependencies import get_current_user
from gerec_api.auth.sessions import CurrentUser
from gerec_api.domain.lead_notifications import LeadNotificationService
from gerec_api.infrastructure.mongo.lead_notification_repository import LeadNotificationStateError


router = APIRouter(tags=["lead-notifications"])


class AcknowledgeNewLeadNotificationsRequest(BaseModel):
    watermark: datetime


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
    service: LeadNotificationService = Depends(get_lead_notification_service),
    current_user: CurrentUser = Depends(get_current_user),
) -> dict[str, object]:
    return _snapshot(service, current_user)


@router.post("/api/lead-notifications/new/acknowledge")
def acknowledge_new_lead_notifications(
    payload: AcknowledgeNewLeadNotificationsRequest,
    service: LeadNotificationService = Depends(get_lead_notification_service),
    current_user: CurrentUser = Depends(get_current_user),
) -> dict[str, str]:
    _require_seller(current_user)
    try:
        watermark = service.acknowledge(current_user, payload.watermark)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)) from error
    except LeadNotificationStateError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error
    return {"watermark": watermark.isoformat()}


def _snapshot(service: LeadNotificationService, current_user: CurrentUser) -> dict[str, object]:
    _require_seller(current_user)
    try:
        return service.for_seller(current_user).to_document()
    except LeadNotificationStateError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error


def _require_seller(user: CurrentUser) -> None:
    if user.role != "seller":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
