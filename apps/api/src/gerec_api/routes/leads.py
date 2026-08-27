"""Internal authenticated routes for source-row ingestion and snapshot finalization."""

from dataclasses import replace
from hmac import compare_digest
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from pydantic import BaseModel, Field

from gerec_api.domain.leads import LeadService
from gerec_api.domain.normalization import normalize_source_row


router = APIRouter(prefix="/api/internal/imports/google-sheets", tags=["lead-imports"])


class SyncRequest(BaseModel):
    source_snapshot_id: str = Field(min_length=1, max_length=200)
    idempotency_key: str = Field(min_length=1, max_length=200)
    rows: list[dict[str, Any]]


def get_lead_service(request: Request) -> LeadService:
    service = getattr(request.app.state, "lead_service", None)
    if not isinstance(service, LeadService):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Lead import service unavailable",
        )
    return service


def require_internal_key(
    request: Request,
    x_internal_key: str = Header(alias="X-Internal-Key"),
) -> None:
    expected = request.app.state.settings.app_secret.get_secret_value()
    if not compare_digest(x_internal_key, expected):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")


@router.post("/sync", dependencies=[Depends(require_internal_key)])
def sync_rows(
    payload: SyncRequest,
    service: LeadService = Depends(get_lead_service),
) -> dict[str, Any]:
    """Import every row before finalizing the complete snapshot and archiving absences."""
    results = []
    for raw_row in payload.rows:
        row = replace(
            normalize_source_row(raw_row),
            source_snapshot_id=payload.source_snapshot_id,
        )
        results.append(
            service.import_row(
                row,
                f"{payload.idempotency_key}:{row.source_lead_id}",
            ).to_document()
        )
    archive = service.archive_missing(payload.source_snapshot_id)
    return {"rows": results, "archive": archive.to_document()}
