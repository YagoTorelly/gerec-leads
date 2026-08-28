"""Integration-style automation tests for leases, fencing and provider composition."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from typing import Any

import pytest
from bson import ObjectId

from gerec_api.automation.google_sheets_adapter import GoogleSheetsAdapter
from gerec_api.automation.outbox_worker import (
    MongoOutboxRepository,
    OutboxEvent,
    WebhookDeliveryAdapter,
)
from gerec_api.automation.scheduler import scheduler_exit_code
from gerec_api.automation.sync_job import (
    InMemorySyncLeaseRepository,
    SyncJob,
    SyncLeaseLostError,
)
from gerec_api.domain.leads import ArchiveResult, ImportResult
from gerec_api.domain.normalization import normalize_source_row


class FakeCollection:
    def __init__(self, documents: list[dict[str, Any]] | None = None) -> None:
        self.documents = documents or []

    def find_one_and_update(self, query: dict[str, Any], update: dict[str, Any], **_: Any):
        now = query["$or"][-1].get("lockedUntil", {}).get("$lte")
        for document in self.documents:
            if document["status"] == "processing" and document.get("lockedUntil") > now:
                continue
            document.update(update.get("$set", {}))
            for key, value in update.get("$inc", {}).items():
                document[key] = document.get(key, 0) + value
            return dict(document)
        return None

    def update_one(self, query: dict[str, Any], update: dict[str, Any], **_: Any):
        for document in self.documents:
            if all(document.get(key) == value for key, value in query.items()):
                document.update(update.get("$set", {}))
                for key in update.get("$unset", {}):
                    document.pop(key, None)
                return SimpleNamespace(matched_count=1)
        return SimpleNamespace(matched_count=0)


class FakeDatabase:
    def __init__(self, outbox: FakeCollection) -> None:
        self.outbox = outbox
        self.incidents = FakeCollection()

    def __getitem__(self, name: str) -> FakeCollection:
        return self.outbox if name == "notification_outbox" else self.incidents


def test_outbox_fencing_rejects_a_stale_worker_after_its_lease_expires() -> None:
    """Breaks if a stale worker can acknowledge a newer worker's claimed event."""
    start = datetime(2026, 8, 27, 13, tzinfo=UTC)
    outbox = FakeCollection(
        [
            {
                "_id": "event-1",
                "eventType": "lead.assigned",
                "idempotencyKey": "assignment-1",
                "payload": {},
                "attempts": 0,
                "status": "pending",
                "createdAt": start,
            }
        ]
    )
    repository = MongoOutboxRepository(FakeDatabase(outbox), lock_for=timedelta(seconds=1))

    first = repository.claim(1, start, 3)[0]
    second = repository.claim(1, start + timedelta(seconds=2), 3)[0]

    assert first.claim_token != second.claim_token
    assert repository.mark_sent(first, start + timedelta(seconds=2)) is False
    assert outbox.documents[0]["status"] == "processing"
    assert repository.mark_sent(second, start + timedelta(seconds=2)) is True
    assert outbox.documents[0]["status"] == "sent"


def test_webhook_delivery_forwards_the_outbox_idempotency_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Breaks if a provider retry cannot deduplicate an externally delivered alert."""
    captured: dict[str, Any] = {}

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *_: Any) -> None:
            return None

    def open_request(request: Any, *, timeout: float):
        captured["headers"] = dict(request.header_items())
        captured["body"] = request.data
        captured["timeout"] = timeout
        return Response()

    monkeypatch.setenv("OUTBOX_DELIVERY_WEBHOOK_URL", "https://provider.example/send")
    adapter = WebhookDeliveryAdapter.from_env(open_request=open_request)
    adapter.deliver(OutboxEvent("event-1", "lead.assigned", "assignment-1", {}))

    assert captured["headers"]["Idempotency-key"] == "assignment-1"
    assert captured["timeout"] == 10


def test_webhook_delivery_serializes_bson_and_datetime_payloads(monkeypatch: pytest.MonkeyPatch) -> None:
    """Breaks if a real Mongo event crashes before reaching the configured provider."""
    captured: dict[str, Any] = {}

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *_: Any) -> None:
            return None

    def open_request(request: Any, *, timeout: float):
        captured["headers"] = dict(request.header_items())
        captured["body"] = request.data
        return Response()

    occurred_at = datetime(2026, 8, 27, 13, tzinfo=UTC)
    aggregate_id = ObjectId()
    monkeypatch.setenv("OUTBOX_DELIVERY_WEBHOOK_URL", "https://provider.example/send")
    WebhookDeliveryAdapter.from_env(open_request=open_request).deliver(
        OutboxEvent("event-2", "lead.assigned", "assignment-2", {"leadId": aggregate_id, "occurredAt": occurred_at})
    )

    body = __import__("json").loads(captured["body"])
    assert captured["headers"]["Idempotency-key"] == "assignment-2"
    assert body["payload"] == {"leadId": str(aggregate_id), "occurredAt": occurred_at.isoformat()}


class RecordingLeadService:
    def __init__(self, leases: InMemorySyncLeaseRepository) -> None:
        self.leases = leases
        self.archives: list[str] = []

    def import_row(self, row: Any, key: str) -> ImportResult:
        self.leases.invalidate_current()
        return ImportResult("created", row.source_lead_id, None)

    def archive_missing(self, snapshot_id: str) -> ArchiveResult:
        self.archives.append(snapshot_id)
        return ArchiveResult(snapshot_id, 0, 0)


def test_sync_lease_stops_an_old_generation_before_archive() -> None:
    """Breaks if an expired sync can archive rows seen by a newer snapshot."""
    leases = InMemorySyncLeaseRepository()
    service = RecordingLeadService(leases)
    job = SyncJob(service, leases=leases)
    row = normalize_source_row(
        {
            "id": "source-1",
            "created_time": "2026-08-27T10:00:00-03:00",
            "campaign_id": "campaign-a",
            "campaign_name": "Campaign A",
            "document": "04.252.011/0001-10",
            "state": "SP",
        }
    )

    with pytest.raises(SyncLeaseLostError):
        job.run([row], "generation-old")

    assert service.archives == []


def test_google_sheets_adapter_reads_the_exact_a_through_q_response() -> None:
    """Breaks if Railway Google Sheets API ingestion bypasses the source contract."""
    values = [[
        "id", "created_time", "ad_id", "ad_name", "adset_id", "adset_name", "campaign_id",
        "campaign_name", "form_id", "form_name", "is_organic", "platform", "você_tem_cnpj_ou_mei?",
        "full_name", "phone_number", "email", "lead_status",
    ], ["source-1", "2026-08-27T10:00:00-03:00", "", "", "", "", "campaign-a", "Campaign A", "", "", "", "", "Sim", "Maria", "11999999999", "maria@example.com", ""]]
    adapter = GoogleSheetsAdapter("sheet-id", "Leads!A:Q", "token", fetch=lambda _: {"values": values})

    rows = list(adapter.read())

    assert rows[0].source_lead_id == "source-1"
    assert rows[0].campaign_external_id == "campaign-a"


def test_scheduler_failure_maps_to_a_non_zero_process_exit() -> None:
    """Breaks if Railway marks a failed sync cron execution as successful."""
    assert scheduler_exit_code(SimpleNamespace(failed=1)) == 1
    assert scheduler_exit_code(SimpleNamespace(failed=0)) == 0
