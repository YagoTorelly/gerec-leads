"""Administrative report endpoints backed by the protected dashboard service."""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from gerec_api.auth.dependencies import get_current_user
from gerec_api.auth.permissions import DashboardService, PermissionDenied
from gerec_api.auth.sessions import CurrentUser


router = APIRouter(prefix="/api/admin/reports", tags=["reports"])


def get_dashboard_service(request: Request) -> DashboardService:
    service = getattr(request.app.state, "dashboard_service", None)
    if not isinstance(service, DashboardService):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Dashboard service unavailable",
        )
    return service


def _admin(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return current_user


@router.get("/lead-distribution")
def lead_distribution(
    current_user: CurrentUser = Depends(_admin),
    service: DashboardService = Depends(get_dashboard_service),
    from_at: datetime = Query(alias="fromAt"),
    to_at: datetime = Query(alias="toAt"),
) -> dict[str, Any]:
    try:
        return service.lead_distribution(current_user, from_at=from_at, to_at=to_at)
    except PermissionDenied as error:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden") from error
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)) from error
