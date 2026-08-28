from datetime import UTC, datetime

import pytest
from bson import ObjectId
from fastapi import FastAPI
from fastapi.testclient import TestClient

from gerec_api.auth.dependencies import get_current_user
from gerec_api.auth.permissions import DashboardService, PermissionService, PermissionDenied
from gerec_api.auth.sessions import CurrentUser
from gerec_api.routes.admin import router as admin_router


class Collection:
    def __init__(self, documents):
        self.documents = documents

    def find(self, query):
        values = self.documents
        for field in ("sellerId", "assigneeId"):
            if field in query:
                expected = query[field].get("$in", [query[field]])
                values = [item for item in values if item.get(field) in expected]
        return Cursor(values)

    def count_documents(self, query):
        return sum(1 for _ in self.find(query))

    def find_one(self, query):
        return self.documents[0] if self.documents else None


class Cursor:
    def __init__(self, values):
        self.values = values

    def sort(self, *_):
        return self

    def skip(self, amount):
        self.values = self.values[amount:]
        return self

    def limit(self, amount):
        self.values = self.values[:amount]
        return self

    def __iter__(self):
        return iter(self.values)


class Database(dict):
    def __getitem__(self, key):
        return super().setdefault(key, Collection([]))


def test_dashboard_reads_are_paginated_and_expose_audit_ready_ids():
    database = Database()
    database["leads"] = Collection([{"_id": "lead-1", "assigneeId": "seller-1"}])
    payload = DashboardService(database).for_user(
        CurrentUser("seller-1", "seller@example.test", "seller")
    )
    assert payload["leads"]["items"][0]["id"] == "lead-1"
    assert payload["leads"]["page"] == 1
    assert payload["leads"]["pageSize"] == 50


def test_dashboard_serializes_nested_bson_identifiers() -> None:
    """Breaks if a real Mongo document reaches FastAPI with a nested ObjectId."""
    database = Database()
    seller_id = ObjectId()
    company_id = ObjectId()
    database["leads"] = Collection(
        [
            {
                "_id": ObjectId(),
                "assigneeId": seller_id,
                "companyId": company_id,
                "metadata": {"relatedIds": [ObjectId()]},
            }
        ]
    )

    payload = DashboardService(database).for_user(
        CurrentUser(str(seller_id), "seller@example.test", "seller")
    )

    item = payload["leads"]["items"][0]
    assert item["assigneeId"] == str(seller_id)
    assert item["companyId"] == str(company_id)
    assert isinstance(item["metadata"]["relatedIds"][0], str)


def test_dashboard_enriches_operational_rows_with_human_labels() -> None:
    database = Database()
    database["leads"] = Collection([{"_id": "lead-1", "assigneeId": "seller-1", "companyId": "company-1", "campaignId": "campaign-1", "contactName": "Ana", "emailNormalized": "ana@example.test"}])
    database["users"] = Collection([{"_id": "seller-1", "fullName": "Renato"}])
    database["companies"] = Collection([{"_id": "company-1", "name": "Empresa Ana"}])
    database["campaigns"] = Collection([{"_id": "campaign-1", "displayName": "Campanha WTG"}])
    payload = DashboardService(database).for_user(CurrentUser("seller-1", "renato@example.test", "seller"))
    item = payload["leads"]["items"][0]
    assert item["sellerName"] == "Renato"
    assert item["companyName"] == "Empresa Ana"
    assert item["campaignName"] == "Campanha WTG"
    assert item["email"] == "ana@example.test"


def test_dashboard_page_two_skips_first_page():
    database = Database()
    database["leads"] = Collection([{"_id": f"lead-{i}", "assigneeId": "seller-1"} for i in range(3)])
    payload = DashboardService(database).for_user(
        CurrentUser("seller-1", "seller@example.test", "seller"), page=2, limit=2
    )
    assert [item["id"] for item in payload["leads"]["items"]] == ["lead-2"]
    assert payload["leads"]["page"] == 2


def test_dashboard_seller_scope_excludes_another_seller():
    database = Database()
    database["leads"] = Collection([
        {"_id": "a", "assigneeId": "seller-a"},
        {"_id": "b", "assigneeId": "seller-b"},
    ])
    payload = DashboardService(database).for_user(
        CurrentUser("seller-a", "a@example.test", "seller")
    )
    assert [item["id"] for item in payload["leads"]["items"]] == ["a"]


def test_dashboard_service_rejects_invalid_direct_pagination():
    with pytest.raises(ValueError, match="limit"):
        DashboardService(Database()).for_user(
            CurrentUser("seller-a", "a@example.test", "seller"), limit=0
        )


def test_admin_route_returns_403_for_seller():
    app = FastAPI()
    app.include_router(admin_router)
    app.dependency_overrides[get_current_user] = lambda: CurrentUser(
        "seller-a", "a@example.test", "seller"
    )
    response = TestClient(app).get("/api/admin/users")
    assert response.status_code == 403


def test_admin_route_returns_2xx_with_real_nested_bson_documents() -> None:
    """Breaks if admin pagination only stringifies the top-level `_id`."""
    database = Database()
    user_id = ObjectId()
    database["users"] = Collection(
        [
            {
                "_id": user_id,
                "emailNormalized": "admin@example.test",
                "managerId": ObjectId(),
                "preferences": {"campaignIds": [ObjectId()]},
            }
        ]
    )
    app = FastAPI()
    app.state.database = database
    app.include_router(admin_router)
    app.dependency_overrides[get_current_user] = lambda: CurrentUser(
        str(user_id), "admin@example.test", "admin"
    )

    response = TestClient(app).get("/api/admin/users")

    assert response.status_code == 200
    body = response.json()["items"][0]
    assert body["id"] == str(user_id)
    assert isinstance(body["managerId"], str)
    assert isinstance(body["preferences"]["campaignIds"][0], str)


def test_seller_scopes_history_queue_and_balance_to_session_identity():
    seller = CurrentUser("seller-a", "a@example.test", "seller")
    assert PermissionService.scope_query(seller, "history") == {"sellerId": {"$in": ["seller-a"]}}
    assert PermissionService.scope_query(seller, "queue") == {"sellerId": {"$in": ["seller-a"]}}
    assert PermissionService.scope_query(seller, "skip_balance") == {"sellerId": {"$in": ["seller-a"]}}

