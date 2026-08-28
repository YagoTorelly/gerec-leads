"""Unit coverage for the global seller rotation and skip-credit rules."""

from bson import ObjectId

from gerec_api.domain.queue import QueueRules, SellerState
from gerec_api.infrastructure.mongo.bootstrap import SCHEMA_VALIDATORS
from gerec_api.infrastructure.mongo.collections import MongoCollections
from gerec_api.infrastructure.mongo.indexes import INDEXES


def _seller(*, active: bool = True, paused: bool = False, overdue: bool = False, credits: int = 0):
    return SellerState(
        seller_id=ObjectId(),
        active=active,
        paused=paused,
        has_overdue_feedback=overdue,
        skip_balance=credits,
    )


def test_ac01_rotation_assigns_each_seller_once_and_returns_to_renato() -> None:
    """Breaks if selection or cursor advancement stops following the canonical order."""
    sellers = [_seller() for _ in range(4)]
    cursor = sellers[0].seller_id
    assigned = []

    for _ in range(4):
        decision = QueueRules.select_normal(sellers, cursor)
        assigned.append(decision.seller_id)
        cursor = decision.next_seller_id

    assert assigned == [seller.seller_id for seller in sellers]
    assert cursor == sellers[0].seller_id


def test_ac02_ac03_overdue_seller_loses_the_turn_without_restoration() -> None:
    """Breaks if an overdue seller keeps a turn or is served immediately after regularizing."""
    renato, sandra, jessica, nelma = [_seller() for _ in range(4)]
    renato = SellerState(renato.seller_id, True, False, True, 0)

    first = QueueRules.select_normal([renato, sandra, jessica, nelma], renato.seller_id)
    regularized = SellerState(renato.seller_id, True, False, False, 0)
    second = QueueRules.select_normal(
        [regularized, sandra, jessica, nelma],
        first.next_seller_id,
    )

    assert first.seller_id == sandra.seller_id
    assert first.next_seller_id == jessica.seller_id
    assert second.seller_id == jessica.seller_id


def test_ac04_ac05_one_overdue_lead_blocks_and_all_unavailable_parks() -> None:
    """Breaks if any blocked/paused/inactive seller can receive a normal lead."""
    sellers = [
        _seller(overdue=True),
        _seller(paused=True),
        _seller(active=False),
        _seller(overdue=True),
    ]

    decision = QueueRules.select_normal(sellers, sellers[0].seller_id)

    assert decision.seller_id is None
    assert decision.next_seller_id == sellers[0].seller_id
    assert decision.consumed_credit_seller_ids == ()


def test_ac08_credits_cross_rotations_and_are_consumed_exactly_once() -> None:
    """Breaks if directed credits disappear, are skipped, or make a balance negative."""
    renato = _seller(credits=3)
    sandra, jessica, nelma = [_seller() for _ in range(3)]
    sellers = [renato, sandra, jessica, nelma]
    cursor = renato.seller_id
    assigned = []
    consumed = 0

    for _ in range(4):
        decision = QueueRules.select_normal(sellers, cursor)
        assigned.append(decision.seller_id)
        consumed += decision.consumed_credit_seller_ids.count(renato.seller_id)
        renato = SellerState(
            renato.seller_id,
            True,
            False,
            False,
            renato.skip_balance - decision.consumed_credit_seller_ids.count(renato.seller_id),
        )
        sellers = [renato, sandra, jessica, nelma]
        cursor = decision.next_seller_id

    assert assigned == [sandra.seller_id, jessica.seller_id, nelma.seller_id, sandra.seller_id]
    assert consumed == 2
    assert renato.skip_balance == 1


def test_only_operational_seller_with_credit_consumes_it_then_receives_the_lead() -> None:
    """Breaks if a finite skip balance can park a lead forever or fall below zero."""
    renato = _seller(credits=2)
    others = [_seller(overdue=True) for _ in range(3)]

    decision = QueueRules.select_normal([renato, *others], renato.seller_id)

    assert decision.seller_id == renato.seller_id
    assert decision.consumed_credit_seller_ids == (renato.seller_id, renato.seller_id)
    assert decision.next_seller_id == others[0].seller_id


def test_current_assignment_has_a_partial_unique_database_guard() -> None:
    """Breaks if concurrent commands can persist two current assignments for one lead."""
    definitions = {definition.name: definition for definition in INDEXES}

    guard = definitions["assignments_current_lead_unique"]
    assert guard.keys == (("leadId", 1),)
    assert guard.unique is True
    assert guard.partial_filter == {"current": True}


def test_skip_balance_schema_rejects_negative_values() -> None:
    """Breaks if a direct or buggy write can persist a negative compensation balance."""
    balance = SCHEMA_VALIDATORS[MongoCollections.SKIP_BALANCES]["$jsonSchema"]

    assert balance["required"] == ["sellerId", "balance"]
    assert balance["properties"]["balance"] == {"bsonType": "int", "minimum": 0}
    definitions = {definition.name: definition for definition in INDEXES}
    assert definitions["skip_balances_seller_unique"].keys == (("sellerId", 1),)
