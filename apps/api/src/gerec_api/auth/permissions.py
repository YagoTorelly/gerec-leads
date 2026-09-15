"""Centralized authorization and role-specific operational read models."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Mapping

from bson import ObjectId

from gerec_api.auth.sessions import CurrentUser
from gerec_api.domain.queue import QueueSnapshot
from gerec_api.infrastructure.mongo.collections import MongoCollections
from gerec_api.infrastructure.mongo.queue_repository import QueueRepository
from gerec_api.infrastructure.mongo.serialization import serialize_bson


NOT_INFORMED = "Não informado"


class PermissionDenied(PermissionError):
    """Raised when a command or query is outside the current user's scope."""


class PermissionService:
    """Pure policy boundary; callers must provide the authenticated user."""

    @staticmethod
    def require_current_user(user: CurrentUser | None) -> CurrentUser:
        if not isinstance(user, CurrentUser) or not user.id or user.role not in {"admin", "seller"}:
            raise PermissionDenied("authenticated user is required")
        return user

    @classmethod
    def require_admin(cls, user: CurrentUser | None) -> None:
        current = cls.require_current_user(user)
        if current.role != "admin":
            raise PermissionDenied("administrator role is required")

    @classmethod
    def scope_query(cls, user: CurrentUser | None, resource: str) -> dict[str, Any]:
        """Return a server-side Mongo filter; seller identity only comes from session."""
        current = cls.require_current_user(user)
        if resource not in {
            "leads", "history", "queue", "skip_balance", "companies", "campaigns",
            "users", "audit", "treatments",
        }:
            raise ValueError(f"unknown protected resource: {resource}")
        if current.role == "admin":
            return {}
        ids = _identity_values(current.id)
        if resource == "leads":
            return {"assigneeId": {"$in": ids}}
        if resource in {"history", "treatments"}:
            return {"sellerId": {"$in": ids}}
        if resource in {"queue", "skip_balance"}:
            return {"sellerId": {"$in": ids}}
        raise PermissionDenied(f"seller cannot read {resource}")

    @classmethod
    def dashboard_lead_scope(
        cls, user: CurrentUser | None, *, assignee_id: str | None = None
    ) -> dict[str, Any]:
        """Build the dashboard lead scope without accepting a seller's override."""
        current = cls.require_current_user(user)
        if current.role != "admin":
            return cls.scope_query(current, "leads")
        if assignee_id is None:
            return {}
        requested_id = assignee_id.strip()
        if not requested_id:
            raise ValueError("assigneeId must not be empty")
        return {"assigneeId": {"$in": _identity_values(requested_id)}}


class DashboardService:
    """Read-model boundary with intentionally different contracts for each role.

    The service contains no command logic. Queue availability is delegated to the
    Task 5 repository snapshot so the read model cannot invent an eligibility rule.
    """

    def __init__(
        self,
        database: Any,
        *,
        page_size: int = 50,
        queue_snapshot: Any | None = None,
    ) -> None:
        self._database = database
        self._page_size = max(1, min(page_size, 200))
        self._queue_snapshot = queue_snapshot or QueueRepository(database).snapshot

    def for_user(
        self,
        user: CurrentUser | None,
        *,
        page: int = 1,
        limit: int | None = None,
        assignee_id: str | None = None,
        sort: str | None = None,
    ) -> dict[str, Any]:
        current = PermissionService.require_current_user(user)
        return (
            self.for_admin(
                current,
                page=page,
                limit=limit,
                assignee_id=assignee_id,
                sort=sort,
            )
            if current.role == "admin"
            else self.for_seller(
                current,
                page=page,
                limit=limit,
                assignee_id=assignee_id,
                sort=sort,
            )
        )

    def for_admin(
        self,
        user: CurrentUser | None,
        *,
        page: int = 1,
        limit: int | None = None,
        assignee_id: str | None = None,
        sort: str | None = None,
    ) -> dict[str, Any]:
        PermissionService.require_admin(user)
        current = PermissionService.require_current_user(user)
        page, page_size = self._pagination(page, limit)
        return {
            "user": _public_user(current),
            "leads": self._lead_page(
                PermissionService.dashboard_lead_scope(current, assignee_id=assignee_id),
                page,
                page_size,
                sort=sort,
            ),
            "history": self._treatment_page({}, page, page_size, include_lead_name=True),
            "queue": self._admin_queue(),
        }

    def for_seller(
        self,
        user: CurrentUser | None,
        *,
        page: int = 1,
        limit: int | None = None,
        assignee_id: str | None = None,
        sort: str | None = None,
    ) -> dict[str, Any]:
        current = PermissionService.require_current_user(user)
        if current.role != "seller":
            raise PermissionDenied("seller role is required")
        page, page_size = self._pagination(page, limit)
        return {
            "user": _public_user(current),
            "leads": self._lead_page(
                PermissionService.dashboard_lead_scope(current, assignee_id=assignee_id),
                page,
                page_size,
                sort=sort,
            ),
            "history": self._treatment_page(
                self._seller_history_query(current),
                page,
                page_size,
                include_lead_name=True,
            ),
            "queue": self._seller_queue(current),
        }

    def _seller_history_query(self, user: CurrentUser) -> dict[str, Any]:
        """Limit seller history to leads they currently own after transfers."""
        lead_ids = [
            lead.get("_id")
            for lead in self._database[MongoCollections.LEADS].find(
                PermissionService.scope_query(user, "leads")
            )
            if lead.get("_id") is not None
        ]
        return {
            "sellerId": {"$in": _identity_values(user.id)},
            "leadId": {"$in": lead_ids},
        }

    def queue_for_user(self, user: CurrentUser | None) -> dict[str, Any]:
        current = PermissionService.require_current_user(user)
        return self._admin_queue() if current.role == "admin" else self._seller_queue(current)

    def lead_treatments_for_user(
        self,
        lead_id: str,
        user: CurrentUser | None,
        *,
        page: int = 1,
        limit: int | None = None,
    ) -> dict[str, Any]:
        current = PermissionService.require_current_user(user)
        page, page_size = self._pagination(page, limit)
        lead = self._find_by_id(MongoCollections.LEADS, lead_id)
        if lead is None:
            raise PermissionDenied("lead is outside current user scope")

        query: dict[str, Any] = {"leadId": {"$in": _identity_values(lead_id)}}
        if current.role == "seller":
            seller_query = PermissionService.scope_query(current, "treatments")
            current_owner = lead.get("assigneeId") in _identity_values(current.id)
            if not current_owner:
                raise PermissionDenied("lead is outside current user scope")
            query.update(seller_query)
        return self._treatment_page(query, page, page_size, include_lead_name=False)

    def _pagination(self, page: int, limit: int | None) -> tuple[int, int]:
        return _page_number(page), _page_limit(self._page_size if limit is None else limit)

    def lead_distribution(
        self,
        user: CurrentUser | None,
        *,
        from_at: datetime,
        to_at: datetime,
    ) -> dict[str, Any]:
        """Aggregate current lead ownership by situation in an assignment interval."""
        PermissionService.require_admin(user)
        from_utc = _as_utc(from_at, name="fromAt")
        to_utc = _as_utc(to_at, name="toAt")
        if from_utc >= to_utc:
            raise ValueError("fromAt must be earlier than toAt")
        leads = list(
            self._database[MongoCollections.LEADS].find(
                {"assignedAt": {"$gte": from_utc, "$lt": to_utc}}
            )
        )
        by_situation: dict[str, int] = {}
        by_seller: dict[str, dict[str, Any]] = {}
        seller_ids: list[Any] = []
        for lead in leads:
            situation = _commercial_status(lead)
            by_situation[situation] = by_situation.get(situation, 0) + 1
            assignee_id = lead.get("assigneeId")
            if assignee_id is None:
                continue
            seller_id = str(assignee_id)
            by_seller[seller_id] = {
                "sellerId": seller_id,
                "sellerName": NOT_INFORMED,
                "count": by_seller.get(seller_id, {}).get("count", 0) + 1,
            }
            seller_ids.extend(_identity_values(assignee_id))

        users = self._database[MongoCollections.USERS].find(
            {"_id": {"$in": list(dict.fromkeys(seller_ids))}}
        ) if seller_ids else []
        names = {
            str(candidate): _name_or_fallback(document)
            for document in users
            for candidate in _identity_values(document.get("_id"))
        }
        for seller in by_seller.values():
            seller["sellerName"] = names.get(seller["sellerId"], NOT_INFORMED)

        return {
            "period": {"from": from_utc.isoformat(), "to": to_utc.isoformat()},
            "bySituation": [
                {"commercialStatus": situation, "count": count}
                for situation, count in sorted(by_situation.items())
            ],
            "bySeller": sorted(
                by_seller.values(), key=lambda item: (item["sellerName"], item["sellerId"])
            ),
        }

    def _lead_page(
        self,
        query: Mapping[str, Any],
        page: int,
        page_size: int,
        *,
        sort: str | None = None,
    ) -> dict[str, Any]:
        collection = self._database[MongoCollections.LEADS]
        cursor = collection.find(dict(query))
        if sort == "situation":
            leads = list(cursor)
            leads.sort(key=lambda lead: str(lead.get("_id") or ""))
            leads.sort(key=_lead_created_at_sort_value, reverse=True)
            leads.sort(key=lambda lead: _situation_sort_rank(_commercial_status(lead)))
            leads = leads[(page - 1) * page_size : page * page_size]
        else:
            if hasattr(cursor, "sort"):
                cursor = cursor.sort(_lead_sort(sort))
            if hasattr(cursor, "skip"):
                cursor = cursor.skip((page - 1) * page_size)
            if hasattr(cursor, "limit"):
                cursor = cursor.limit(page_size)
            leads = list(cursor)
        references = self._lead_references(leads)
        items = [self._lead_projection(lead, references=references) for lead in leads]
        total = collection.count_documents(dict(query)) if hasattr(collection, "count_documents") else len(items)
        return {"items": items, "page": page, "pageSize": page_size, "total": total}

    def _lead_references(self, leads: list[Mapping[str, Any]]) -> dict[str, dict[str, Mapping[str, Any]]]:
        """Load all lead enrichment references with one query per collection."""
        ids_by_collection: dict[str, list[Any]] = {
            MongoCollections.USERS: [],
            MongoCollections.COMPANIES: [],
            MongoCollections.CAMPAIGNS: [],
        }
        for lead in leads:
            for collection_name, field in (
                (MongoCollections.USERS, "assigneeId"),
                (MongoCollections.COMPANIES, "companyId"),
                (MongoCollections.CAMPAIGNS, "campaignId"),
            ):
                value = lead.get(field)
                if value is not None:
                    ids_by_collection[collection_name].extend(_identity_values(value))

        references: dict[str, dict[str, Mapping[str, Any]]] = {}
        for collection_name, values in ids_by_collection.items():
            unique_values = list(dict.fromkeys(values))
            if not unique_values:
                references[collection_name] = {}
                continue
            collection = self._database[collection_name]
            documents = collection.find({"_id": {"$in": unique_values}})
            references[collection_name] = {
                str(candidate): document
                for document in documents
                for candidate in _identity_values(document.get("_id"))
            }
        return references

    def _treatment_page(
        self,
        query: Mapping[str, Any],
        page: int,
        page_size: int,
        *,
        include_lead_name: bool,
    ) -> dict[str, Any]:
        collection = self._database[MongoCollections.LEAD_TREATMENTS]
        cursor = collection.find(dict(query))
        if hasattr(cursor, "sort"):
            cursor = cursor.sort("createdAt", -1)
        if hasattr(cursor, "skip"):
            cursor = cursor.skip((page - 1) * page_size)
        if hasattr(cursor, "limit"):
            cursor = cursor.limit(page_size)
        treatments = list(cursor)
        references = self._treatment_references(treatments)
        items = [
            self._treatment_projection(
                treatment,
                include_lead_name=include_lead_name,
                references=references,
            )
            for treatment in treatments
        ]
        total = collection.count_documents(dict(query)) if hasattr(collection, "count_documents") else len(items)
        return {"items": items, "page": page, "pageSize": page_size, "total": total}

    def _treatment_references(self, treatments: list[Mapping[str, Any]]) -> dict[str, dict[str, Mapping[str, Any]]]:
        ids_by_collection: dict[str, list[Any]] = {
            MongoCollections.USERS: [],
            MongoCollections.LEADS: [],
        }
        for treatment in treatments:
            ids_by_collection[MongoCollections.USERS].extend(_identity_values(treatment.get("sellerId")))
            ids_by_collection[MongoCollections.LEADS].extend(_identity_values(treatment.get("leadId")))

        references: dict[str, dict[str, Mapping[str, Any]]] = {}
        for collection_name, values in ids_by_collection.items():
            unique_values = list(dict.fromkeys(value for value in values if value is not None))
            if not unique_values:
                references[collection_name] = {}
                continue
            documents = self._database[collection_name].find({"_id": {"$in": unique_values}})
            references[collection_name] = {
                str(candidate): document
                for document in documents
                for candidate in _identity_values(document.get("_id"))
            }
        return references

    def _page(
        self,
        collection_name: str,
        query: Mapping[str, Any],
        page: int,
        page_size: int,
        projection: Any,
    ) -> dict[str, Any]:
        collection = self._database[collection_name]
        cursor = collection.find(dict(query))
        if hasattr(cursor, "sort"):
            cursor = cursor.sort("createdAt", -1)
        if hasattr(cursor, "skip"):
            cursor = cursor.skip((page - 1) * page_size)
        if hasattr(cursor, "limit"):
            cursor = cursor.limit(page_size)
        items = [projection(item) for item in cursor]
        total = collection.count_documents(dict(query)) if hasattr(collection, "count_documents") else len(items)
        return {"items": items, "page": page, "pageSize": page_size, "total": total}

    def _lead_projection(
        self,
        lead: Mapping[str, Any],
        *,
        references: dict[str, dict[str, Mapping[str, Any]]] | None = None,
    ) -> dict[str, Any]:
        if references is None:
            references = self._lead_references([lead])
        company = references[MongoCollections.COMPANIES].get(str(lead.get("companyId")))
        campaign = references[MongoCollections.CAMPAIGNS].get(str(lead.get("campaignId")))
        seller = references[MongoCollections.USERS].get(str(lead.get("assigneeId")))
        return _serialize_read_model(
            {
                "id": str(lead["_id"]),
                "contactName": _text_or_fallback(lead.get("contactName")),
                "sellerName": _name_or_fallback(seller),
                "companyName": _company_name(company),
                "campaignName": _campaign_name(campaign),
                "phoneDisplay": _phone_without_country_code(self._lead_phone_value(lead)),
                "email": _text_or_fallback(lead.get("email") or lead.get("emailNormalized")),
                "commercialStatus": _commercial_status(lead),
                "isDisqualified": bool(lead.get("isDisqualified", False)),
                "commentCount": int(lead.get("commentCount", 0)),
                "assignedAt": lead.get("assignedAt"),
                "lastUpdatedAt": lead.get("lastCommentAt")
                or lead.get("updatedAt")
                or lead.get("assignedAt"),
            }
        )

    def _treatment_projection(
        self,
        treatment: Mapping[str, Any],
        *,
        include_lead_name: bool,
        references: dict[str, dict[str, Mapping[str, Any]]] | None = None,
    ) -> dict[str, Any]:
        references = references or self._treatment_references([treatment])
        seller = references[MongoCollections.USERS].get(str(treatment.get("sellerId")))
        lead = references[MongoCollections.LEADS].get(str(treatment.get("leadId")))
        result: dict[str, Any] = {
            "leadId": str(treatment.get("leadId")),
            "sellerName": _name_or_fallback(seller),
            "comment": _text_or_fallback(treatment.get("comment")),
            "commercialStatus": _commercial_status(treatment),
            "isDisqualified": bool(treatment.get("isDisqualified", False)),
            "assignedAt": (lead or {}).get("assignedAt"),
            "createdAt": treatment.get("createdAt"),
            "lastUpdatedAt": (
                (lead or {}).get("lastCommentAt")
                or (lead or {}).get("updatedAt")
                or (lead or {}).get("assignedAt")
            ),
        }
        if include_lead_name:
            result["leadName"] = _text_or_fallback((lead or {}).get("contactName"))
        return _serialize_read_model(result)

    def _admin_queue(self) -> dict[str, Any]:
        snapshot = self._snapshot()
        entries = []
        for position, entry in enumerate(snapshot.entries, start=1):
            seller = self._find_by_id(MongoCollections.USERS, entry.seller_id)
            entries.append(
                {
                    "sellerName": _name_or_fallback(seller),
                    "position": position,
                    "availability": entry.availability.status,
                    "reason": entry.availability.reason,
                    "skipBalance": entry.skip_balance,
                }
            )
        return {
            "items": entries,
            "total": len(entries),
            "nextSellerName": entries[0]["sellerName"] if entries else NOT_INFORMED,
            "cursorSellerName": _name_or_fallback(
                self._find_by_id(MongoCollections.USERS, snapshot.cursor_seller_id)
            ),
        }

    def _seller_queue(self, user: CurrentUser) -> dict[str, Any]:
        for position, entry in enumerate(self._snapshot().entries, start=1):
            if entry.seller_id in _identity_values(user.id):
                return {
                    "position": position,
                    "availability": entry.availability.status,
                    "skipBalance": entry.skip_balance,
                }
        # A seller can remain authenticated while an administrative migration or
        # deactivation has removed it from the queue. This is its own state, not
        # a reason to disclose the global queue or fail the complete dashboard.
        return {"position": None, "availability": "paused", "skipBalance": 0}

    def _snapshot(self) -> QueueSnapshot:
        return self._queue_snapshot()

    def _find_by_id(self, collection_name: str, value: Any) -> Mapping[str, Any] | None:
        if value is None:
            return None
        collection = self._database[collection_name]
        for candidate in _identity_values(value):
            item = collection.find_one({"_id": candidate})
            if item is not None:
                return item
        return None

    def _lead_phone_value(self, lead: Mapping[str, Any]) -> Any:
        """Read the canonical phone, tolerating source records from older imports.

        Current imports persist ``phoneNormalized`` on the lead.  Some already
        persisted snapshots retain the original value only in ``source_records``;
        reading those fields keeps the read model useful without changing the
        source contract or mutating data during a GET.
        """
        value = _phone_from_mapping(lead)
        if value is not None:
            return value

        source_records = self._database[MongoCollections.SOURCE_RECORDS]
        source = _find_source_record(source_records, lead)
        if source is None:
            return None
        return _phone_from_mapping(source)


def _identity_values(value: Any) -> list[Any]:
    values: list[Any] = [value]
    if isinstance(value, str) and ObjectId.is_valid(value):
        values.append(ObjectId(value))
    elif isinstance(value, ObjectId):
        values.append(str(value))
    return values


_PHONE_FIELDS = ("phoneNormalized", "phoneNumber", "phone_number", "phone", "telefone")
_PHONE_CONTAINERS = (
    "sourceProjection",
    "sourcePayload",
    "sellerProjection",
    "payload",
    "projection",
    "source_projection",
    "source_payload",
    "row",
    "data",
    "fields",
)
_SOURCE_LINK_FIELDS = ("leadId", "lead_id", "sourceLeadId", "source_lead_id")


def _phone_from_mapping(value: Any, *, depth: int = 0) -> Any:
    """Extract only known phone aliases from known persisted containers."""
    if not isinstance(value, Mapping) or depth > 4:
        return None
    for field in _PHONE_FIELDS:
        candidate = value.get(field)
        if candidate is not None and str(candidate).strip():
            return candidate
    for field in _PHONE_CONTAINERS:
        candidate = value.get(field)
        found = _phone_from_mapping(candidate, depth=depth + 1)
        if found is not None:
            return found
    return None


def _find_source_record(collection: Any, lead: Mapping[str, Any]) -> Mapping[str, Any] | None:
    """Resolve source records across current and legacy link field names."""
    lead_values: list[Any] = []
    for field in ("_id", "id", "sourceLeadId", "source_lead_id"):
        candidate = lead.get(field)
        if candidate is not None:
            lead_values.extend(_identity_values(candidate))
    seen: set[str] = set()
    for link_field in _SOURCE_LINK_FIELDS:
        for candidate in lead_values:
            marker = f"{link_field}:{candidate!r}"
            if marker in seen:
                continue
            seen.add(marker)
            source = collection.find_one({link_field: candidate})
            if source is not None:
                return source
    return None


def _public_user(user: CurrentUser) -> dict[str, str]:
    return {"id": user.id, "email": user.email, "role": user.role}


def _text_or_fallback(value: Any) -> str:
    text = str(value).strip() if value is not None else ""
    return text or NOT_INFORMED


def _name_or_fallback(document: Mapping[str, Any] | None) -> str:
    value = (document or {}).get("fullName") or (document or {}).get("name") or (document or {}).get("email")
    return _text_or_fallback(value)


def _company_name(document: Mapping[str, Any] | None) -> str:
    return _text_or_fallback((document or {}).get("name") or (document or {}).get("legalName"))


def _campaign_name(document: Mapping[str, Any] | None) -> str:
    return _text_or_fallback(
        (document or {}).get("displayName")
        or (document or {}).get("sourceName")
        or (document or {}).get("name")
    )


def _phone_without_country_code(value: Any) -> str:
    digits = "".join(character for character in str(value or "") if character.isdigit())
    if digits.startswith("55") and len(digits) in {12, 13}:
        digits = digits[2:]
    return digits or NOT_INFORMED


def _commercial_status(document: Mapping[str, Any]) -> str:
    direct = document.get("commercialStatus")
    if direct in {"undefined", "potential", "negotiation", "won"}:
        return str(direct)
    if document.get("conversionStatus") == "won":
        return "won"
    if document.get("qualificationStatus") in {"qualified", "in_negotiation", "negotiation"}:
        return "negotiation"
    return "undefined"


def _lead_sort(sort: str | None) -> list[tuple[str, int]]:
    if sort is None:
        return [("createdAt", -1)]
    if sort != "situation":
        raise ValueError("sort must be situation")
    return [("createdAt", -1), ("_id", 1)]


_SITUATION_SORT_ORDER = {"won": 0, "undefined": 1, "negotiation": 2, "potential": 3}


def _situation_sort_rank(status: str) -> int:
    return _SITUATION_SORT_ORDER[status]


def _lead_created_at_sort_value(lead: Mapping[str, Any]) -> float:
    value = lead.get("createdAt")
    if isinstance(value, datetime):
        return value.replace(tzinfo=UTC).timestamp() if value.tzinfo is None else value.timestamp()
    return float("-inf")


def _as_utc(value: datetime, *, name: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must include a timezone")
    return value.astimezone(UTC)


def _page_number(value: int) -> int:
    if value < 1:
        raise ValueError("page must be at least 1")
    return value


def _page_limit(value: int) -> int:
    if value < 1 or value > 200:
        raise ValueError("limit must be between 1 and 200")
    return value


def _serialize_read_model(value: Mapping[str, Any]) -> dict[str, Any]:
    return serialize_bson(
        {
            key: item.isoformat() if isinstance(item, datetime) else item
            for key, item in value.items()
        }
    )
