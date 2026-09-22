"""Idempotent full-snapshot synchronization for Railway jobs."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from uuid import uuid4
from bson import ObjectId

from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError

from gerec_api.automation.workbook_adapter import WorkbookAdapter
from gerec_api.config import Settings
from gerec_api.domain.leads import LeadService
from gerec_api.domain.queue import QueueService
from gerec_api.domain.normalization import NormalizedSourceRow, normalize_source_row
from gerec_api.infrastructure.mongo.client import MongoClientFactory
from gerec_api.infrastructure.mongo.lead_repository import LeadRepository
from gerec_api.infrastructure.mongo.queue_repository import QueueRepository
from gerec_api.infrastructure.mongo.collections import MongoCollections


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
    skipped: bool = False


@dataclass(frozen=True)
class SyncLease:
    run_id: str
    claim_token: str
    generation: int


class SyncLeaseLostError(RuntimeError):
    """Raised when a newer synchronization owns the source fence."""


class SyncLeaseRepository:
    def claim(self, run_id: str, now: datetime) -> SyncLease | None: ...

    def heartbeat(self, lease: SyncLease, now: datetime) -> bool: ...

    def finish(self, lease: SyncLease, now: datetime, *, succeeded: bool) -> bool: ...


class InMemorySyncLeaseRepository(SyncLeaseRepository):
    """Deterministic fence for tests; Railway composes the Mongo implementation."""

    def __init__(self) -> None:
        self._current: SyncLease | None = None
        self._generation = 0

    def claim(self, run_id: str, now: datetime) -> SyncLease | None:
        if self._current is not None:
            return None
        self._generation += 1
        self._current = SyncLease(run_id, uuid4().hex, self._generation)
        return self._current

    def heartbeat(self, lease: SyncLease, now: datetime) -> bool:
        return self._current == lease

    def finish(self, lease: SyncLease, now: datetime, *, succeeded: bool) -> bool:
        if self._current != lease:
            return False
        self._current = None
        return True

    def invalidate_current(self) -> None:
        self._current = None


class MongoSyncLeaseRepository(SyncLeaseRepository):
    """Generation fence for full snapshots, persisted with Railway scheduler locks."""

    _LEASE_ID = "source_sync"

    def __init__(self, database: Any, *, lease_seconds: int = 600) -> None:
        self._locks = database[MongoCollections.AUTOMATION_JOB_LOCKS]
        self._lease_seconds = lease_seconds

    def claim(self, run_id: str, now: datetime) -> SyncLease | None:
        token = uuid4().hex
        try:
            document = self._locks.find_one_and_update(
                {
                    "_id": self._LEASE_ID,
                    "$or": [{"lockedUntil": {"$lte": now}}, {"lockedUntil": {"$exists": False}}],
                },
                {
                    "$set": {"runId": run_id, "claimToken": token, "lockedUntil": now + timedelta(seconds=self._lease_seconds)},
                    "$inc": {"generation": 1},
                    "$setOnInsert": {"createdAt": now},
                },
                upsert=True,
                return_document=ReturnDocument.AFTER,
            )
        except DuplicateKeyError:
            return None
        if document is None:
            return None
        return SyncLease(run_id, token, int(document["generation"]))

    def heartbeat(self, lease: SyncLease, now: datetime) -> bool:
        result = self._locks.update_one(
            {"_id": self._LEASE_ID, "claimToken": lease.claim_token, "generation": lease.generation},
            {"$set": {"lockedUntil": now + timedelta(seconds=self._lease_seconds)}},
        )
        return result.matched_count == 1

    def finish(self, lease: SyncLease, now: datetime, *, succeeded: bool) -> bool:
        result = self._locks.update_one(
            {"_id": self._LEASE_ID, "claimToken": lease.claim_token, "generation": lease.generation},
            {
                "$set": {"lastRunAt": now, "lastStatus": "succeeded" if succeeded else "failed"},
                "$unset": {"runId": "", "claimToken": "", "lockedUntil": ""},
            },
        )
        return result.matched_count == 1


class SyncJob:
    """Keep ingestion in the existing domain service; never assign leads directly."""

    def __init__(
        self,
        lead_service: LeadService,
        *,
        queue_service: QueueService | Any | None = None,
        leases: SyncLeaseRepository | None = None,
    ) -> None:
        self._lead_service = lead_service
        self._queue_service = queue_service
        self._leases = leases

    def run(self, source: Any, run_id: str) -> SyncResult:
        snapshot_id = run_id.strip()
        if not snapshot_id:
            raise ValueError("run_id is required")

        lease = self._leases.claim(snapshot_id, datetime.now(UTC)) if self._leases else None
        if self._leases is not None and lease is None:
            return SyncResult(snapshot_id, 0, 0, 0, 0, 0, 0, 0, skipped=True)
        counts = {"created": 0, "updated": 0, "ignored": 0, "pending": 0}
        read_rows = 0
        try:
            for raw_row in self._rows(source):
                self._heartbeat(lease)
                row = raw_row if isinstance(raw_row, NormalizedSourceRow) else normalize_source_row(raw_row)
                row = replace(row, source_snapshot_id=snapshot_id)
                result = self._lead_service.import_row(row, f"sync:{snapshot_id}:{row.source_lead_id}")
                read_rows += 1
                if result.status in counts:
                    counts[result.status] += 1
            if self._queue_service is not None:
                self._queue_service.reconcile_pending(f"sync:{snapshot_id}:reconcile")
                self._queue_service.reconcile_pending_manual(
                    f"sync:{snapshot_id}:reconcile-manual"
                )
            self._heartbeat(lease)
            archive = self._lead_service.archive_missing(snapshot_id)
        except Exception:
            self._finish(lease, succeeded=False)
            raise
        self._finish(lease, succeeded=True)
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

    def _heartbeat(self, lease: SyncLease | None) -> None:
        if lease is not None and self._leases is not None:
            if not self._leases.heartbeat(lease, datetime.now(UTC)):
                raise SyncLeaseLostError("sync lease lost to a newer generation")

    def _finish(self, lease: SyncLease | None, *, succeeded: bool) -> None:
        if lease is not None and self._leases is not None:
            self._leases.finish(lease, datetime.now(UTC), succeeded=succeeded)

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
    return SyncJob(
        LeadService(LeadRepository(database)),
        queue_service=QueueService(
            QueueRepository(database), actor_id="google-sheets-sync"
        ),
        leases=MongoSyncLeaseRepository(database),
    ).run(source, run_id)


def _mongo_id(value: str) -> Any:
    return ObjectId(value) if ObjectId.is_valid(value) else value
