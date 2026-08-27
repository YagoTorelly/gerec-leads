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
    SELLER_SKIP_BALANCES: Final = "seller_skip_balances"
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
    BUSINESS_HOLIDAYS: Final = "business_holidays"
    SOURCE_SNAPSHOTS: Final = "source_snapshots"
    FIELD_OVERRIDES: Final = "field_overrides"
    SOURCE_CONFLICTS: Final = "source_conflicts"
    NOTIFICATION_OUTBOX: Final = "notification_outbox"
    NOTIFICATION_INCIDENTS: Final = "notification_incidents"
    AUDIT_LOG: Final = "audit_log"
    SYSTEM_SETTINGS: Final = "system_settings"

    ALL: Final = (
        USERS,
        SESSIONS,
        SELLER_QUEUE,
        QUEUE_STATE,
        SELLER_SKIP_BALANCES,
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
        BUSINESS_HOLIDAYS,
        SOURCE_SNAPSHOTS,
        FIELD_OVERRIDES,
        SOURCE_CONFLICTS,
        NOTIFICATION_OUTBOX,
        NOTIFICATION_INCIDENTS,
        AUDIT_LOG,
        SYSTEM_SETTINGS,
    )


def collection(db: Database, name: str) -> Collection:
    """Retorna uma cole\u00e7\u00e3o pelo nome can\u00f4nico centralizado."""
    return db[name]
