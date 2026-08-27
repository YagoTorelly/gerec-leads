"""Nomes can\u00f4nicos das cole\u00e7\u00f5es MongoDB do Gerenciador de Leads."""

from typing import Final

from pymongo.collection import Collection
from pymongo.database import Database


class MongoCollections:
    """Evita que nomes de cole\u00e7\u00f5es sejam repetidos nas queries da aplica\u00e7\u00e3o."""

    USERS: Final = "users"
    SESSIONS: Final = "sessions"
    SELLER_QUEUE: Final = "seller_queue"
    QUEUE_STATE: Final = "queue_state"
    SKIP_BALANCES: Final = "skip_balances"
    CAMPAIGNS: Final = "campaigns"
    COMPANIES: Final = "companies"
    LEADS: Final = "leads"
    SOURCE_RECORDS: Final = "source_records"
    ASSIGNMENTS: Final = "assignments"
    FEEDBACK_CYCLES: Final = "feedback_cycles"
    FEEDBACKS: Final = "feedbacks"
    CONTACT_ATTEMPTS: Final = "contact_attempts"
    QUALIFICATION_EVENTS: Final = "qualification_events"
    SALES: Final = "sales"
    HOLIDAYS: Final = "holidays"
    SOURCE_SNAPSHOTS: Final = "source_snapshots"
    FIELD_OVERRIDES: Final = "field_overrides"
    SOURCE_CONFLICTS: Final = "source_conflicts"
    NOTIFICATION_OUTBOX: Final = "notification_outbox"
    NOTIFICATION_INCIDENTS: Final = "notification_incidents"
    AUDIT_LOG: Final = "audit_log"
    SYSTEM_SETTINGS: Final = "system_settings"
    COMMAND_RESULTS: Final = "command_results"

    ALL: Final = (
        USERS,
        SESSIONS,
        SELLER_QUEUE,
        QUEUE_STATE,
        SKIP_BALANCES,
        CAMPAIGNS,
        COMPANIES,
        LEADS,
        SOURCE_RECORDS,
        ASSIGNMENTS,
        FEEDBACK_CYCLES,
        FEEDBACKS,
        CONTACT_ATTEMPTS,
        QUALIFICATION_EVENTS,
        SALES,
        HOLIDAYS,
        SOURCE_SNAPSHOTS,
        FIELD_OVERRIDES,
        SOURCE_CONFLICTS,
        NOTIFICATION_OUTBOX,
        NOTIFICATION_INCIDENTS,
        AUDIT_LOG,
        SYSTEM_SETTINGS,
        COMMAND_RESULTS,
    )


def collection(db: Database, name: str) -> Collection:
    """Retorna uma cole\u00e7\u00e3o pelo nome can\u00f4nico centralizado."""
    return db[name]
