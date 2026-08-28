from datetime import UTC, datetime

from gerec_api.auth.permissions import DashboardService
from gerec_api.auth.sessions import CurrentUser


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
