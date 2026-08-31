"""Unit coverage for the immutable commercial treatment command."""

from datetime import datetime
from typing import Any

import pytest

from gerec_api.domain.operations import OperationsService, TreatmentCommand, TreatmentResult


NOW = datetime.fromisoformat("2026-09-04T14:00:00+00:00")


class FixedClock:
    def now(self) -> datetime:
        return NOW


class RecordingBusinessClock:
    def add_business_hours(self, start: datetime, hours: int) -> datetime:
        assert start == NOW
        assert hours == 24
        return datetime.fromisoformat("2026-09-09T14:00:00+00:00")

    def subtract_business_hours(self, deadline: datetime, hours: int) -> datetime:
        assert deadline == datetime.fromisoformat("2026-09-09T14:00:00+00:00")
        assert hours == 4
        return datetime.fromisoformat("2026-09-08T19:00:00+00:00")


class RecordingPersistence:
    def __init__(self) -> None:
        self.treatments: list[tuple[Any, ...]] = []

    def register_treatment(
        self,
        command: TreatmentCommand,
        *,
        actor_id: Any,
        actor_role: str,
        now: datetime,
        reminder_at: datetime,
        due_at: datetime,
    ) -> TreatmentResult:
        self.treatments.append((command, actor_id, actor_role, now, reminder_at, due_at))
        return TreatmentResult(
            lead_id=str(command.lead_id),
            treatment_id="treatment-1",
            status="recorded",
            commercial_status=command.commercial_status,
            is_disqualified=command.is_disqualified,
            comment_count=1,
            last_updated_at=now,
            reminder_at=reminder_at,
            due_at=due_at,
        )


def _service(persistence: RecordingPersistence | None = None) -> OperationsService:
    return OperationsService(
        persistence or RecordingPersistence(),
        business_clock=RecordingBusinessClock(),
        clock=FixedClock(),
    ).with_actor("seller-1", "seller")


def test_treatment_rejects_five_useful_characters_before_reaching_persistence() -> None:
    """Breaks if a five-character comment can change commercial state."""
    persistence = RecordingPersistence()

    with pytest.raises(ValueError, match="6"):
        _service(persistence).register_treatment(
            TreatmentCommand("lead-1", " abcde ", "undefined", False, "short-comment")
        )

    assert persistence.treatments == []


def test_treatment_requires_a_closed_commercial_status() -> None:
    """Breaks if an omitted primary situation becomes an implicit state."""
    persistence = RecordingPersistence()

    with pytest.raises(ValueError, match="commercial status"):
        _service(persistence).register_treatment(
            TreatmentCommand("lead-1", "Contato confirmado", None, False, "missing-status")  # type: ignore[arg-type]
        )

    assert persistence.treatments == []


def test_treatment_rejects_disqualification_without_a_useful_comment() -> None:
    """Breaks if the additional disqualification marker can be set without context."""
    persistence = RecordingPersistence()

    with pytest.raises(ValueError, match="6"):
        _service(persistence).register_treatment(
            TreatmentCommand("lead-1", "   ", "negotiation", True, "blank-disqualification")
        )

    assert persistence.treatments == []


def test_admin_cannot_register_a_treatment() -> None:
    """Breaks if a global-read administrator can alter a seller treatment."""
    persistence = RecordingPersistence()
    service = _service(persistence).with_actor("admin-1", "admin")

    with pytest.raises(ValueError, match="seller"):
        service.register_treatment(
            TreatmentCommand("lead-1", "Contato confirmado", "negotiation", False, "admin-denied")
        )

    assert persistence.treatments == []


def test_treatment_preserves_won_plus_disqualified_as_independent_values() -> None:
    """Breaks if marking disqualified overwrites the primary won situation."""
    persistence = RecordingPersistence()

    result = _service(persistence).register_treatment(
        TreatmentCommand("lead-1", "Venda confirmada pelo cliente", "won", True, "won-disqualified")
    )

    command, actor_id, actor_role, _, _, _ = persistence.treatments[0]
    assert command.comment == "Venda confirmada pelo cliente"
    assert actor_id == "seller-1"
    assert actor_role == "seller"
    assert result.commercial_status == "won"
    assert result.is_disqualified is True
