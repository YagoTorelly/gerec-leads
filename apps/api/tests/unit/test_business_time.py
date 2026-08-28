"""Unit coverage for the business-day clock used by feedback SLAs."""

from datetime import UTC, date, datetime
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
    """Breaks if the SLA counts overnight instead of only commercial hours."""
    clock = BusinessClock(FixedHolidayRepository())
    assigned_at = datetime(2026, 8, 28, 14, 0, tzinfo=SAO_PAULO)  # Friday

    assert clock.add_business_hours(assigned_at, 24) == datetime(
        2026, 9, 2, 11, 0, tzinfo=SAO_PAULO
    )
    assert clock.add_business_hours(assigned_at, 20) == datetime(
        2026, 9, 1, 16, 0, tzinfo=SAO_PAULO
    )


@pytest.mark.parametrize("scope", ["national", "sp"])
def test_national_and_sp_holidays_are_ignored_as_complete_days(scope: str) -> None:
    """Breaks if either canonical holiday scope consumes business-time hours."""
    del scope  # Both scopes are normalized by the repository before reaching the clock.
    monday_holiday = date(2026, 8, 31)
    clock = BusinessClock(FixedHolidayRepository(monday_holiday))
    assigned_at = datetime(2026, 8, 28, 14, 0, tzinfo=SAO_PAULO)

    assert clock.add_business_hours(assigned_at, 24) == datetime(
        2026, 9, 3, 11, 0, tzinfo=SAO_PAULO
    )


def test_add_business_hours_consumes_only_the_commercial_window() -> None:
    """Breaks if a Friday 17:00 SLA counts nighttime or non-business days."""
    clock = BusinessClock(FixedHolidayRepository())

    assert clock.add_business_hours(
        datetime(2026, 8, 28, 17, 0, tzinfo=SAO_PAULO), 24
    ) == datetime(2026, 9, 2, 14, 0, tzinfo=SAO_PAULO)


def test_add_business_hours_normalizes_before_and_after_the_commercial_window() -> None:
    """Breaks if 08:30 or 18:00 can start an SLA outside the approved window."""
    clock = BusinessClock(FixedHolidayRepository())

    assert clock.add_business_hours(
        datetime(2026, 8, 31, 8, 30, tzinfo=SAO_PAULO), 0
    ) == datetime(2026, 8, 31, 9, 0, tzinfo=SAO_PAULO)
    assert clock.add_business_hours(
        datetime(2026, 8, 28, 18, 0, tzinfo=SAO_PAULO), 0
    ) == datetime(2026, 8, 31, 9, 0, tzinfo=SAO_PAULO)


def test_add_business_hours_preserves_minutes_when_crossing_the_weekend() -> None:
    """Breaks if a partial commercial hour is rounded while skipping the weekend."""
    clock = BusinessClock(FixedHolidayRepository())

    assert clock.add_business_hours(
        datetime(2026, 8, 28, 17, 59, tzinfo=SAO_PAULO), 1
    ) == datetime(2026, 8, 31, 9, 59, tzinfo=SAO_PAULO)


def test_sp_holiday_is_skipped_inside_the_commercial_window() -> None:
    """Breaks if a configured São Paulo holiday consumes commercial hours."""
    clock = BusinessClock(FixedHolidayRepository(date(2026, 8, 31)))

    assert clock.add_business_hours(
        datetime(2026, 8, 28, 17, 0, tzinfo=SAO_PAULO), 24
    ) == datetime(2026, 9, 3, 14, 0, tzinfo=SAO_PAULO)


def test_subtract_business_hours_calculates_the_four_hour_reminder() -> None:
    """Breaks if the reminder subtracts calendar time instead of business time."""
    clock = BusinessClock(FixedHolidayRepository())
    due_at = datetime(2026, 9, 2, 14, 0, tzinfo=SAO_PAULO)

    assert clock.subtract_business_hours(due_at, 4) == datetime(
        2026, 9, 2, 10, 0, tzinfo=SAO_PAULO
    )


def test_subtract_business_hours_crosses_the_end_of_a_business_day() -> None:
    """Breaks if subtracting from 09:30 does not resume at 17:30 on the prior day."""
    clock = BusinessClock(FixedHolidayRepository())

    assert clock.subtract_business_hours(
        datetime(2026, 9, 1, 9, 30, tzinfo=SAO_PAULO), 1
    ) == datetime(2026, 8, 31, 17, 30, tzinfo=SAO_PAULO)


def test_subtract_business_hours_crosses_a_weekend() -> None:
    """Breaks if weekend hours are consumed while subtracting a reminder."""
    clock = BusinessClock(FixedHolidayRepository())

    assert clock.subtract_business_hours(
        datetime(2026, 8, 31, 9, 30, tzinfo=SAO_PAULO), 1
    ) == datetime(2026, 8, 28, 17, 30, tzinfo=SAO_PAULO)


def test_subtract_business_hours_crosses_an_sp_holiday() -> None:
    """Breaks if an SP holiday is counted while subtracting a reminder."""
    clock = BusinessClock(FixedHolidayRepository(date(2026, 8, 31)))

    assert clock.subtract_business_hours(
        datetime(2026, 9, 1, 9, 30, tzinfo=SAO_PAULO), 1
    ) == datetime(2026, 8, 28, 17, 30, tzinfo=SAO_PAULO)


def test_subtract_business_hours_converts_an_external_timezone_to_sao_paulo() -> None:
    """Breaks if an aware deadline outside São Paulo is not normalized before subtraction."""
    clock = BusinessClock(FixedHolidayRepository())

    assert clock.subtract_business_hours(
        datetime(2026, 9, 2, 14, 0, tzinfo=UTC), 4
    ) == datetime(2026, 9, 1, 16, 0, tzinfo=SAO_PAULO)


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
