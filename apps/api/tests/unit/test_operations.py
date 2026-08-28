"""Unit coverage for validation and time decisions at the operations seam."""

from datetime import date, datetime
from zoneinfo import ZoneInfo

import pytest

from gerec_api.domain.business_time import BusinessClock
from gerec_api.domain.operations import (
    AttemptCommand,
    AttemptResult,
    FeedbackCommand,
    FeedbackResult,
    OperationsService,
    OutcomeCommand,
    OutcomeResult,
)
from gerec_api.infrastructure.mongo.indexes import INDEXES


SAO_PAULO = ZoneInfo("America/Sao_Paulo")
NOW = datetime(2026, 8, 31, 14, 0, tzinfo=SAO_PAULO)


class NoHolidays:
    def is_holiday(self, day: date) -> bool:
        return False


class FixedClock:
    def now(self) -> datetime:
        return NOW


class RecordingPersistence:
    def __init__(self) -> None:
        self.feedbacks = []
        self.attempts = []
        self.outcomes = []

    def register_feedback(self, command, *, actor_id, actor_role, now, reminder_at, due_at):
        self.feedbacks.append((command, actor_id, actor_role, now, reminder_at, due_at))
        return FeedbackResult(
            lead_id=str(command.lead_id),
            feedback_id="feedback-1",
            cycle_id="cycle-1",
            status="recorded",
            reminder_at=reminder_at,
            due_at=due_at,
        )

    def register_attempt(self, command, *, actor_id, actor_role, now, business_date):
        self.attempts.append((command, actor_id, actor_role, now, business_date))
        return AttemptResult(
            lead_id=str(command.lead_id),
            attempt_id="attempt-1",
            sequence=1,
            business_date=business_date,
            may_disqualify_no_answer=False,
            status="recorded",
        )

    def register_outcome(self, command, *, actor_id, actor_role, now):
        self.outcomes.append((command, actor_id, actor_role, now))
        return OutcomeResult(
            lead_id=str(command.lead_id),
            outcome_event_id="event-1",
            outcome=command.outcome,
            sale_id=None,
            status="recorded",
        )


def _service(persistence: RecordingPersistence | None = None) -> OperationsService:
    return OperationsService(
        persistence or RecordingPersistence(),
        business_clock=BusinessClock(NoHolidays()),
        clock=FixedClock(),
    ).with_actor("seller-1", "seller")


def test_ac19_short_feedback_comment_does_not_reach_persistence_or_renew_sla() -> None:
    """Breaks if whitespace or fewer than six useful characters can renew a cycle."""
    persistence = RecordingPersistence()
    service = _service(persistence)

    with pytest.raises(ValueError, match="6"):
        service.register_feedback(
            FeedbackCommand("lead-1", "  abcde  ", True, "feedback-short")
        )

    assert persistence.feedbacks == []


def test_ac20_valid_feedback_opens_24_business_hour_cycle_with_four_hour_reminder() -> None:
    """Breaks if feedback deadlines are client-provided or use elapsed calendar hours."""
    result = _service().register_feedback(
        FeedbackCommand("lead-1", " Retorno confirmado ", True, "feedback-valid")
    )

    assert result.status == "recorded"
    assert result.reminder_at == datetime(2026, 9, 1, 10, 0, tzinfo=SAO_PAULO)
    assert result.due_at == datetime(2026, 9, 1, 14, 0, tzinfo=SAO_PAULO)


def test_feedback_requires_an_explicit_contact_action() -> None:
    """Breaks if a generic note can masquerade as seller feedback."""
    with pytest.raises(ValueError, match="contact"):
        _service().register_feedback(
            FeedbackCommand("lead-1", "Apenas anotação", False, "feedback-note")
        )


def test_attempt_rejects_weekend_holiday_and_future_business_dates() -> None:
    """Breaks if any invalid date can count toward the five distinct attempts."""
    saturday = date(2026, 8, 29)
    future = date(2026, 9, 1)
    service = _service()

    with pytest.raises(ValueError, match="business day"):
        service.register_attempt(
            AttemptCommand("lead-1", "Sem resposta", "attempt-weekend", saturday)
        )
    with pytest.raises(ValueError, match="future"):
        service.register_attempt(
            AttemptCommand("lead-1", "Sem resposta", "attempt-future", future)
        )


def test_ac22_no_conversion_remains_a_qualified_outcome() -> None:
    """Breaks if refusal is collapsed into a disqualification category."""
    result = _service().register_outcome(
        OutcomeCommand(
            "lead-1",
            "qualified_closed_no_conversion",
            "Cliente recusou a proposta",
            "outcome-no-sale",
            None,
            True,
        )
    )

    assert result.outcome == "qualified_closed_no_conversion"


def test_admin_cannot_change_commercial_status() -> None:
    """Only the assigned seller may manually change the commercial status."""
    with pytest.raises(ValueError, match="seller"):
        _service().with_actor("admin-1", "admin").register_outcome(
            OutcomeCommand("lead-1", "won", "Seguro pago pelo cliente", "admin-outcome")
        )


def test_qualified_outcome_requires_explicit_real_response_confirmation() -> None:
    """Breaks if qualification can be recorded without confirming a real contact response."""
    with pytest.raises(ValueError, match="response"):
        _service().register_outcome(
            OutcomeCommand(
                "lead-1",
                "qualified_follow_up",
                "Cliente respondeu e pediu retorno",
                "outcome-unconfirmed",
            )
        )


def test_attempt_date_has_a_unique_database_guard() -> None:
    """Breaks if concurrent commands can count two attempts for one lead/business date."""
    definitions = {definition.name: definition for definition in INDEXES}

    guard = definitions["contact_attempts_lead_business_date_unique"]
    assert guard.keys == (("leadId", 1), ("businessDate", 1))
    assert guard.unique is True
