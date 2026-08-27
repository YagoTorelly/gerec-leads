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
        existing = target.index_information().get(self.name)
        if existing is None:
            return self._create(target, self.name)
        if self._matches(existing):
            return self.name

        replacement_name = f"{self.name}__replacement"
        replacement = target.index_information().get(replacement_name)
        if replacement is None:
            self._create(target, replacement_name)
        elif not self._matches(replacement):
            target.drop_index(replacement_name)
            self._create(target, replacement_name)

        target.drop_index(self.name)
        try:
            return self._create(target, self.name)
        except Exception:
            # O \u00edndice tempor\u00e1rio continua protegendo os documentos para a pr\u00f3xima tentativa de bootstrap.
            raise
        finally:
            if self._matches(target.index_information().get(self.name, {})):
                target.drop_index(replacement_name)

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
    MongoIndex(
        MongoCollections.COMMAND_RESULTS,
        (("idempotencyKey", ASCENDING),),
        "command_results_idempotency_key_unique",
        unique=True,
    ),
)
