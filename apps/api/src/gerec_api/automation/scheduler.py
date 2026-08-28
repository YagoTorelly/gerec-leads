"""Railway cron coordination backed by persistent MongoDB job locks."""

from __future__ import annotations

import os
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Protocol

from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError

from gerec_api.automation.sync_job import run_sync
from gerec_api.config import Settings
from gerec_api.infrastructure.mongo.client import MongoClientFactory
from gerec_api.infrastructure.mongo.collections import MongoCollections


SYNC_JOB_NAME = "google_sheets_sync"
SYNC_INTERVAL_MINUTES = 5


@dataclass(frozen=True)
class JobResult:
    sync_runs: int
    skipped: int
    failed: int


class JobLockRepository(Protocol):
    def claim(self, job_name: str, slot: str, now: datetime) -> bool: ...

    def finish(self, job_name: str, slot: str, now: datetime, *, succeeded: bool) -> None: ...


class MongoJobLockRepository:
    """Allow one successful run per time slot, with expired leases recoverable after crashes."""

    def __init__(self, database: Any, *, lease_for: timedelta = timedelta(minutes=10)) -> None:
        self._jobs = database[MongoCollections.AUTOMATION_JOB_LOCKS]
        self._lease_for = lease_for

    def claim(self, job_name: str, slot: str, now: datetime) -> bool:
        try:
            document = self._jobs.find_one_and_update(
                {
                    "_id": job_name,
                    "$and": [
                        {
                            "$or": [
                                {"lastSuccessfulSlot": {"$ne": slot}},
                                {"lastSuccessfulSlot": {"$exists": False}},
                            ]
                        },
                        {
                            "$or": [
                                {"lockedUntil": {"$lte": now}},
                                {"lockedUntil": {"$exists": False}},
                            ]
                        },
                    ],
                },
                {
                    "$set": {"lockedSlot": slot, "lockedUntil": now + self._lease_for},
                    "$setOnInsert": {"createdAt": now},
                },
                upsert=True,
                return_document=ReturnDocument.AFTER,
            )
        except DuplicateKeyError:
            return False
        return document is not None and document.get("lockedSlot") == slot

    def finish(self, job_name: str, slot: str, now: datetime, *, succeeded: bool) -> None:
        update: dict[str, Any] = {
            "$set": {"lastRunAt": now, "lastStatus": "succeeded" if succeeded else "failed"},
            "$unset": {"lockedSlot": "", "lockedUntil": ""},
        }
        if succeeded:
            update["$set"]["lastSuccessfulSlot"] = slot
        self._jobs.update_one({"_id": job_name, "lockedSlot": slot}, update)


class InMemoryJobLockRepository:
    """Small deterministic lock repository for unit tests."""

    def __init__(self) -> None:
        self._successful_slots: set[tuple[str, str]] = set()
        self._locked: set[tuple[str, str]] = set()

    def claim(self, job_name: str, slot: str, now: datetime) -> bool:
        key = (job_name, slot)
        if key in self._successful_slots or key in self._locked:
            return False
        self._locked.add(key)
        return True

    def finish(self, job_name: str, slot: str, now: datetime, *, succeeded: bool) -> None:
        key = (job_name, slot)
        self._locked.discard(key)
        if succeeded:
            self._successful_slots.add(key)


class Scheduler:
    """Run the sync once per five-minute slot without embedding domain decisions."""

    def __init__(self, locks: JobLockRepository, run_sync_job: Callable[[str], None]) -> None:
        self._locks = locks
        self._run_sync_job = run_sync_job

    def run_due_jobs(self, now: datetime) -> JobResult:
        timestamp = now.astimezone(UTC)
        slot_time = timestamp.replace(
            minute=timestamp.minute - timestamp.minute % SYNC_INTERVAL_MINUTES,
            second=0,
            microsecond=0,
        )
        slot = slot_time.isoformat()
        if not self._locks.claim(SYNC_JOB_NAME, slot, timestamp):
            return JobResult(sync_runs=0, skipped=1, failed=0)
        try:
            self._run_sync_job(f"sync:{slot}")
        except Exception:
            self._locks.finish(SYNC_JOB_NAME, slot, timestamp, succeeded=False)
            return JobResult(sync_runs=0, skipped=0, failed=1)
        self._locks.finish(SYNC_JOB_NAME, slot, timestamp, succeeded=True)
        return JobResult(sync_runs=1, skipped=0, failed=0)


def _configured_sync(run_id: str) -> None:
    source_path = os.environ.get("GOOGLE_SHEETS_WORKBOOK_PATH")
    if not source_path:
        raise RuntimeError("GOOGLE_SHEETS_WORKBOOK_PATH must be configured in Railway")
    run_sync(Path(source_path), run_id)


def run_due_jobs(now: datetime) -> JobResult:
    """Railway cron entry point for the five-minute Google Sheets sync slot."""
    settings = Settings.from_env()
    database = MongoClientFactory.create(settings)
    return Scheduler(MongoJobLockRepository(database), _configured_sync).run_due_jobs(now)


if __name__ == "__main__":
    run_due_jobs(datetime.now(UTC))
