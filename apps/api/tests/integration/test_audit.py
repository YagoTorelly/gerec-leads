from datetime import UTC, datetime

from gerec_api.auth.permissions import DashboardService
from gerec_api.auth.sessions import CurrentUser


class Collection:
    def __init__(self, documents):
        self.documents = documents

    def find(self, query):
        return iter(self.documents)

    def count_documents(self, query):
        return len(self.documents)

    def find_one(self, query):
        return self.documents[0] if self.documents else None


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
