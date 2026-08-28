"""Transactional MongoDB implementation of the lead-ingestion interface."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Callable

from pymongo.errors import DuplicateKeyError

from gerec_api.domain.documents import prepare_company_for_persistence
from gerec_api.domain.leads import ArchiveResult, ImportResult
from gerec_api.domain.normalization import NormalizedSourceRow
from gerec_api.infrastructure.mongo.collections import MongoCollections


IMPORT_COMMAND = "lead.import"
ARCHIVE_COMMAND = "lead.archive_missing"


class LeadRepository:
    """Keep deduplication, pending-state and snapshot lifecycle local to one adapter."""

    def __init__(self, database: Any, *, now: Callable[[], datetime] | None = None) -> None:
        self._database = database
        self._now = now or (lambda: datetime.now(UTC))

    def import_row(self, row: NormalizedSourceRow, idempotency_key: str) -> ImportResult:
        try:
            return self._with_transaction(
                lambda session: self._import_in_transaction(row, idempotency_key, session)
            )
        except DuplicateKeyError:
            receipt = self._command_results.find_one({"idempotencyKey": idempotency_key})
            if receipt is None or receipt.get("commandName") != IMPORT_COMMAND:
                raise
            return ImportResult.from_document(receipt["result"])

    def archive_missing(self, source_snapshot_id: str) -> ArchiveResult:
        idempotency_key = f"{ARCHIVE_COMMAND}:{source_snapshot_id}"
        try:
            return self._with_transaction(
                lambda session: self._archive_in_transaction(
                    source_snapshot_id,
                    idempotency_key,
                    session,
                )
            )
        except DuplicateKeyError:
            receipt = self._command_results.find_one({"idempotencyKey": idempotency_key})
            if receipt is None or receipt.get("commandName") != ARCHIVE_COMMAND:
                raise
            return ArchiveResult.from_document(receipt["result"])

    def _with_transaction(self, operation: Callable[[Any], Any]) -> Any:
        with self._database.client.start_session() as session:
            with session.start_transaction():
                return operation(session)

    def _import_in_transaction(
        self,
        row: NormalizedSourceRow,
        idempotency_key: str,
        session: Any,
    ) -> ImportResult:
        receipt = self._command_results.find_one(
            {"idempotencyKey": idempotency_key},
            session=session,
        )
        if receipt is not None:
            if receipt.get("commandName") != IMPORT_COMMAND:
                raise ValueError("idempotency key already belongs to another command")
            return ImportResult.from_document(receipt["result"])

        now = self._now()
        existing_source = self._source_records.find_one(
            {"sourceLeadId": row.source_lead_id},
            session=session,
        )
        campaign = (
            None
            if "campaign" in row.data_issues
            else self._resolve_campaign(row, now, session)
        )
        identical = (
            existing_source is not None
            and existing_source.get("rowHash") == row.row_hash
            and existing_source.get("present") is True
        )

        if identical:
            source_id = existing_source["_id"]
            lead_id = existing_source.get("leadId")
            lead = (
                self._leads.find_one({"_id": lead_id}, session=session)
                if lead_id is not None
                else None
            )
            self._mark_source_seen(source_id, row.source_snapshot_id, now, session)
            result = ImportResult(
                status="ignored",
                source_record_id=str(source_id),
                lead_id=str(lead_id) if lead_id is not None else None,
                pending_reasons=tuple(existing_source.get("pendingReasons", [])),
                assignment_status=(lead.get("assignmentStatus") if lead is not None else None),
            )
        else:
            pending_reasons = list(row.data_issues)
            previous_lead_id = existing_source.get("leadId") if existing_source else None
            lead_id = None
            occurrence_created = False
            if not row.data_issues:
                assert campaign is not None
                company = self._resolve_company(row, now, session)
                lead, occurrence_created = self._resolve_lead(row, company, campaign, now, session)
                lead_id = lead["_id"]
                if campaign["status"] != "approved":
                    pending_reasons.append("campaign")
            source_id = self._upsert_source(
                row,
                lead_id,
                pending_reasons,
                existing_source,
                now,
                session,
            )
            if previous_lead_id is not None and previous_lead_id != lead_id:
                self._archive_detached_lead_if_orphaned(
                    previous_lead_id,
                    "source_became_pending" if lead_id is None else "source_relinked",
                    now,
                    session,
                )
            status = "pending" if pending_reasons else ("created" if occurrence_created else "updated")
            result = ImportResult(
                status=status,
                source_record_id=str(source_id),
                lead_id=str(lead_id) if lead_id is not None else None,
                pending_reasons=tuple(pending_reasons),
                assignment_status=(lead.get("assignmentStatus") if lead_id is not None else None),
            )

        self._command_results.insert_one(
            {
                "commandName": IMPORT_COMMAND,
                "idempotencyKey": idempotency_key,
                "result": result.to_document(),
                "createdAt": now,
            },
            session=session,
        )
        return result

    def _resolve_campaign(
        self,
        row: NormalizedSourceRow,
        now: datetime,
        session: Any,
    ) -> dict[str, Any]:
        identity_key = _campaign_identity(row)
        campaign = self._campaigns.find_one({"identityKey": identity_key}, session=session)
        fields = {
            "externalId": row.campaign_external_id,
            "sourceName": row.campaign_name,
            "updatedAt": now,
        }
        if campaign is None:
            document = {
                "identityKey": identity_key,
                **fields,
                "displayName": row.campaign_name or row.campaign_external_id,
                "status": "approved",
                "approvalMode": "google_sheets_auto",
                "createdAt": now,
            }
            result = self._campaigns.insert_one(document, session=session)
            return {"_id": result.inserted_id, **document}
        if campaign.get("status") == "pending_approval":
            fields["status"] = "approved"
            fields["approvalMode"] = "google_sheets_auto"
        self._campaigns.update_one({"_id": campaign["_id"]}, {"$set": fields}, session=session)
        return {**campaign, **fields}

    def _resolve_company(
        self,
        row: NormalizedSourceRow,
        now: datetime,
        session: Any,
    ) -> dict[str, Any]:
        if row.document_normalized is None:
            identity = f"source:{row.source_lead_id}"
            company = self._companies.find_one({"sourceIdentity": identity}, session=session)
            fields = {"name": row.company_name or row.contact_name, "state": row.state, "updatedAt": now}
            if company is None:
                document = {"sourceIdentity": identity, **fields, "ownerId": None, "clientSince": None, "createdAt": now}
                result = self._companies.insert_one(document, session=session)
                return {"_id": result.inserted_id, **document}
            self._companies.update_one({"_id": company["_id"]}, {"$set": fields}, session=session)
            return {**company, **fields}
        company = self._companies.find_one(
            {"documentNormalized": row.document_normalized},
            session=session,
        )
        fields = {
            "name": row.company_name or row.contact_name,
            "state": row.state,
            "updatedAt": now,
        }
        if company is None:
            document = prepare_company_for_persistence(
                {
                    "documentNormalized": row.document_normalized,
                    **fields,
                    "ownerId": None,
                    "clientSince": None,
                    "createdAt": now,
                }
            )
            result = self._companies.insert_one(document, session=session)
            return {"_id": result.inserted_id, **document}
        self._companies.update_one({"_id": company["_id"]}, {"$set": fields}, session=session)
        return {**company, **fields}

    def _resolve_lead(
        self,
        row: NormalizedSourceRow,
        company: dict[str, Any],
        campaign: dict[str, Any],
        now: datetime,
        session: Any,
    ) -> tuple[dict[str, Any], bool]:
        query = {
            "companyId": company["_id"],
            "campaignId": campaign["_id"],
            "archivedAt": None,
        }
        lead = self._leads.find_one(query, session=session)
        source_fields = {
            "sourceEnteredAt": row.source_entered_at,
            "contactName": row.contact_name,
            "phoneNormalized": row.phone_normalized,
            "emailNormalized": row.email_normalized,
            "state": row.state,
            "adExternalId": row.ad_external_id,
            "adName": row.ad_name,
            "updatedAt": now,
        }
        if lead is None:
            document = {
                **query,
                **source_fields,
                "assignmentStatus": "ready" if campaign["status"] == "approved" else "pending_campaign",
                "qualificationStatus": "pending",
                "conversionStatus": "active",
                "createdAt": now,
            }
            result = self._leads.insert_one(document, session=session)
            return {"_id": result.inserted_id, **document}, True
        operational_fields: dict[str, Any] = {}
        if lead.get("assignmentStatus") == "pending_campaign" and campaign["status"] == "approved":
            operational_fields["assignmentStatus"] = "ready"
        fields = {**source_fields, **operational_fields}
        self._leads.update_one({"_id": lead["_id"]}, {"$set": fields}, session=session)
        return {**lead, **fields}, False

    def _upsert_source(
        self,
        row: NormalizedSourceRow,
        lead_id: Any | None,
        pending_reasons: list[str],
        existing_source: dict[str, Any] | None,
        now: datetime,
        session: Any,
    ) -> Any:
        fields = {
            "leadId": lead_id,
            "sourceEnteredAt": row.source_entered_at,
            "lastSeenSnapshotId": row.source_snapshot_id,
            "rowHash": row.row_hash,
            "payload": row.source_payload,
            "sellerProjection": row.source_projection,
            "pendingReasons": pending_reasons,
            "present": True,
            "archivedAt": None,
            "archiveReason": None,
            "updatedAt": now,
        }
        if existing_source is None:
            result = self._source_records.insert_one(
                {
                    "sourceLeadId": row.source_lead_id,
                    **fields,
                    "createdAt": now,
                },
                session=session,
            )
            return result.inserted_id
        self._source_records.update_one(
            {"_id": existing_source["_id"]},
            {"$set": fields},
            session=session,
        )
        return existing_source["_id"]

    def _archive_detached_lead_if_orphaned(
        self,
        lead_id: Any,
        reason: str,
        now: datetime,
        session: Any,
    ) -> None:
        another_active = self._source_records.find_one(
            {"leadId": lead_id, "present": True},
            session=session,
        )
        if another_active is not None:
            return
        self._leads.update_one(
            {"_id": lead_id, "archivedAt": None},
            {
                "$set": {
                    "archivedAt": now,
                    "archiveReason": reason,
                    "assignmentStatus": "archived",
                    "updatedAt": now,
                }
            },
            session=session,
        )

    def _mark_source_seen(
        self,
        source_id: Any,
        source_snapshot_id: str | None,
        now: datetime,
        session: Any,
    ) -> None:
        self._source_records.update_one(
            {"_id": source_id},
            {
                "$set": {
                    "lastSeenSnapshotId": source_snapshot_id,
                    "updatedAt": now,
                }
            },
            session=session,
        )

    def _archive_in_transaction(
        self,
        source_snapshot_id: str,
        idempotency_key: str,
        session: Any,
    ) -> ArchiveResult:
        receipt = self._command_results.find_one(
            {"idempotencyKey": idempotency_key},
            session=session,
        )
        if receipt is not None:
            if receipt.get("commandName") != ARCHIVE_COMMAND:
                raise ValueError("idempotency key already belongs to another command")
            return ArchiveResult.from_document(receipt["result"])

        now = self._now()
        missing = list(
            self._source_records.find(
                {
                    "present": True,
                    "lastSeenSnapshotId": {"$ne": source_snapshot_id},
                },
                session=session,
            )
        )
        archived_leads = 0
        for source in missing:
            self._source_records.update_one(
                {"_id": source["_id"]},
                {
                    "$set": {
                        "present": False,
                        "archivedAt": now,
                        "archiveReason": "removed_from_source",
                        "updatedAt": now,
                    }
                },
                session=session,
            )
            lead_id = source.get("leadId")
            if lead_id is None:
                continue
            another_active = self._source_records.find_one(
                {
                    "leadId": lead_id,
                    "present": True,
                    "_id": {"$ne": source["_id"]},
                },
                session=session,
            )
            if another_active is None:
                lead = self._leads.find_one({"_id": lead_id, "archivedAt": None}, session=session)
                if lead is not None:
                    self._leads.update_one(
                        {"_id": lead_id},
                        {
                            "$set": {
                                "archivedAt": now,
                                "archiveReason": "removed_from_source",
                                "assignmentStatus": "archived",
                                "updatedAt": now,
                            }
                        },
                        session=session,
                    )
                    archived_leads += 1

        result = ArchiveResult(
            source_snapshot_id=source_snapshot_id,
            archived_source_records=len(missing),
            archived_leads=archived_leads,
        )
        self._command_results.insert_one(
            {
                "commandName": ARCHIVE_COMMAND,
                "idempotencyKey": idempotency_key,
                "result": result.to_document(),
                "createdAt": now,
            },
            session=session,
        )
        return result

    @property
    def _campaigns(self):
        return self._database[MongoCollections.CAMPAIGNS]

    @property
    def _companies(self):
        return self._database[MongoCollections.COMPANIES]

    @property
    def _leads(self):
        return self._database[MongoCollections.LEADS]

    @property
    def _source_records(self):
        return self._database[MongoCollections.SOURCE_RECORDS]

    @property
    def _command_results(self):
        return self._database[MongoCollections.COMMAND_RESULTS]


def _campaign_identity(row: NormalizedSourceRow) -> str:
    if row.campaign_external_id is not None:
        return f"external:{row.campaign_external_id}"
    assert row.campaign_name is not None
    return f"name:{' '.join(row.campaign_name.casefold().split())}"
