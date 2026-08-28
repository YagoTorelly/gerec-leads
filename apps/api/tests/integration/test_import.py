"""Integration coverage for workbook ingestion and MongoDB lead persistence."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from bson import ObjectId
from openpyxl import Workbook

from gerec_api.automation.workbook_adapter import EXPECTED_HEADERS, InvalidWorkbookError, WorkbookAdapter
from gerec_api.domain.leads import LeadService
from gerec_api.domain.normalization import normalize_source_row
from gerec_api.infrastructure.mongo.lead_repository import LeadRepository


class FakeTransaction:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False


class FakeSession:
    def __init__(self) -> None:
        self.transactions = 0

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def start_transaction(self) -> FakeTransaction:
        self.transactions += 1
        return FakeTransaction()


class FakeClient:
    def __init__(self) -> None:
        self.sessions: list[FakeSession] = []

    def start_session(self) -> FakeSession:
        session = FakeSession()
        self.sessions.append(session)
        return session


class FakeCollection:
    def __init__(self) -> None:
        self.documents: list[dict[str, Any]] = []

    def find_one(self, query: dict[str, Any], **_: Any) -> dict[str, Any] | None:
        for document in self.documents:
            if _matches(document, query):
                return deepcopy(document)
        return None

    def find(self, query: dict[str, Any], **_: Any) -> list[dict[str, Any]]:
        return [deepcopy(document) for document in self.documents if _matches(document, query)]

    def insert_one(self, document: dict[str, Any], **_: Any) -> SimpleNamespace:
        stored = deepcopy(document)
        stored.setdefault("_id", ObjectId())
        self.documents.append(stored)
        return SimpleNamespace(inserted_id=stored["_id"])

    def update_one(
        self,
        query: dict[str, Any],
        update: dict[str, Any],
        *,
        upsert: bool = False,
        **_: Any,
    ) -> SimpleNamespace:
        for document in self.documents:
            if _matches(document, query):
                _apply_update(document, update, inserting=False)
                return SimpleNamespace(matched_count=1, modified_count=1, upserted_id=None)
        if not upsert:
            return SimpleNamespace(matched_count=0, modified_count=0, upserted_id=None)
        stored = {key: value for key, value in query.items() if not isinstance(value, dict)}
        stored["_id"] = ObjectId()
        _apply_update(stored, update, inserting=True)
        self.documents.append(stored)
        return SimpleNamespace(matched_count=0, modified_count=0, upserted_id=stored["_id"])


class FakeDatabase:
    def __init__(self) -> None:
        self.client = FakeClient()
        self.collections: dict[str, FakeCollection] = {}

    def __getitem__(self, name: str) -> FakeCollection:
        return self.collections.setdefault(name, FakeCollection())


def _matches(document: dict[str, Any], query: dict[str, Any]) -> bool:
    for key, expected in query.items():
        actual = document.get(key)
        if isinstance(expected, dict):
            if "$ne" in expected and actual == expected["$ne"]:
                return False
            if "$in" in expected and actual not in expected["$in"]:
                return False
            continue
        if actual != expected:
            return False
    return True


def _apply_update(document: dict[str, Any], update: dict[str, Any], *, inserting: bool) -> None:
    if inserting:
        document.update(deepcopy(update.get("$setOnInsert", {})))
    document.update(deepcopy(update.get("$set", {})))
    for key in update.get("$unset", {}):
        document.pop(key, None)


def _complete_row(source_id: str, campaign_id: str = "campaign-a"):
    return normalize_source_row(
        {
            "source_snapshot_id": "snapshot-1",
            "id": source_id,
            "created_time": "2026-08-27T10:00:00-03:00",
            "campaign_id": campaign_id,
            "campaign_name": f"Campaign {campaign_id}",
            "document": "04.252.011/0001-10",
            "state": "SP",
            "company_name": "Empresa WTG",
            "full_name": "Maria",
            "phone_number": "(11) 99876-5432",
            "email": "maria@example.com",
        }
    )


def test_workbook_adapter_reads_only_leads_and_enforces_the_exact_a_through_q_contract() -> None:
    """Breaks if the production fixture can bypass header/order validation or the Leads sheet."""
    fixture = Path(__file__).parents[4] / "WTG - Leads.xlsx"

    rows = list(WorkbookAdapter().read(fixture))

    assert rows
    assert rows[0].source_lead_id
    assert rows[0].document_normalized is None
    assert tuple(rows[0].source_projection) == EXPECTED_HEADERS[12:16]
    assert EXPECTED_HEADERS[16] not in rows[0].source_projection


def test_workbook_adapter_rejects_a_structurally_different_workbook(tmp_path: Path) -> None:
    """Breaks if a partial snapshot can start after an unexpected source schema."""
    path = tmp_path / "wrong.xlsx"
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Leads"
    sheet.append([*EXPECTED_HEADERS[:-1], "unexpected_status"])
    workbook.save(path)

    with pytest.raises(InvalidWorkbookError, match="headers"):
        list(WorkbookAdapter().read(path))


def test_import_is_idempotent_and_repeated_company_campaign_reuses_the_commercial_occurrence() -> None:
    """Breaks if retries or a second origin duplicate companies, campaigns, or leads."""
    database = FakeDatabase()
    service = LeadService(LeadRepository(database))

    first = service.import_row(_complete_row("source-1"), "command-1")
    replay = service.import_row(_complete_row("source-1"), "command-1")
    second_source = service.import_row(_complete_row("source-2"), "command-2")

    assert first.status == "pending"
    assert replay == first
    assert second_source.status == "pending"
    assert len(database["command_results"].documents) == 2
    assert len(database["source_records"].documents) == 2
    assert len(database["companies"].documents) == 1
    assert len(database["campaigns"].documents) == 1
    assert len(database["leads"].documents) == 1
    assert database["leads"].documents[0]["assignmentStatus"] == "pending_campaign"
    assert all(session.transactions == 1 for session in database.client.sessions)


def test_changed_informational_source_field_updates_the_source_record() -> None:
    """Breaks if the row hash ignores a source-only field and silently drops its new value."""
    database = FakeDatabase()
    service = LeadService(LeadRepository(database))
    first = _complete_row("source-changing")
    changed_payload = {**first.source_payload, "lead_status": "CONTACTED"}

    service.import_row(first, "command-before-change")
    service.import_row(normalize_source_row(changed_payload), "command-after-change")

    stored = database["source_records"].documents[0]
    assert stored["payload"]["lead_status"] == "CONTACTED"


def test_reimport_updates_source_fields_without_resetting_assigned_or_final_lead_state() -> None:
    """Breaks if a spreadsheet refresh reopens distribution or a completed sale."""
    database = FakeDatabase()
    database["campaigns"].insert_one(
        {
            "identityKey": "external:campaign-a",
            "externalId": "campaign-a",
            "sourceName": "Campaign campaign-a",
            "status": "approved",
        }
    )
    service = LeadService(LeadRepository(database))
    row = _complete_row("source-final")
    service.import_row(row, "command-initial")
    lead = database["leads"].documents[0]
    lead.update(
        {
            "assignmentStatus": "assigned",
            "assigneeId": ObjectId(),
            "qualificationStatus": "qualified",
            "conversionStatus": "won",
            "outcomeEventId": ObjectId(),
            "wonAt": row.source_entered_at,
        }
    )

    changed = normalize_source_row({**row.source_payload, "full_name": "Maria Atualizada"})
    result = service.import_row(changed, "command-refresh")

    stored = database["leads"].documents[0]
    assert stored["contactName"] == "Maria Atualizada"
    assert result.assignment_status == "assigned"
    assert stored["assignmentStatus"] == "assigned"
    assert stored["qualificationStatus"] == "qualified"
    assert stored["conversionStatus"] == "won"
    assert "outcomeEventId" in stored
    assert "wonAt" in stored


def test_valid_source_becoming_pending_detaches_and_archives_its_only_lead() -> None:
    """Breaks if a newly invalid source leaves its previous lead active and distributable."""
    database = FakeDatabase()
    database["campaigns"].insert_one(
        {
            "identityKey": "external:campaign-a",
            "externalId": "campaign-a",
            "sourceName": "Campaign campaign-a",
            "status": "approved",
        }
    )
    service = LeadService(LeadRepository(database))
    valid = _complete_row("source-transition")
    service.import_row(valid, "command-valid")
    lead_id = database["source_records"].documents[0]["leadId"]
    pending_payload = {**valid.source_payload, "document": ""}

    result = service.import_row(normalize_source_row(pending_payload), "command-pending")

    source = database["source_records"].documents[0]
    lead = database["leads"].find_one({"_id": lead_id})
    assert result.lead_id is None
    assert result.pending_reasons == ("document",)
    assert source["leadId"] is None
    assert lead["archivedAt"] is not None
    assert lead["assignmentStatus"] == "archived"
    assert lead["archiveReason"] == "source_became_pending"


def test_one_shared_source_becoming_pending_preserves_lead_for_the_other_active_source() -> None:
    """Breaks if detaching one source archives a lead still backed by another active source."""
    database = FakeDatabase()
    database["campaigns"].insert_one(
        {
            "identityKey": "external:campaign-a",
            "externalId": "campaign-a",
            "sourceName": "Campaign campaign-a",
            "status": "approved",
        }
    )
    service = LeadService(LeadRepository(database))
    first = _complete_row("source-shared-1")
    second = _complete_row("source-shared-2")
    service.import_row(first, "command-shared-1")
    service.import_row(second, "command-shared-2")
    lead_id = database["source_records"].documents[0]["leadId"]

    service.import_row(
        normalize_source_row({**first.source_payload, "document": ""}),
        "command-shared-pending",
    )

    first_source = database["source_records"].find_one({"sourceLeadId": "source-shared-1"})
    second_source = database["source_records"].find_one({"sourceLeadId": "source-shared-2"})
    lead = database["leads"].find_one({"_id": lead_id})
    assert first_source["leadId"] is None
    assert second_source["leadId"] == lead_id
    assert lead["archivedAt"] is None
    assert lead["assignmentStatus"] == "ready"


def test_mock_pending_row_stays_in_source_records_and_never_enters_the_queue() -> None:
    """Breaks if missing document/state creates a fictitious company or distributable lead."""
    database = FakeDatabase()
    service = LeadService(LeadRepository(database))
    row = normalize_source_row(
        {
            "source_snapshot_id": "snapshot-1",
            "id": "mock-source",
            "created_time": "2026-08-27T10:00:00-03:00",
            "campaign_id": "campaign-a",
            "campaign_name": "Campaign A",
            "voc\u00ea_tem_cnpj_ou_mei?": "Sim",
            "full_name": "Maria",
            "phone_number": "(11) 99876-5432",
            "email": "maria@example.com",
        }
    )

    result = service.import_row(row, "command-pending")

    assert result.status == "pending"
    assert result.lead_id is None
    assert result.pending_reasons == ("document", "state")
    assert len(database["source_records"].documents) == 1
    assert database["source_records"].documents[0]["leadId"] is None
    assert database["companies"].documents == []
    assert database["leads"].documents == []


def test_row_without_campaign_is_preserved_as_pending_instead_of_crashing() -> None:
    """Breaks if a missing campaign prevents the source issue from being recorded for correction."""
    database = FakeDatabase()
    service = LeadService(LeadRepository(database))
    row = normalize_source_row(
        {
            "source_snapshot_id": "snapshot-1",
            "id": "missing-campaign",
            "created_time": "2026-08-27T10:00:00-03:00",
            "document": "04.252.011/0001-10",
            "state": "SP",
            "full_name": "Maria",
            "phone_number": "(11) 99876-5432",
            "email": "maria@example.com",
        }
    )

    result = service.import_row(row, "command-missing-campaign")

    assert result.status == "pending"
    assert result.pending_reasons == ("campaign",)
    assert len(database["source_records"].documents) == 1
    assert database["campaigns"].documents == []


def test_archive_missing_preserves_lead_until_its_last_active_source_disappears() -> None:
    """Breaks if one removed source archives shared history or the last source leaves a lead active."""
    database = FakeDatabase()
    service = LeadService(LeadRepository(database))
    service.import_row(_complete_row("source-1"), "command-1")
    service.import_row(_complete_row("source-2"), "command-2")
    lead_id = database["leads"].documents[0]["_id"]

    database["source_records"].documents[1]["lastSeenSnapshotId"] = "snapshot-2"
    first_archive = service.archive_missing("snapshot-2")

    assert first_archive.archived_source_records == 1
    assert first_archive.archived_leads == 0
    assert database["leads"].find_one({"_id": lead_id})["archivedAt"] is None

    final_archive = service.archive_missing("snapshot-3")

    assert final_archive.archived_source_records == 1
    assert final_archive.archived_leads == 1
    assert database["leads"].find_one({"_id": lead_id})["archivedAt"] is not None
