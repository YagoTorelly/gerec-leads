"""Database-backed clock used for timestamps in transactional commands."""

from datetime import UTC, datetime
from typing import Any


class MongoClock:
    """Read MongoDB's server clock before starting a transaction."""

    def __init__(self, database: Any) -> None:
        self._database = database

    def now(self, session: Any | None = None) -> datetime:
        if session is not None:
            raise RuntimeError("MongoClock must be read before starting a transaction")
        local_time = self._database.command({"hello": 1})["localTime"]
        if local_time.tzinfo is None:
            return local_time.replace(tzinfo=UTC)
        return local_time.astimezone(UTC)
