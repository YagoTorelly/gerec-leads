"""Small domain interface for idempotent lead ingestion and source snapshots."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Protocol

from gerec_api.domain.normalization import NormalizedSourceRow, normalize_source_row


@dataclass(frozen=True)
class ImportResult:
    status: str
    source_record_id: str
    lead_id: str | None
    pending_reasons: tuple[str, ...] = ()
    assignment_status: str | None = None

    def to_document(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "sourceRecordId": self.source_record_id,
            "leadId": self.lead_id,
            "pendingReasons": list(self.pending_reasons),
            "assignmentStatus": self.assignment_status,
        }

    @classmethod
    def from_document(cls, value: Mapping[str, Any]) -> "ImportResult":
        return cls(
            status=str(value["status"]),
            source_record_id=str(value["sourceRecordId"]),
            lead_id=str(value["leadId"]) if value.get("leadId") is not None else None,
            pending_reasons=tuple(str(item) for item in value.get("pendingReasons", [])),
            assignment_status=(
                str(value["assignmentStatus"])
                if value.get("assignmentStatus") is not None
                else None
            ),
        )


@dataclass(frozen=True)
class ArchiveResult:
    source_snapshot_id: str
    archived_source_records: int
    archived_leads: int

    def to_document(self) -> dict[str, Any]:
        return {
            "sourceSnapshotId": self.source_snapshot_id,
            "archivedSourceRecords": self.archived_source_records,
            "archivedLeads": self.archived_leads,
        }

    @classmethod
    def from_document(cls, value: Mapping[str, Any]) -> "ArchiveResult":
        return cls(
            source_snapshot_id=str(value["sourceSnapshotId"]),
            archived_source_records=int(value["archivedSourceRecords"]),
            archived_leads=int(value["archivedLeads"]),
        )


class LeadPersistence(Protocol):
    def import_row(self, row: NormalizedSourceRow, idempotency_key: str) -> ImportResult: ...

    def archive_missing(self, source_snapshot_id: str) -> ArchiveResult: ...


class LeadService:
    """Expose the complete ingestion workflow through two commands."""

    def __init__(self, persistence: LeadPersistence) -> None:
        self._persistence = persistence

    def import_row(
        self,
        row: NormalizedSourceRow | Mapping[str, Any],
        idempotency_key: str,
    ) -> ImportResult:
        normalized = row if isinstance(row, NormalizedSourceRow) else normalize_source_row(row)
        if not idempotency_key.strip():
            raise ValueError("idempotency key is required")
        return self._persistence.import_row(normalized, idempotency_key.strip())

    def archive_missing(self, source_snapshot_id: str) -> ArchiveResult:
        if not source_snapshot_id.strip():
            raise ValueError("source snapshot id is required")
        return self._persistence.archive_missing(source_snapshot_id.strip())
