"""Defini\u00e7\u00f5es idempotentes dos \u00edndices que protegem invariantes MongoDB."""

from dataclasses import dataclass
from typing import Any, Final

from pymongo import ASCENDING, DESCENDING
from pymongo.collection import Collection

from gerec_api.infrastructure.mongo.collections import MongoCollections


@dataclass(frozen=True)
class MongoIndex:
    """Contrato declarativo de um \u00edndice que pode ser aplicado repetidamente."""

    collection_name: str
    keys: tuple[tuple[str, int], ...]
    name: str
    unique: bool = False
    partial_filter: dict[str, Any] | None = None

    def apply(self, target: Collection) -> str:
        """Cria ou reconcilia o \u00edndice sem apagar documentos existentes."""
        replacement_name = f"{self.name}__replacement"
        existing = target.index_information().get(self.name)
        if existing is not None and self._matches(existing):
            self._drop_replacement(target, replacement_name)
            return self.name

        if existing is None:
            try:
                return self._create(target, self.name)
            finally:
                self._drop_replacement(target, replacement_name)

        try:
            self._drop_replacement(target, replacement_name)
            self._create(target, replacement_name)
            target.drop_index(self.name)
            return self._create(target, self.name)
        except Exception:
            self._restore(target, self.name, existing)
            raise
        finally:
            self._drop_replacement(target, replacement_name)

    def _create(self, target: Collection, name: str) -> str:
        return target.create_index(self.keys, **self._options(name))

    def _options(self, name: str) -> dict[str, Any]:
        options: dict[str, Any] = {"name": name, "unique": self.unique}
        if self.partial_filter is not None:
            options["partialFilterExpression"] = self.partial_filter
        return options

    def _matches(self, index: dict[str, Any]) -> bool:
        return (
            index.get("key") == list(self.keys)
            and index.get("unique", False) is self.unique
            and index.get("partialFilterExpression") == self.partial_filter
        )

    @staticmethod
    def _drop_replacement(target: Collection, name: str) -> None:
        if name in target.index_information():
            target.drop_index(name)

    @staticmethod
    def _restore(target: Collection, name: str, index: dict[str, Any] | None) -> None:
        if index is None or name in target.index_information():
            return
        options: dict[str, Any] = {"name": name, "unique": index.get("unique", False)}
        if "partialFilterExpression" in index:
            options["partialFilterExpression"] = index["partialFilterExpression"]
        target.create_index(index["key"], **options)


INDEXES: Final[tuple[MongoIndex, ...]] = (
    MongoIndex(
        MongoCollections.USERS,
        (("emailNormalized", ASCENDING),),
        "users_email_normalized_unique",
        unique=True,
    ),
    MongoIndex(
        MongoCollections.SOURCE_RECORDS,
        (("sourceLeadId", ASCENDING),),
        "source_records_source_lead_id_unique",
        unique=True,
    ),
    MongoIndex(
        MongoCollections.CAMPAIGNS,
        (("identityKey", ASCENDING),),
        "campaigns_identity_key_unique",
        unique=True,
    ),
    MongoIndex(
        MongoCollections.COMPANIES,
        (("documentNormalized", ASCENDING),),
        "companies_document_normalized_present_unique",
        unique=True,
        partial_filter={"documentNormalized": {"$exists": True}},
    ),
    MongoIndex(
        MongoCollections.LEADS,
        (("companyId", ASCENDING), ("campaignId", ASCENDING)),
        "leads_active_company_campaign_unique",
        unique=True,
        partial_filter={"archivedAt": None},
    ),
    MongoIndex(
        MongoCollections.LEADS,
        (("assigneeId", ASCENDING), ("createdAt", ASCENDING)),
        "leads_assignee_created_at",
    ),
    MongoIndex(
        MongoCollections.LEADS,
        (("assigneeId", ASCENDING), ("assignedAt", ASCENDING)),
        "leads_assignee_assigned_at",
    ),
    MongoIndex(
        MongoCollections.LEADS,
        (("assigneeId", ASCENDING), ("assignmentSequence", ASCENDING)),
        "leads_assignee_assignment_sequence",
    ),
    MongoIndex(
        MongoCollections.LEADS,
        (("manualQueueLeadId", ASCENDING),),
        "leads_manual_queue_lead_id_unique",
        unique=True,
        partial_filter={"manualQueueLeadId": {"$exists": True}},
    ),
    MongoIndex(
        MongoCollections.SALES,
        (("leadId", ASCENDING),),
        "sales_active_lead_unique",
        unique=True,
        partial_filter={"reversedAt": None},
    ),
    MongoIndex(
        MongoCollections.CONTACT_ATTEMPTS,
        (("leadId", ASCENDING), ("businessDate", ASCENDING)),
        "contact_attempts_lead_business_date_unique",
        unique=True,
    ),
    MongoIndex(
        MongoCollections.SESSIONS,
        (("tokenHash", ASCENDING),),
        "sessions_token_hash_unique",
        unique=True,
    ),
    MongoIndex(
        MongoCollections.ASSIGNMENTS,
        (("leadId", ASCENDING),),
        "assignments_current_lead_unique",
        unique=True,
        partial_filter={"current": True},
    ),
    MongoIndex(
        MongoCollections.SKIP_BALANCES,
        (("sellerId", ASCENDING),),
        "skip_balances_seller_unique",
        unique=True,
    ),
    MongoIndex(
        MongoCollections.COMMAND_RESULTS,
        (("idempotencyKey", ASCENDING),),
        "command_results_idempotency_key_unique",
        unique=True,
    ),
    MongoIndex(
        MongoCollections.LEAD_TREATMENTS,
        (("leadId", ASCENDING), ("createdAt", ASCENDING)),
        "lead_treatments_lead_created_at",
    ),
    MongoIndex(
        MongoCollections.LEAD_TREATMENTS,
        (("sellerId", ASCENDING), ("createdAt", ASCENDING)),
        "lead_treatments_seller_created_at",
    ),
    MongoIndex(
        MongoCollections.LEAD_TREATMENTS,
        (("leadId", ASCENDING), ("idempotencyKey", ASCENDING)),
        "lead_treatments_lead_idempotency_key_unique",
        unique=True,
    ),
    MongoIndex(
        MongoCollections.SELLER_QUEUE,
        (("sellerId", ASCENDING),),
        "seller_queue_seller_unique",
        unique=True,
    ),
    MongoIndex(
        MongoCollections.SELLER_QUEUE,
        (("position", ASCENDING),),
        "seller_queue_position_present_unique",
        unique=True,
        partial_filter={"position": {"$exists": True}},
    ),
    MongoIndex(
        MongoCollections.NOTIFICATION_OUTBOX,
        (("idempotencyKey", ASCENDING),),
        "notification_outbox_idempotency_key_unique",
        unique=True,
    ),
    MongoIndex(
        MongoCollections.NOTIFICATION_INCIDENTS,
        (("outboxEventId", ASCENDING),),
        "notification_incidents_outbox_event_unique",
        unique=True,
    ),
    MongoIndex(
        MongoCollections.EXPORTATIONS,
        (("createdAt", DESCENDING),),
        "exportations_created_at_desc",
    ),
    MongoIndex(
        MongoCollections.EXPORTATIONS,
        (("actorId", ASCENDING), ("createdAt", DESCENDING)),
        "exportations_actor_created_at_desc",
    ),
)


# Kept separate so the already-applied 20260923 migration retains its original
# behavior. The 20260924 migration backfills attemptId before bootstrap applies
# this unique index.
VERSIONED_INDEXES: Final[tuple[MongoIndex, ...]] = (
    MongoIndex(
        MongoCollections.EXPORTATIONS,
        (("attemptId", ASCENDING),),
        "exportations_attempt_id_unique",
        unique=True,
    ),
)

ALL_INDEXES: Final[tuple[MongoIndex, ...]] = (*INDEXES, *VERSIONED_INDEXES)
