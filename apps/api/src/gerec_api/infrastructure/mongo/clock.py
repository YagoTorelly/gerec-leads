"""Database-backed clock used for timestamps in transactional commands."""

from datetime import UTC, datetime
from typing import Any


class MongoClock:
    """Read MongoDB's server clock, preserving the transaction session when present."""

    def __init__(self, database: Any) -> None:
        self._database = database

    def now(self, session: Any | None = None) -> datetime:
        options = {} if session is None else {"session": session}
        local_time = self._database.command({"hello": 1}, **options)["localTime"]
        if local_time.tzinfo is None:
            return local_time.replace(tzinfo=UTC)
        return local_time.astimezone(UTC)
