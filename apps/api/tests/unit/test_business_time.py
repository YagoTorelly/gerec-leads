"""Unit coverage for the business-day clock used by feedback SLAs."""

from datetime import date, datetime
from zoneinfo import ZoneInfo

import pytest

from gerec_api.domain.business_time import BusinessClock, MongoHolidayRepository


SAO_PAULO = ZoneInfo("America/Sao_Paulo")


class FixedHolidayRepository:
    def __init__(self, *holidays: date) -> None:
        self._holidays = frozenset(holidays)

    def is_holiday(self, day: date) -> bool:
        return day in self._holidays


class HolidayCollection:
    def __init__(self, documents) -> None:
        self.documents = documents

    def find_one(self, query):
        return next(
            (
                document
                for document in self.documents
                if document["date"] == query["date"]
                and document["scope"] in query["scope"]["$in"]
            ),
            None,
        )


def test_ac18_weekend_is_ignored_for_due_date_and_reminder() -> None:
    """Breaks if Saturday or Sunday consumes any part of the 24-hour SLA."""
    clock = BusinessClock(FixedHolidayRepository())
    assigned_at = datetime(2026, 8, 28, 14, 0, tzinfo=SAO_PAULO)  # Friday

    assert clock.add_business_hours(assigned_at, 24) == datetime(
        2026, 8, 31, 14, 0, tzinfo=SAO_PAULO
    )
    assert clock.add_business_hours(assigned_at, 20) == datetime(
        2026, 8, 31, 10, 0, tzinfo=SAO_PAULO
    )


@pytest.mark.parametrize("scope", ["national", "sp"])
def test_national_and_sp_holidays_are_ignored_as_complete_days(scope: str) -> None:
    """Breaks if either canonical holiday scope consumes business-time hours."""
    del scope  # Both scopes are normalized by the repository before reaching the clock.
    monday_holiday = date(2026, 8, 31)
    clock = BusinessClock(FixedHolidayRepository(monday_holiday))
    assigned_at = datetime(2026, 8, 28, 14, 0, tzinfo=SAO_PAULO)

    assert clock.add_business_hours(assigned_at, 24) == datetime(
        2026, 9, 1, 14, 0, tzinfo=SAO_PAULO
    )


def test_business_clock_rejects_naive_datetimes_and_negative_hours() -> None:
    """Breaks if callers can calculate an SLA without an explicit timezone or backwards."""
    clock = BusinessClock(FixedHolidayRepository())

    with pytest.raises(ValueError, match="timezone"):
        clock.add_business_hours(datetime(2026, 8, 28, 14, 0), 24)
    with pytest.raises(ValueError, match="non-negative"):
        clock.add_business_hours(datetime(2026, 8, 28, 14, 0, tzinfo=SAO_PAULO), -1)


def test_mongo_holiday_repository_counts_only_national_and_sp_scopes() -> None:
    """Breaks if a configured canonical holiday is missed or a municipal date is counted."""
    repository = MongoHolidayRepository(
        HolidayCollection(
            [
                {"date": "2026-09-07", "scope": "national"},
                {"date": "2026-01-25", "scope": "municipal"},
            ]
        )
    )

    assert repository.is_holiday(date(2026, 9, 7)) is True
    assert repository.is_holiday(date(2026, 1, 25)) is False
