"""Idempotent full-snapshot synchronization for Railway jobs."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from gerec_api.automation.workbook_adapter import WorkbookAdapter
from gerec_api.config import Settings
from gerec_api.domain.leads import LeadService
from gerec_api.domain.normalization import NormalizedSourceRow, normalize_source_row
from gerec_api.infrastructure.mongo.client import MongoClientFactory
from gerec_api.infrastructure.mongo.lead_repository import LeadRepository


@dataclass(frozen=True)
class SyncResult:
    """Observable summary of one complete, replay-safe source snapshot."""

    run_id: str
    read_rows: int
    created: int
    updated: int
    ignored: int
    pending: int
    archived_source_records: int
    archived_leads: int


class SyncJob:
    """Keep ingestion in the existing domain service; never assign leads directly."""

    def __init__(self, lead_service: LeadService) -> None:
        self._lead_service = lead_service

    def run(self, source: Any, run_id: str) -> SyncResult:
        snapshot_id = run_id.strip()
        if not snapshot_id:
            raise ValueError("run_id is required")

        counts = {"created": 0, "updated": 0, "ignored": 0, "pending": 0}
        read_rows = 0
        for raw_row in self._rows(source):
            row = raw_row if isinstance(raw_row, NormalizedSourceRow) else normalize_source_row(raw_row)
            row = replace(row, source_snapshot_id=snapshot_id)
            result = self._lead_service.import_row(
                row,
                f"sync:{snapshot_id}:{row.source_lead_id}",
            )
            read_rows += 1
            if result.status in counts:
                counts[result.status] += 1

        archive = self._lead_service.archive_missing(snapshot_id)
        return SyncResult(
            run_id=snapshot_id,
            read_rows=read_rows,
            created=counts["created"],
            updated=counts["updated"],
            ignored=counts["ignored"],
            pending=counts["pending"],
            archived_source_records=archive.archived_source_records,
            archived_leads=archive.archived_leads,
        )

    @staticmethod
    def _rows(source: Any) -> Iterable[NormalizedSourceRow | dict[str, Any]]:
        if isinstance(source, (str, Path)):
            return WorkbookAdapter().read(Path(source))
        if hasattr(source, "read"):
            return source.read()
        return source


def run_sync(source: Any, run_id: str) -> SyncResult:
    """Railway entry point; credentials stay in the Python process environment."""
    settings = Settings.from_env()
    database = MongoClientFactory.create(settings)
    return SyncJob(LeadService(LeadRepository(database))).run(source, run_id)
