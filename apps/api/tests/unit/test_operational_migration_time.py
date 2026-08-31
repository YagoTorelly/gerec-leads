"""Regression tests for timestamps read by the operational migration."""

from datetime import UTC, datetime
from zoneinfo import ZoneInfo

from importlib import import_module


migration = import_module(
    "gerec_api.infrastructure.mongo.migrations.20260828_operacao_comercial"
)


SAO_PAULO = ZoneInfo("America/Sao_Paulo")


def test_legacy_naive_timestamp_is_interpreted_in_sao_paulo_before_business_clock() -> None:
    legacy = datetime(2026, 8, 28, 17, 0)

    normalized = migration._legacy_datetime(legacy)

    assert normalized == datetime(2026, 8, 28, 17, 0, tzinfo=SAO_PAULO)
    assert normalized.tzinfo is not None


def test_legacy_aware_timestamp_is_converted_to_sao_paulo() -> None:
    legacy = datetime(2026, 8, 28, 20, 0, tzinfo=UTC)

    normalized = migration._legacy_datetime(legacy)

    assert normalized == datetime(2026, 8, 28, 17, 0, tzinfo=SAO_PAULO)


def test_legacy_feedback_sort_accepts_mixed_naive_and_aware_timestamps() -> None:
    class Collection:
        def find(self, _query, **_options):
            return [
                {
                    "_id": "aware",
                    "kind": "seller_feedback",
                    "contactStarted": True,
                    "comment": "retorno confirmado",
                    "createdAt": datetime(2026, 8, 28, 20, 0, tzinfo=UTC),
                },
                {
                    "_id": "naive",
                    "kind": "seller_feedback",
                    "contactStarted": True,
                    "comment": "primeiro contato",
                    "createdAt": datetime(2026, 8, 28, 17, 0),
                },
            ]

    class Database:
        def __getitem__(self, _name):
            return Collection()

    feedbacks = migration._valid_feedbacks(Database(), "lead-1", {})

    assert {feedback["_id"] for feedback in feedbacks} == {"naive", "aware"}
