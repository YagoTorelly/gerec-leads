"""Unit coverage for Railway automation boundaries and replay safety."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any

from gerec_api.automation.outbox_worker import OutboxEvent, OutboxWorker
from gerec_api.automation.scheduler import InMemoryJobLockRepository, Scheduler
from gerec_api.automation.sync_job import SyncJob
from gerec_api.domain.leads import ArchiveResult, ImportResult
from gerec_api.domain.normalization import normalize_source_row


def _row(source_id: str):
    return normalize_source_row(
        {
            "id": source_id,
            "created_time": "2026-08-27T10:00:00-03:00",
            "campaign_id": "campaign-a",
            "campaign_name": "Campaign A",
            "document": "04.252.011/0001-10",
            "state": "SP",
            "company_name": "Empresa WTG",
            "full_name": "Maria",
            "phone_number": "(11) 99876-5432",
            "email": "maria@example.com",
        }
    )


class RecordingLeadService:
    def __init__(self) -> None:
        self.imports: dict[str, Any] = {}
        self.archives: list[str] = []

    def import_row(self, row: Any, key: str) -> ImportResult:
        self.imports.setdefault(key, row)
        return ImportResult("created", row.source_lead_id, row.source_lead_id, (), "ready")

    def archive_missing(self, snapshot_id: str) -> ArchiveResult:
        if snapshot_id not in self.archives:
            self.archives.append(snapshot_id)
        return ArchiveResult(snapshot_id, 0, 0)


def test_sync_job_replays_a_complete_snapshot_with_stable_per_row_keys() -> None:
    """Breaks if a Railway retry changes imports or archives before the full snapshot."""
    service = RecordingLeadService()
    job = SyncJob(service)

    first = job.run([_row("source-a"), _row("source-b")], "run-20260827-1000")
    replay = job.run([_row("source-a"), _row("source-b")], "run-20260827-1000")

    assert first == replay
    assert first.read_rows == 2
    assert first.created == 2
    assert set(service.imports) == {
        "sync:run-20260827-1000:source-a",
        "sync:run-20260827-1000:source-b",
    }
    assert {row.source_snapshot_id for row in service.imports.values()} == {"run-20260827-1000"}
    assert service.archives == ["run-20260827-1000"]


class RecordingQueueService:
    def __init__(self) -> None:
        self.commands: list[tuple[str, str]] = []
        self.reconciliations: list[str] = []
        self.manual_reconciliations: list[str] = []

    def distribute_ready(self, lead_id: str, command_id: str) -> None:
        self.commands.append((lead_id, command_id))

    def reconcile_pending(self, command_prefix: str) -> None:
        self.reconciliations.append(command_prefix)

    def reconcile_pending_manual(self, command_prefix: str) -> None:
        self.manual_reconciliations.append(command_prefix)


def test_sync_job_reconciles_all_pending_leads_after_the_complete_import() -> None:
    """Breaks if newer rows bypass older parked leads during the same sync."""
    service = RecordingLeadService()
    queue = RecordingQueueService()

    SyncJob(service, queue_service=queue).run(
        [_row("source-a"), _row("source-b")], "run-20260827-1000"
    )

    assert queue.commands == []
    assert queue.reconciliations == ["sync:run-20260827-1000:reconcile"]
    assert queue.manual_reconciliations == ["sync:run-20260827-1000:reconcile-manual"]


class InMemoryOutboxRepository:
    def __init__(self, events: list[OutboxEvent]) -> None:
        self.events = {event.event_id: event for event in events}
        self.sent: set[str] = set()
        self.retries: list[str] = []
        self.dead_letters: list[str] = []
        self.cancelled: list[str] = []

    def claim(self, batch_size: int, now: datetime, max_attempts: int) -> list[OutboxEvent]:
        claimed = []
        for event in self.events.values():
            if event.event_id in self.sent or event.attempts >= max_attempts:
                continue
            if event.status not in {"pending", "retry"}:
                continue
            claimed.append(replace(event, status="processing", attempts=event.attempts + 1))
            if len(claimed) == batch_size:
                break
        return claimed

    def mark_sent(self, event: OutboxEvent, now: datetime) -> bool:
        self.sent.add(event.event_id)
        return True

    def mark_retry(self, event: OutboxEvent, error: Exception, now: datetime, max_attempts: int) -> bool:
        if event.attempts >= max_attempts:
            self.dead_letters.append(event.event_id)
        else:
            self.events[event.event_id] = replace(event, status="retry")
            self.retries.append(event.event_id)
        return True

    def cancel(self, event: OutboxEvent, now: datetime) -> bool:
        self.cancelled.append(event.event_id)
        return True


def test_outbox_worker_retries_once_and_never_delivers_an_event_twice() -> None:
    """Breaks if an alert is sent twice after a retry or a completed worker replay."""
    event = OutboxEvent("event-1", "lead.assigned", "alert-1", {"leadId": "lead-1"})
    repository = InMemoryOutboxRepository([event])
    calls: list[str] = []

    def send_once_then_succeed(message: OutboxEvent) -> None:
        calls.append(message.idempotency_key)
        if len(calls) == 1:
            raise ConnectionError("mail provider unavailable")

    worker = OutboxWorker(repository, send_once_then_succeed, max_attempts=3)
    now = datetime(2026, 8, 27, 13, tzinfo=UTC)

    assert worker.process(10, now=now) == 0
    assert worker.process(10, now=now) == 1
    assert worker.process(10, now=now) == 0
    assert calls == ["alert-1", "alert-1"]
    assert repository.retries == ["event-1"]
    assert repository.sent == {"event-1"}


def test_outbox_worker_never_delivers_legacy_deadline_alerts() -> None:
    """Breaks if a claimed pre-migration SLA event can still reach an external provider."""
    event = OutboxEvent("event-1", "lead.feedback_due_soon", "alert-1", {"leadId": "lead-1"})
    repository = InMemoryOutboxRepository([event])
    delivered: list[str] = []

    processed = OutboxWorker(repository, lambda message: delivered.append(message.event_id)).process(
        10, now=datetime(2026, 9, 4, 13, tzinfo=UTC)
    )

    assert processed == 0
    assert delivered == []
    assert repository.cancelled == ["event-1"]


def test_scheduler_runs_the_five_minute_slot_once_and_allows_next_slot() -> None:
    """Breaks if overlapping Railway cron invocations duplicate a synchronization."""
    runs: list[str] = []
    scheduler = Scheduler(
        InMemoryJobLockRepository(),
        lambda run_id: runs.append(run_id),
    )

    first = scheduler.run_due_jobs(datetime(2026, 8, 27, 13, 2, tzinfo=UTC))
    duplicate = scheduler.run_due_jobs(datetime(2026, 8, 27, 13, 4, tzinfo=UTC))
    next_slot = scheduler.run_due_jobs(datetime(2026, 8, 27, 13, 5, tzinfo=UTC))

    assert first.sync_runs == 1
    assert duplicate.sync_runs == 0
    assert next_slot.sync_runs == 1
    assert runs == ["sync:2026-08-27T13:00:00+00:00", "sync:2026-08-27T13:05:00+00:00"]


def test_railway_deployment_contract_documents_api_worker_cron_and_server_only_secrets() -> None:
    """Breaks if Railway loses a process or commits an integration credential."""
    root = Path(__file__).parents[4]
    config = json.loads((root / "railway.json").read_text(encoding="utf-8"))
    guide = (root / "infra" / "railway" / "README.md").read_text(encoding="utf-8")

    assert config["$schema"] == "https://railway.com/railway.schema.json"
    assert config["build"]["dockerfilePath"] == "apps/api/Dockerfile"
    assert "startCommand" not in config["deploy"]
    assert config["deploy"]["healthcheckPath"] == "/health"
    assert "uvicorn gerec_api.main:create_app" in guide
    assert "python -m gerec_api.automation.outbox_worker" in guide
    assert "python -m gerec_api.automation.scheduler" in guide
    assert "*/5 * * * *" in guide
    assert all(name in guide for name in ("MONGODB_URI", "MONGODB_DATABASE", "APP_SECRET"))
    assert "n8n" not in guide.lower()
