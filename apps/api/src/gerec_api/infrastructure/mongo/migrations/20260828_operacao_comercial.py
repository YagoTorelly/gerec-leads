"""Materialize GOV-004 commercial-operation projections from immutable legacy history."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from gerec_api.domain.business_time import BusinessClock, MongoHolidayRepository
from gerec_api.infrastructure.mongo.collections import MongoCollections


VERSION = "20260828_operacao_comercial"
_COMMERCIAL_STATUSES = frozenset({"undefined", "negotiation", "won"})


def apply(database: Any, *, session: Any | None = None) -> None:
    """Rebuild mutable lead projections without altering legacy events or sessions."""
    options = _session_options(session)
    business_clock = BusinessClock(
        MongoHolidayRepository(database[MongoCollections.HOLIDAYS])
    )
    for lead in database[MongoCollections.LEADS].find({}, **options):
        _migrate_lead(database, lead, business_clock, session)


def _migrate_lead(
    database: Any,
    lead: dict[str, Any],
    business_clock: BusinessClock,
    session: Any | None,
) -> None:
    options = _session_options(session)
    lead_id = lead["_id"]
    feedbacks = _valid_feedbacks(database, lead_id, options)
    outcomes = list(
        database[MongoCollections.QUALIFICATION_EVENTS].find({"leadId": lead_id}, **options)
    )
    commercial_status = _commercial_status(lead, outcomes)
    is_disqualified = _is_disqualified(lead, outcomes)
    last_comment_at = feedbacks[-1].get("createdAt") if feedbacks else None

    _copy_legacy_feedbacks_as_treatments(
        database,
        lead_id,
        feedbacks,
        commercial_status,
        is_disqualified,
        session,
    )
    update: dict[str, Any] = {
        "commercialStatus": commercial_status,
        "isDisqualified": is_disqualified,
        "commentCount": len(feedbacks),
        "lastCommentAt": last_comment_at,
    }
    if is_disqualified:
        closed_at = _disqualification_closed_at(outcomes, feedbacks, lead)
        database[MongoCollections.FEEDBACK_CYCLES].update_many(
            {"leadId": lead_id, "closedAt": None},
            {"$set": {"closedAt": closed_at, "closedByMigration": VERSION}},
            **options,
        )
        update.update({"feedbackDueAt": None, "feedbackReminderAt": None})
    else:
        due_at, reminder_at = _recalculate_open_cycles(
            database, lead, business_clock, session
        )
        update.update({"feedbackDueAt": due_at, "feedbackReminderAt": reminder_at})
    database[MongoCollections.LEADS].update_one({"_id": lead_id}, {"$set": update}, **options)


def _valid_feedbacks(database: Any, lead_id: Any, options: dict[str, Any]) -> list[dict[str, Any]]:
    feedbacks = database[MongoCollections.FEEDBACKS].find({"leadId": lead_id}, **options)
    valid = [
        feedback
        for feedback in feedbacks
        if feedback.get("kind") == "seller_feedback"
        and feedback.get("contactStarted") is True
        and len(str(feedback.get("comment", "")).strip()) >= 6
    ]
    return sorted(valid, key=lambda feedback: (feedback.get("createdAt") or _EPOCH, str(feedback["_id"])))


def _copy_legacy_feedbacks_as_treatments(
    database: Any,
    lead_id: Any,
    feedbacks: list[dict[str, Any]],
    commercial_status: str,
    is_disqualified: bool,
    session: Any | None,
) -> None:
    options = _session_options(session)
    treatments = database[MongoCollections.LEAD_TREATMENTS]
    for feedback in feedbacks:
        legacy_id = feedback["_id"]
        treatments.update_one(
            {"leadId": lead_id, "idempotencyKey": f"legacy-feedback:{legacy_id}"},
            {
                "$setOnInsert": {
                    "leadId": lead_id,
                    "sellerId": feedback.get("sellerId"),
                    "comment": str(feedback["comment"]).strip(),
                    "commercialStatus": commercial_status,
                    "isDisqualified": is_disqualified,
                    "createdAt": feedback.get("createdAt") or _EPOCH,
                    "idempotencyKey": f"legacy-feedback:{legacy_id}",
                    "legacyFeedbackId": legacy_id,
                }
            },
            upsert=True,
            **options,
        )


def _recalculate_open_cycles(
    database: Any,
    lead: dict[str, Any],
    business_clock: BusinessClock,
    session: Any | None,
) -> tuple[datetime | None, datetime | None]:
    options = _session_options(session)
    cycles = list(
        database[MongoCollections.FEEDBACK_CYCLES].find(
            {"leadId": lead["_id"], "closedAt": None}, **options
        )
    )
    recalculated: list[dict[str, Any]] = []
    for cycle in cycles:
        start_at = cycle.get("startAt") or lead.get("assignedAt")
        if not isinstance(start_at, datetime):
            continue
        due_at = business_clock.add_business_hours(start_at, 24)
        reminder_at = business_clock.subtract_business_hours(due_at, 4)
        database[MongoCollections.FEEDBACK_CYCLES].update_one(
            {"_id": cycle["_id"], "closedAt": None},
            {"$set": {"startAt": start_at, "dueAt": due_at, "reminderAt": reminder_at}},
            **options,
        )
        recalculated.append({"startAt": start_at, "dueAt": due_at, "reminderAt": reminder_at})
    if not recalculated:
        return None, None
    latest = max(recalculated, key=lambda cycle: (cycle["startAt"], cycle["dueAt"]))
    return latest["dueAt"], latest["reminderAt"]


def _commercial_status(lead: dict[str, Any], outcomes: list[dict[str, Any]]) -> str:
    if lead.get("conversionStatus") == "won" or any(
        outcome.get("outcome") == "won" for outcome in outcomes
    ):
        return "won"
    existing = lead.get("commercialStatus")
    if existing in _COMMERCIAL_STATUSES:
        return str(existing)
    if lead.get("qualificationStatus") in {"qualified", "in_negotiation", "negotiation"} or any(
        outcome.get("outcome") in {"qualified_follow_up", "negotiation"} for outcome in outcomes
    ):
        return "negotiation"
    return "undefined"


def _is_disqualified(lead: dict[str, Any], outcomes: list[dict[str, Any]]) -> bool:
    return bool(
        lead.get("isDisqualified")
        or lead.get("qualificationStatus") == "disqualified"
        or lead.get("conversionStatus") == "disqualified"
        or any(outcome.get("outcome") == "disqualified" for outcome in outcomes)
    )


def _disqualification_closed_at(
    outcomes: list[dict[str, Any]], feedbacks: list[dict[str, Any]], lead: dict[str, Any]
) -> datetime:
    timestamps = [
        event.get("createdAt")
        for event in outcomes
        if event.get("outcome") == "disqualified" and isinstance(event.get("createdAt"), datetime)
    ]
    timestamps.extend(
        feedback.get("createdAt")
        for feedback in feedbacks
        if isinstance(feedback.get("createdAt"), datetime)
    )
    if isinstance(lead.get("assignedAt"), datetime):
        timestamps.append(lead["assignedAt"])
    return max(timestamps, default=_EPOCH)


def _session_options(session: Any | None) -> dict[str, Any]:
    return {} if session is None else {"session": session}


_EPOCH = datetime(1970, 1, 1, tzinfo=UTC)
