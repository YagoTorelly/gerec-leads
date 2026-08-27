"""Defini\u00e7\u00f5es idempotentes dos \u00edndices que protegem invariantes MongoDB."""

from dataclasses import dataclass
from typing import Any, Final

from pymongo import ASCENDING
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
        options: dict[str, Any] = {"name": self.name, "unique": self.unique}
        if self.partial_filter is not None:
            options["partialFilterExpression"] = self.partial_filter
        return target.create_index(self.keys, **options)


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
        MongoCollections.SALES,
        (("leadId", ASCENDING),),
        "sales_active_lead_unique",
        unique=True,
        partial_filter={"reversedAt": None},
    ),
    MongoIndex(
        MongoCollections.SESSIONS,
        (("tokenHash", ASCENDING),),
        "sessions_token_hash_unique",
        unique=True,
    ),
)
