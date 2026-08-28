"""Authenticated, paginated dashboard read endpoints."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status

from gerec_api.auth.dependencies import get_current_user
from gerec_api.auth.permissions import DashboardService, PermissionDenied
from gerec_api.auth.sessions import CurrentUser


router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


def get_dashboard_service(request: Request) -> DashboardService:
    service = getattr(request.app.state, "dashboard_service", None)
    if not isinstance(service, DashboardService):
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Dashboard service unavailable")
    return service


@router.get("")
def dashboard(
    current_user: CurrentUser = Depends(get_current_user),
    service: DashboardService = Depends(get_dashboard_service),
) -> dict[str, Any]:
    try:
        return service.for_user(current_user)
    except PermissionDenied as error:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden") from error
