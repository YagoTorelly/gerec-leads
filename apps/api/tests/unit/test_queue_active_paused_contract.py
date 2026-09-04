"""Contrato QA da disponibilidade operacional sem SLA automático.

Esta suíte cobre a regra vigente: atraso de tratativa é apenas dado histórico e
não cria um terceiro estado de disponibilidade. Somente a pausa manual impede
novas atribuições.
"""

from bson import ObjectId

from gerec_api.domain.queue import QueueRules, SellerState


def _seller(*, active: bool = True, paused: bool = False) -> SellerState:
    return SellerState(
        seller_id=ObjectId(),
        active=active,
        paused=paused,
        skip_balance=0,
    )


def test_atraso_nao_cria_estado_bloqueado_e_vendedor_continua_ativo() -> None:
    seller = _seller()

    availability = QueueRules.availability(seller)

    assert availability.status == "active"
    assert availability.reason is None


def test_atraso_nao_impede_o_vendedor_de_receber_o_proximo_lead() -> None:
    overdue = _seller()
    next_seller = _seller()

    decision = QueueRules.select_normal([overdue, next_seller], overdue.seller_id)

    assert decision.seller_id == overdue.seller_id


def test_somente_pausa_manual_mantem_vendedor_fora_da_rotacao() -> None:
    paused = _seller(paused=True)
    active = _seller()

    availability = QueueRules.availability(paused)
    decision = QueueRules.select_normal([paused, active], paused.seller_id)

    assert availability.status == "paused"
    assert decision.seller_id == active.seller_id


def test_snapshot_de_atrasado_exibe_apenas_disponibilidade_operacional_valida() -> None:
    overdue = _seller()

    snapshot = QueueRules.snapshot([overdue], overdue.seller_id)

    assert snapshot.entries[0].availability.status in {"active", "paused"}
    assert snapshot.entries[0].availability.status == "active"
