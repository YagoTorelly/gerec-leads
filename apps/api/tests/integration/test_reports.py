"""Administrative lead-distribution report contracts."""

from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from gerec_api.auth.dependencies import get_current_user
from gerec_api.auth.permissions import DashboardService
from gerec_api.auth.sessions import CurrentUser
from gerec_api.routes.reports import router as reports_router


TRANSFER_AT = datetime(2026, 9, 14, 15, tzinfo=UTC)


class Cursor:
    def __init__(self, values: list[dict[str, Any]]) -> None:
        self.values = values

    def __iter__(self):
        return iter(deepcopy(self.values))


class Collection:
    def __init__(self, documents: list[dict[str, Any]] | None = None) -> None:
        self.documents = documents or []

    def find(self, query: dict[str, Any], **_: Any) -> Cursor:
        return Cursor([document for document in self.documents if _matches(document, query)])


class Database(dict[str, Collection]):
    def __getitem__(self, name: str) -> Collection:
        return super().setdefault(name, Collection())


def _matches(document: dict[str, Any], query: dict[str, Any]) -> bool:
    for field, expected in query.items():
        value = document.get(field)
        if not isinstance(expected, dict):
            if value != expected:
                return False
            continue
        if "$in" in expected and value not in expected["$in"]:
            return False
        if "$gte" in expected and (value is None or value < expected["$gte"]):
            return False
        if "$lt" in expected and (value is None or value >= expected["$lt"]):
            return False
    return True


def _database() -> Database:
    return Database(
        users=Collection(
            [
                {"_id": "seller-old", "fullName": "Renato"},
                {"_id": "seller-new", "fullName": "Jessica"},
            ]
        ),
        leads=Collection(
            [
                {
                    "_id": "transferred-lead",
                    "assigneeId": "seller-new",
                    "assignedAt": TRANSFER_AT,
                    "commercialStatus": "potential",
                },
                {
                    "_id": "previous-period-lead",
                    "assigneeId": "seller-old",
                    "assignedAt": TRANSFER_AT - timedelta(seconds=1),
                    "commercialStatus": "negotiation",
                },
            ]
        ),
    )


def _admin() -> CurrentUser:
    return CurrentUser("admin-1", "yago@example.test", "admin")


def _seller() -> CurrentUser:
    return CurrentUser("seller-old", "renato@example.test", "seller")


def test_report_uses_current_owner_and_transfer_assignment_date() -> None:
    """Breaks if the report uses assignment history or a pre-transfer assignment date."""
    report = DashboardService(_database()).lead_distribution(
        _admin(), from_at=TRANSFER_AT, to_at=TRANSFER_AT + timedelta(days=1)
    )

    assert report["period"] == {
        "from": "2026-09-14T15:00:00+00:00",
        "to": "2026-09-15T15:00:00+00:00",
    }
    assert report["bySituation"] == [{"commercialStatus": "potential", "count": 1}]
    assert report["bySeller"] == [
        {"sellerId": "seller-new", "sellerName": "Jessica", "count": 1}
    ]


def test_report_route_denies_seller() -> None:
    """Breaks if a seller can access a global aggregation through the API route."""
    app = FastAPI()
    app.state.dashboard_service = DashboardService(_database())
    app.include_router(reports_router)
    app.dependency_overrides[get_current_user] = _seller

    response = TestClient(app).get("/api/admin/reports/lead-distribution")

    assert response.status_code == 403


def test_report_rejects_an_empty_or_reversed_assignment_interval() -> None:
    """Breaks if an invalid range can be interpreted as a report period."""
    service = DashboardService(_database())

    with pytest.raises(ValueError, match="fromAt must be earlier than toAt"):
        service.lead_distribution(_admin(), from_at=TRANSFER_AT, to_at=TRANSFER_AT)
