"""Transactional MongoDB implementation of the lead-ingestion interface."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Callable
from uuid import uuid4

from pymongo.errors import DuplicateKeyError

from gerec_api.domain.documents import prepare_company_for_persistence
from gerec_api.domain.leads import ArchiveResult, ImportResult
from gerec_api.domain.manual_leads import ManualLeadCommand, ManualLeadResult
from gerec_api.domain.normalization import NormalizedSourceRow
from gerec_api.infrastructure.mongo.collections import MongoCollections
from gerec_api.infrastructure.mongo.queue_repository import QueueRepository


IMPORT_COMMAND = "lead.import"
ARCHIVE_COMMAND = "lead.archive_missing"
MANUAL_COMMAND = "lead.create_manual"


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

    def create_manual_lead(
        self,
        actor: Any,
        command: ManualLeadCommand,
        now: datetime,
    ) -> ManualLeadResult:
        """Create and assign one manual lead atomically with an idempotent receipt."""
        existing = self._manual_receipt(command.idempotency_key)
        if existing is not None:
            return ManualLeadResult.from_document(existing["result"])

        def operation(session: Any) -> ManualLeadResult:
            receipt = self._manual_receipt(command.idempotency_key, session=session)
            if receipt is not None:
                return ManualLeadResult.from_document(receipt["result"])
            result = self._create_manual_in_transaction(actor, command, now, session)
            self._command_results.insert_one(
                {
                    "commandName": MANUAL_COMMAND,
                    "idempotencyKey": command.idempotency_key,
                    "result": result.to_document(),
                    "createdAt": now,
                },
                session=session,
            )
            return result

        try:
            with self._database.client.start_session() as session:
                return session.with_transaction(operation)
        except DuplicateKeyError:
            receipt = self._manual_receipt(command.idempotency_key)
            if receipt is None:
                raise
            return ManualLeadResult.from_document(receipt["result"])

    def _with_transaction(self, operation: Callable[[Any], Any]) -> Any:
        with self._database.client.start_session() as session:
            with session.start_transaction():
                return operation(session)

    def _create_manual_in_transaction(
        self,
        actor: Any,
        command: ManualLeadCommand,
        now: datetime,
        session: Any,
    ) -> ManualLeadResult:
        manual_queue_lead_id = f"MAN-{uuid4()}"
        inherited = self._latest_automatic_context(session)
        campaign_id, campaign_name = self._manual_campaign(
            command.campaign, inherited, now, session
        )
        inherited_origin = (
            inherited.get("origin")
            or inherited.get("adName")
            or inherited.get("adExternalId")
        )
        origin = command.source if command.source is not None else inherited_origin
        company = {
            "sourceIdentity": f"manual:{manual_queue_lead_id}",
            "name": command.name,
            "ownerId": None,
            "clientSince": None,
            "createdAt": now,
            "updatedAt": now,
        }
        company_id = self._companies.insert_one(company, session=session).inserted_id
        audit_payload = dict(command.original_payload) if command.original_payload else {
            "name": command.name,
            "email": command.email,
            "phone": command.phone,
            "campaign": command.campaign,
            "source": command.source,
        }
        lead = {
            "companyId": company_id,
            "campaignId": campaign_id,
            "campaignName": campaign_name,
            "origin": origin,
            "manualQueueLeadId": manual_queue_lead_id,
            "source": "manual",
            "contactName": command.name,
            "phone": command.phone,
            "emailNormalized": command.email,
            "commercialStatus": "undefined",
            "isDisqualified": False,
            "commentCount": 0,
            "lastCommentAt": None,
            "assignmentStatus": "ready",
            "assigneeId": None,
            "currentAssignmentId": None,
            "archivedAt": None,
            "createdAt": now,
            "updatedAt": now,
        }
        lead_id = self._leads.insert_one(lead, session=session).inserted_id
        self._audit_log.insert_one(
            {
                "actorId": actor,
                "action": "lead.manual_created",
                "entityType": "lead",
                "entityId": lead_id,
                "before": {},
                "after": {
                    "manualQueueLeadId": manual_queue_lead_id,
                    "payload": audit_payload,
                },
                "createdAt": now,
                "correlationId": command.idempotency_key,
            },
            session=session,
        )

        queue = QueueRepository(self._database, now=lambda: now)
        selection = queue._select_next_seller("manual", now, session)
        if selection.seller_id is None:
            self._leads.update_one(
                {"_id": lead_id, "currentAssignmentId": None},
                {
                    "$set": {
                        "assignmentStatus": "parked",
                        "parkReason": "no_eligible_seller",
                        "updatedAt": now,
                    }
                },
                session=session,
            )
            self._audit_log.insert_one(
                {
                    "actorId": actor,
                    "action": "queue.manual_parked",
                    "entityType": "lead",
                    "entityId": lead_id,
                    "before": {"assignmentStatus": "ready"},
                    "after": {
                        "assignmentStatus": "parked",
                        "parkReason": "no_eligible_seller",
                    },
                    "createdAt": now,
                    "correlationId": command.idempotency_key,
                },
                session=session,
            )
            return ManualLeadResult(
                lead_id=str(lead_id),
                manual_queue_lead_id=manual_queue_lead_id,
                assignee_id=None,
                assigned_at=None,
                status="parked",
            )

        assignment_sequence = queue._next_assignment_sequence(session)
        assignment = {
            "leadId": lead_id,
            "sellerId": selection.seller_id,
            "type": "manual",
            "reason": None,
            "current": True,
            "startedAt": now,
            "endedAt": None,
            "commandId": command.idempotency_key,
        }
        assignment_id = self._assignments.insert_one(assignment, session=session).inserted_id
        assigned = self._leads.update_one(
            {"_id": lead_id, "currentAssignmentId": None},
            {
                "$set": {
                    "assignmentStatus": "assigned",
                    "assigneeId": selection.seller_id,
                    "currentAssignmentId": assignment_id,
                    "assignmentType": "manual",
                    "assignedAt": now,
                    "assignmentSequence": assignment_sequence,
                    "updatedAt": now,
                }
            },
            session=session,
        )
        if assigned.matched_count != 1:
            raise RuntimeError("manual lead changed concurrently")
        self._companies.update_one(
            {"_id": company_id, "ownerId": None},
            {"$set": {"ownerId": selection.seller_id, "updatedAt": now}},
            session=session,
        )
        event_payload = {
            "assignmentStatus": "assigned",
            "assigneeId": selection.seller_id,
            "assignmentType": "manual",
            "manualQueueLeadId": manual_queue_lead_id,
            "assignmentSequence": assignment_sequence,
        }
        self._audit_log.insert_one(
            {
                "actorId": actor,
                "action": "queue.manual_assigned",
                "entityType": "lead",
                "entityId": lead_id,
                "before": {"assignmentStatus": "ready", "assigneeId": None},
                "after": event_payload,
                "createdAt": now,
                "correlationId": command.idempotency_key,
            },
            session=session,
        )
        self._notification_outbox.insert_one(
            {
                "eventType": "lead.assigned",
                "aggregateId": lead_id,
                "actorId": actor,
                "idempotencyKey": f"{command.idempotency_key}:lead.assigned",
                "status": "pending",
                "attempts": 0,
                "payload": event_payload,
                "createdAt": now,
            },
            session=session,
        )
        return ManualLeadResult(
            lead_id=str(lead_id),
            manual_queue_lead_id=manual_queue_lead_id,
            assignee_id=str(selection.seller_id),
            assigned_at=now,
        )

    def _manual_receipt(
        self,
        idempotency_key: str,
        *,
        session: Any | None = None,
    ) -> dict[str, Any] | None:
        options = {} if session is None else {"session": session}
        receipt = self._command_results.find_one({"idempotencyKey": idempotency_key}, **options)
        if receipt is not None and receipt.get("commandName") != MANUAL_COMMAND:
            raise ValueError("idempotency key already belongs to another command")
        return receipt

    def _latest_automatic_context(self, session: Any) -> dict[str, Any]:
        candidates = list(
            self._leads.find(
                {"manualQueueLeadId": {"$exists": False}},
                session=session,
            )
        )
        if not candidates:
            return {}
        minimum = datetime.min.replace(tzinfo=UTC)
        return max(
            candidates,
            key=lambda lead: lead.get("sourceEnteredAt") or lead.get("createdAt") or minimum,
        )

    def _manual_campaign(
        self,
        requested_name: str | None,
        inherited: dict[str, Any],
        now: datetime,
        session: Any,
    ) -> tuple[Any | None, str | None]:
        if requested_name is None:
            campaign_id = inherited.get("campaignId")
            campaign_name = inherited.get("campaignName")
            if campaign_name is None and campaign_id is not None:
                campaign = self._campaigns.find_one({"_id": campaign_id}, session=session)
                if campaign is not None:
                    campaign_name = (
                        campaign.get("displayName")
                        or campaign.get("sourceName")
                        or campaign.get("externalId")
                    )
            return campaign_id, campaign_name

        identity_key = f"manual:{' '.join(requested_name.casefold().split())}"
        campaign = self._campaigns.find_one({"identityKey": identity_key}, session=session)
        if campaign is not None:
            return campaign["_id"], requested_name
        document = {
            "identityKey": identity_key,
            "externalId": None,
            "sourceName": requested_name,
            "displayName": requested_name,
            "status": "approved",
            "approvalMode": "manual_lead",
            "createdAt": now,
            "updatedAt": now,
        }
        campaign_id = self._campaigns.insert_one(document, session=session).inserted_id
        return campaign_id, requested_name

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
            and (existing_source.get("leadId") is not None or bool(row.data_issues))
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

    @property
    def _assignments(self):
        return self._database[MongoCollections.ASSIGNMENTS]

    @property
    def _audit_log(self):
        return self._database[MongoCollections.AUDIT_LOG]

    @property
    def _notification_outbox(self):
        return self._database[MongoCollections.NOTIFICATION_OUTBOX]


def _campaign_identity(row: NormalizedSourceRow) -> str:
    if row.campaign_external_id is not None:
        return f"external:{row.campaign_external_id}"
    assert row.campaign_name is not None
    return f"name:{' '.join(row.campaign_name.casefold().split())}"
