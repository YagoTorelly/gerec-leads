"""Business-time calculations for the São Paulo operating calendar."""

from datetime import date, datetime, time, timedelta
from typing import Protocol
from zoneinfo import ZoneInfo


SAO_PAULO = ZoneInfo("America/Sao_Paulo")
BUSINESS_DAY_START = time(9)
BUSINESS_DAY_END = time(18)


class HolidayRepository(Protocol):
    def is_holiday(self, day: date) -> bool: ...


class MongoHolidayRepository:
    """Adapt configured national/SP holiday documents to the calendar interface."""

    def __init__(self, collection) -> None:
        self._collection = collection

    def is_holiday(self, day: date) -> bool:
        return (
            self._collection.find_one(
                {"date": day.isoformat(), "scope": {"$in": ["national", "sp"]}}
            )
            is not None
        )


class BusinessClock:
    def __init__(self, holidays: HolidayRepository) -> None:
        self._holidays = holidays

    def add_business_hours(self, start: datetime, hours: int) -> datetime:
        if start.tzinfo is None or start.utcoffset() is None:
            raise ValueError("start datetime must include a timezone")
        if hours < 0:
            raise ValueError("hours must be non-negative")

        current = self._normalize_forward(start.astimezone(SAO_PAULO))
        remaining = timedelta(hours=hours)

        while remaining:
            business_day_end = self._at_business_day_end(current.date())
            available = business_day_end - current
            if remaining <= available:
                return current + remaining
            remaining -= available
            current = self._next_business_day_start(current.date())

        return current

    def subtract_business_hours(self, deadline: datetime, hours: int) -> datetime:
        if deadline.tzinfo is None or deadline.utcoffset() is None:
            raise ValueError("deadline datetime must include a timezone")
        if hours < 0:
            raise ValueError("hours must be non-negative")

        current = self._normalize_backward(deadline.astimezone(SAO_PAULO))
        remaining = timedelta(hours=hours)

        while remaining:
            business_day_start = self._at_business_day_start(current.date())
            available = current - business_day_start
            if remaining <= available:
                return current - remaining
            remaining -= available
            current = self._previous_business_day_end(current.date())

        return current

    def is_business_day(self, day: date) -> bool:
        return day.weekday() < 5 and not self._holidays.is_holiday(day)

    def _normalize_forward(self, value: datetime) -> datetime:
        if not self.is_business_day(value.date()):
            return self._next_business_day_start(value.date())
        if value.time() < BUSINESS_DAY_START:
            return self._at_business_day_start(value.date())
        if value.time() >= BUSINESS_DAY_END:
            return self._next_business_day_start(value.date())
        return value

    def _normalize_backward(self, value: datetime) -> datetime:
        if not self.is_business_day(value.date()):
            return self._previous_business_day_end(value.date())
        if value.time() < BUSINESS_DAY_START:
            return self._previous_business_day_end(value.date())
        if value.time() > BUSINESS_DAY_END:
            return self._at_business_day_end(value.date())
        return value

    def _next_business_day_start(self, day: date) -> datetime:
        next_day = day + timedelta(days=1)
        while not self.is_business_day(next_day):
            next_day += timedelta(days=1)
        return self._at_business_day_start(next_day)

    def _previous_business_day_end(self, day: date) -> datetime:
        previous_day = day - timedelta(days=1)
        while not self.is_business_day(previous_day):
            previous_day -= timedelta(days=1)
        return self._at_business_day_end(previous_day)

    @staticmethod
    def _at_business_day_start(day: date) -> datetime:
        return datetime.combine(day, BUSINESS_DAY_START, tzinfo=SAO_PAULO)

    @staticmethod
    def _at_business_day_end(day: date) -> datetime:
        return datetime.combine(day, BUSINESS_DAY_END, tzinfo=SAO_PAULO)
