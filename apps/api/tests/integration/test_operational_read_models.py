"""Read-model contracts for the administrative and seller operational views."""

from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from gerec_api.auth.dependencies import get_current_user
from gerec_api.auth.permissions import DashboardService, PermissionDenied
from gerec_api.auth.sessions import CurrentUser
from gerec_api.routes.dashboard import router as dashboard_router
from gerec_api.routes.leads import router as leads_router
from gerec_api.routes.queue import router as queue_router


class Cursor:
    def __init__(self, values: list[dict[str, Any]]) -> None:
        self.values = values

    def sort(self, field: str, direction: int) -> "Cursor":
        self.values.sort(
            key=lambda value: value.get(field) or datetime.min.replace(tzinfo=UTC),
            reverse=direction < 0,
        )
        return self

    def skip(self, amount: int) -> "Cursor":
        self.values = self.values[amount:]
        return self

    def limit(self, amount: int) -> "Cursor":
        self.values = self.values[:amount]
        return self

    def __iter__(self):
        return iter(deepcopy(self.values))


class Collection:
    def __init__(self, documents: list[dict[str, Any]] | None = None) -> None:
        self.documents = documents or []

    def find(self, query: dict[str, Any], **_: Any) -> Cursor:
        return Cursor([document for document in self.documents if _matches(document, query)])

    def find_one(self, query: dict[str, Any], **_: Any) -> dict[str, Any] | None:
        return next((deepcopy(document) for document in self.documents if _matches(document, query)), None)

    def count_documents(self, query: dict[str, Any]) -> int:
        return sum(1 for _ in self.find(query))


class Database(dict[str, Collection]):
    def __getitem__(self, name: str) -> Collection:
        return super().setdefault(name, Collection())


def _matches(document: dict[str, Any], query: dict[str, Any]) -> bool:
    for field, expected in query.items():
        value = document.get(field)
        if isinstance(expected, dict) and "$in" in expected:
            if value not in expected["$in"]:
                return False
        elif value != expected:
            return False
    return True


def _database() -> Database:
    return Database(
        users=Collection(
            [
                {"_id": "seller-a", "fullName": "Renato", "active": True},
                {"_id": "seller-b", "fullName": "Sandra", "active": True},
            ]
        ),
        companies=Collection([{"_id": "company-a", "name": "Empresa Ana"}]),
        campaigns=Collection([{"_id": "campaign-a", "displayName": "Campanha WTG"}]),
        leads=Collection(
            [
                {
                    "_id": "lead-a",
                    "assigneeId": "seller-a",
                    "companyId": "company-a",
                    "campaignId": "campaign-a",
                    "contactName": "Ana da Silva",
                    "phoneNormalized": "5511987654321",
                    "emailNormalized": "ana@example.test",
                    "commercialStatus": "negotiation",
                    "isDisqualified": False,
                    "commentCount": 2,
                    "assignedAt": datetime(2026, 8, 28, 9, tzinfo=UTC),
                    "feedbackDueAt": datetime(2026, 8, 31, 15, tzinfo=UTC),
                    "updatedAt": datetime(2026, 8, 28, 12, tzinfo=UTC),
                    "createdAt": datetime(2026, 8, 28, 10, tzinfo=UTC),
                },
                {
                    "_id": "lead-b",
                    "assigneeId": "seller-b",
                    "contactName": None,
                    "phoneNormalized": None,
                    "emailNormalized": None,
                    "commercialStatus": "undefined",
                    "isDisqualified": False,
                    "commentCount": 0,
                    "assignedAt": datetime(2026, 8, 28, 11, tzinfo=UTC),
                    "feedbackDueAt": None,
                    "updatedAt": datetime(2026, 8, 28, 11, tzinfo=UTC),
                    "createdAt": datetime(2026, 8, 28, 11, tzinfo=UTC),
                },
            ]
        ),
        seller_queue=Collection(
            [
                {"_id": "queue-a", "sellerId": "seller-a", "position": 1, "paused": False},
                {"_id": "queue-b", "sellerId": "seller-b", "position": 2, "paused": False},
            ]
        ),
        queue_state=Collection([{"_id": "global", "nextSellerId": "seller-b"}]),
        skip_balances=Collection(
            [
                {"_id": "balance-a", "sellerId": "seller-a", "balance": 0},
                {"_id": "balance-b", "sellerId": "seller-b", "balance": 1},
            ]
        ),
        lead_treatments=Collection(
            [
                {
                    "_id": "treatment-old",
                    "leadId": "lead-a",
                    "sellerId": "seller-a",
                    "comment": "Primeiro contato realizado",
                    "commercialStatus": "negotiation",
                    "isDisqualified": False,
                    "idempotencyKey": "old-key",
                    "createdAt": datetime(2026, 8, 28, 10, tzinfo=UTC),
                },
                {
                    "_id": "treatment-new",
                    "leadId": "lead-a",
                    "sellerId": "seller-a",
                    "comment": "Cliente pediu retorno amanhã",
                    "commercialStatus": "negotiation",
                    "isDisqualified": False,
                    "idempotencyKey": "new-key",
                    "createdAt": datetime(2026, 8, 28, 12, tzinfo=UTC),
                },
                {
                    "_id": "treatment-b",
                    "leadId": "lead-b",
                    "sellerId": "seller-b",
                    "comment": "Tratativa exclusiva da Sandra",
                    "commercialStatus": "undefined",
                    "isDisqualified": False,
                    "idempotencyKey": "b-key",
                    "createdAt": datetime(2026, 8, 28, 13, tzinfo=UTC),
                },
            ]
        ),
    )


def _seller_a() -> CurrentUser:
    return CurrentUser("seller-a", "renato@example.test", "seller")


def _admin() -> CurrentUser:
    return CurrentUser("admin-1", "yago@example.test", "admin")


def test_admin_lead_projection_is_human_readable_and_omits_internal_foreign_keys() -> None:
    payload = DashboardService(_database()).for_user(_admin())
    lead = next(item for item in payload["leads"]["items"] if item["id"] == "lead-a")

    assert lead == {
        "id": "lead-a",
        "contactName": "Ana da Silva",
        "sellerName": "Renato",
        "companyName": "Empresa Ana",
        "campaignName": "Campanha WTG",
        "phoneDisplay": "11987654321",
        "email": "ana@example.test",
        "commercialStatus": "negotiation",
        "isDisqualified": False,
        "commentCount": 2,
        "assignedAt": "2026-08-28T09:00:00+00:00",
        "feedbackDueAt": "2026-08-31T15:00:00+00:00",
        "lastUpdatedAt": "2026-08-28T12:00:00+00:00",
    }
    assert {"assigneeId", "companyId", "campaignId", "phoneNormalized"}.isdisjoint(lead)


def test_missing_names_and_contact_data_use_the_single_safe_fallback() -> None:
    payload = DashboardService(_database()).for_user(_admin())
    lead = next(item for item in payload["leads"]["items"] if item["id"] == "lead-b")

    assert lead["contactName"] == "Não informado"
    assert lead["companyName"] == "Não informado"
    assert lead["campaignName"] == "Não informado"
    assert lead["phoneDisplay"] == "Não informado"
    assert lead["email"] == "Não informado"


def test_seller_projection_never_exposes_colleagues_or_global_queue_totals() -> None:
    payload = DashboardService(_database()).for_user(_seller_a())

    assert [lead["id"] for lead in payload["leads"]["items"]] == ["lead-a"]
    assert payload["queue"] == {
        "position": 1,
        "availability": "active",
        "skipBalance": 0,
    }
    assert "reason" not in payload["queue"]
    assert "nextSellerName" not in payload["queue"]
    assert "cursorSellerName" not in payload["queue"]
    assert "items" not in payload["queue"]
    assert "total" not in payload["queue"]
    assert "skipBalance" not in payload


def test_admin_queue_exposes_the_persisted_cursor_without_its_technical_identifier() -> None:
    queue = DashboardService(_database()).for_user(_admin())["queue"]

    assert queue["cursorSellerName"] == "Sandra"
    assert queue["nextSellerName"] == "Renato"
    assert [item["sellerName"] for item in queue["items"]] == ["Renato", "Sandra"]
    assert all("sellerId" not in item for item in queue["items"])


def test_admin_treatments_are_paginated_descending_and_seller_cannot_read_another_lead() -> None:
    service = DashboardService(_database())

    treatments = service.lead_treatments_for_user("lead-a", _admin(), page=1, limit=1)
    assert treatments == {
        "items": [
            {
                "leadId": "lead-a",
                "comment": "Cliente pediu retorno amanhã",
                "commercialStatus": "negotiation",
                "isDisqualified": False,
                "sellerName": "Renato",
                "createdAt": "2026-08-28T12:00:00+00:00",
                "assignedAt": "2026-08-28T09:00:00+00:00",
                "lastUpdatedAt": "2026-08-28T12:00:00+00:00",
            }
        ],
        "page": 1,
        "pageSize": 1,
        "total": 2,
    }

    with pytest.raises(PermissionDenied):
        service.lead_treatments_for_user("lead-b", _seller_a())


def test_read_endpoints_enforce_the_same_role_contract() -> None:
    database = _database()
    app = FastAPI()
    app.state.dashboard_service = DashboardService(database)
    app.include_router(dashboard_router)
    app.include_router(leads_router)
    app.include_router(queue_router)
    app.dependency_overrides[get_current_user] = _seller_a
    client = TestClient(app)

    dashboard = client.get("/api/dashboard")
    queue = client.get("/api/queue")
    other_treatments = client.get("/api/leads/lead-b/treatments")

    assert dashboard.status_code == 200
    assert queue.status_code == 200
    assert queue.json()["position"] == 1
    assert "nextSellerName" not in queue.json()
    assert other_treatments.status_code == 403
