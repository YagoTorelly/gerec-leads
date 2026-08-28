"""Business-time calculations for the São Paulo operating calendar."""

from datetime import date, datetime, time, timedelta
from typing import Protocol
from zoneinfo import ZoneInfo


SAO_PAULO = ZoneInfo("America/Sao_Paulo")


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

        current = start.astimezone(SAO_PAULO)
        if hours == 0:
            return current
        remaining = timedelta(hours=hours)

        while remaining:
            if not self.is_business_day(current.date()):
                current = self._next_midnight(current)
                continue

            next_midnight = self._next_midnight(current)
            available = next_midnight - current
            if remaining < available:
                return current + remaining
            remaining -= available
            current = next_midnight

        while not self.is_business_day(current.date()):
            current = self._next_midnight(current)
        return current

    def is_business_day(self, day: date) -> bool:
        return day.weekday() < 5 and not self._holidays.is_holiday(day)

    @staticmethod
    def _next_midnight(value: datetime) -> datetime:
        return datetime.combine(value.date() + timedelta(days=1), time.min, tzinfo=SAO_PAULO)
