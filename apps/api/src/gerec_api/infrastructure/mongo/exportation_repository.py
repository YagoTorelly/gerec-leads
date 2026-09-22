"""MongoDB read model and history persistence for lead exportations."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from typing import Any, Mapping

from bson import ObjectId

from gerec_api.infrastructure.mongo.collections import MongoCollections


NOT_INFORMED = "Não informado"


class MongoExportationRepository:
    def __init__(self, database: Any) -> None:
        self._database = database

    def list_leads(self, filters: dict[str, Any]) -> list[dict[str, Any]]:
        query = dict(filters)
        cursor = self._database[MongoCollections.LEADS].find(query)
        if hasattr(cursor, "sort"):
            cursor = cursor.sort([("createdAt", -1), ("_id", 1)])
        leads = list(cursor)
        users = self._references(MongoCollections.USERS, leads, "assigneeId")
        campaigns = self._references(MongoCollections.CAMPAIGNS, leads, "campaignId")
        return [self._lead_projection(lead, users, campaigns) for lead in leads]

    def record_exportation(
        self,
        *,
        attempt_id: str,
        actor_id: str,
        administrator_fallback: str,
        lead_count: int,
        filters: dict[str, Any],
        status: str,
        created_at: datetime,
        error_code: str | None = None,
    ) -> str:
        if status not in {"success", "error"}:
            raise ValueError("exportation status is invalid")
        administrator = self._find_by_id(MongoCollections.USERS, actor_id)
        administrator_name = _name(administrator, administrator_fallback)
        document = {
            "attemptId": attempt_id,
            "actorId": actor_id,
            "administratorName": administrator_name,
            "leadCount": int(lead_count),
            "filters": deepcopy(filters),
            "status": status,
            "createdAt": created_at,
        }
        if error_code is not None:
            document["errorCode"] = error_code
        collection = self._database[MongoCollections.EXPORTATIONS]
        collection.update_one(
            {"attemptId": attempt_id},
            {"$setOnInsert": document},
            upsert=True,
        )
        final_status = self.get_exportation_status(attempt_id)
        if final_status is None:
            raise RuntimeError("exportation result was not persisted")
        return final_status

    def get_exportation_status(self, attempt_id: str) -> str | None:
        document = self._database[MongoCollections.EXPORTATIONS].find_one(
            {"attemptId": attempt_id}
        )
        if document is None:
            return None
        status = str(document.get("status", ""))
        if status not in {"success", "error"}:
            raise RuntimeError("persisted exportation status is invalid")
        return status

    def list_exportations(self, *, page: int, limit: int) -> dict[str, Any]:
        collection = self._database[MongoCollections.EXPORTATIONS]
        cursor = collection.find({})
        if hasattr(cursor, "sort"):
            cursor = cursor.sort("createdAt", -1)
        if hasattr(cursor, "skip"):
            cursor = cursor.skip((page - 1) * limit)
        if hasattr(cursor, "limit"):
            cursor = cursor.limit(limit)
        items = [
            {
                "createdAt": item.get("createdAt"),
                "administratorName": _text(item.get("administratorName"), NOT_INFORMED),
                "leadCount": int(item.get("leadCount", 0)),
                "filters": deepcopy(item.get("filters") or {}),
                "status": str(item.get("status", "error")),
            }
            for item in cursor
        ]
        total = collection.count_documents({}) if hasattr(collection, "count_documents") else len(items)
        return {"items": items, "page": page, "pageSize": limit, "total": total}

    def _lead_projection(
        self,
        lead: Mapping[str, Any],
        users: dict[str, Mapping[str, Any]],
        campaigns: dict[str, Mapping[str, Any]],
    ) -> dict[str, Any]:
        seller = users.get(str(lead.get("assigneeId")))
        campaign = campaigns.get(str(lead.get("campaignId")))
        return {
            "leadId": str(lead.get("_id", "")),
            "manualQueueLeadId": lead.get("manualQueueLeadId"),
            "name": lead.get("contactName") or lead.get("name") or NOT_INFORMED,
            "assigneeName": _name(seller, NOT_INFORMED),
            "phone": self._phone(lead),
            "email": lead.get("email") or lead.get("emailNormalized") or NOT_INFORMED,
            "campaign": (
                lead.get("campaignName")
                or (campaign or {}).get("displayName")
                or (campaign or {}).get("sourceName")
                or NOT_INFORMED
            ),
            "origin": lead.get("origin") or lead.get("adName") or lead.get("adExternalId") or NOT_INFORMED,
            "commercialStatus": _commercial_status(lead),
            "isDisqualified": bool(lead.get("isDisqualified", False)),
            "createdAt": lead.get("createdAt") or lead.get("sourceEnteredAt"),
            "assignedAt": lead.get("assignedAt"),
            "updatedAt": lead.get("lastCommentAt") or lead.get("updatedAt") or lead.get("assignedAt"),
            "sourceType": "manual" if lead.get("source") == "manual" else "automatico",
        }

    def _references(
        self,
        collection_name: str,
        leads: list[Mapping[str, Any]],
        field: str,
    ) -> dict[str, Mapping[str, Any]]:
        values = [candidate for lead in leads for candidate in _identity_values(lead.get(field))]
        unique_values = list(dict.fromkeys(candidate for candidate in values if candidate is not None))
        if not unique_values:
            return {}
        documents = self._database[collection_name].find({"_id": {"$in": unique_values}})
        return {
            str(candidate): document
            for document in documents
            for candidate in _identity_values(document.get("_id"))
        }

    def _find_by_id(self, collection_name: str, value: Any) -> Mapping[str, Any] | None:
        for candidate in _identity_values(value):
            item = self._database[collection_name].find_one({"_id": candidate})
            if item is not None:
                return item
        return None

    def _phone(self, lead: Mapping[str, Any]) -> str:
        direct = _phone_from_mapping(lead, include_normalized=False)
        if direct is not None:
            return str(direct)
        sources = self._database[MongoCollections.SOURCE_RECORDS]
        source = None
        for candidate in _identity_values(lead.get("_id")):
            source = sources.find_one({"leadId": candidate})
            if source is not None:
                inherited = _phone_from_mapping(source, include_normalized=False)
                if inherited is not None:
                    return str(inherited)
                break
        normalized = _phone_from_mapping(lead, include_normalized=True)
        if normalized is not None:
            return str(normalized)
        if source is not None:
            normalized = _phone_from_mapping(source, include_normalized=True)
            if normalized is not None:
                return str(normalized)
        return NOT_INFORMED


def _identity_values(value: Any) -> list[Any]:
    if value is None:
        return []
    values = [value]
    if isinstance(value, str) and ObjectId.is_valid(value):
        values.append(ObjectId(value))
    elif isinstance(value, ObjectId):
        values.append(str(value))
    return values


def _name(document: Mapping[str, Any] | None, fallback: str) -> str:
    return _text(
        (document or {}).get("fullName")
        or (document or {}).get("name")
        or (document or {}).get("emailNormalized"),
        fallback,
    )


def _text(value: Any, fallback: str) -> str:
    text = str(value).strip() if value is not None else ""
    return text or fallback


def _commercial_status(lead: Mapping[str, Any]) -> str:
    status = lead.get("commercialStatus")
    if status in {"undefined", "potential", "negotiation", "won"}:
        return str(status)
    if lead.get("conversionStatus") == "won":
        return "won"
    if lead.get("qualificationStatus") in {"qualified", "in_negotiation", "negotiation"}:
        return "negotiation"
    return "undefined"


_PHONE_FIELDS = ("phone", "phoneNumber", "phone_number", "telefone")
_PHONE_CONTAINERS = (
    "sourceProjection",
    "sourcePayload",
    "sellerProjection",
    "payload",
    "projection",
    "row",
    "data",
    "fields",
)


def _phone_from_mapping(
    value: Any,
    *,
    include_normalized: bool,
    depth: int = 0,
) -> Any:
    if not isinstance(value, Mapping) or depth > 4:
        return None
    fields = (*_PHONE_FIELDS, "phoneNormalized") if include_normalized else _PHONE_FIELDS
    for field in fields:
        candidate = value.get(field)
        if candidate is not None and str(candidate).strip():
            return candidate
    for field in _PHONE_CONTAINERS:
        candidate = _phone_from_mapping(
            value.get(field),
            include_normalized=include_normalized,
            depth=depth + 1,
        )
        if candidate is not None:
            return candidate
    return None
