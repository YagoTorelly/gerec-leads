"""Unit coverage for the canonical source-row normalization boundary."""

from datetime import UTC, datetime

from gerec_api.domain.normalization import normalize_source_row


def test_normalize_source_row_canonicalizes_commercial_identity_and_contact_fields() -> None:
    """Breaks if equivalent source values stop producing one stable internal identity."""
    normalized = normalize_source_row(
        {
            "id": " lead-001 ",
            "created_time": "27/08/2026 10:30",
            "campaign_id": " campaign-01 ",
            "campaign_name": " Campanha Empresarial ",
            "document": "04.252.011/0001-10",
            "state": "São Paulo",
            "full_name": " Maria da Silva ",
            "phone_number": "(11) 99876-5432",
            "email": " MARIA@EXAMPLE.COM ",
        }
    )

    assert normalized.source_lead_id == "lead-001"
    assert normalized.source_entered_at == datetime(2026, 8, 27, 13, 30, tzinfo=UTC)
    assert normalized.campaign_external_id == "campaign-01"
    assert normalized.campaign_name == "Campanha Empresarial"
    assert normalized.document_normalized == "04252011000110"
    assert normalized.state == "SP"
    assert normalized.contact_name == "Maria da Silva"
    assert normalized.phone_normalized == "5511998765432"
    assert normalized.email_normalized == "maria@example.com"
    assert normalized.data_issues == ()


def test_mock_projection_contains_only_m_through_p_and_never_treats_m_as_document() -> None:
    """Breaks if the mock answer in column M becomes a CNPJ or column Q leaks to sellers."""
    normalized = normalize_source_row(
        {
            "id": "mock-001",
            "created_time": "2026-08-25T13:39:01-05:00",
            "campaign_id": "campaign-01",
            "campaign_name": "Campanha",
            "voc\u00ea_tem_cnpj_ou_mei?": "Sim, tenho CNPJ 04.252.011/0001-10",
            "full_name": "Contato Mock",
            "phone_number": "+55 11 98765-4321",
            "email": "contato@example.com",
            "lead_status": "NEW",
        }
    )

    assert normalized.document_normalized is None
    assert normalized.source_projection == {
        "voc\u00ea_tem_cnpj_ou_mei?": "Sim, tenho CNPJ 04.252.011/0001-10",
        "full_name": "Contato Mock",
        "phone_number": "+55 11 98765-4321",
        "email": "contato@example.com",
    }
    assert "lead_status" not in normalized.source_projection
    assert normalized.data_issues == ("document", "state")


def test_invalid_document_state_email_and_date_are_reported_without_inventing_values() -> None:
    """Breaks if malformed source data becomes distributable after lossy normalization."""
    normalized = normalize_source_row(
        {
            "id": "invalid-001",
            "created_time": "not-a-date",
            "campaign_name": "Campanha",
            "document": "11.111.111/1111-11",
            "state": "Estado inexistente",
            "full_name": "Contato",
            "phone_number": "123",
            "email": "not-an-email",
        }
    )

    assert normalized.source_entered_at is None
    assert normalized.document_normalized is None
    assert normalized.state is None
    assert normalized.phone_normalized is None
    assert normalized.email_normalized is None
    assert normalized.data_issues == ("source_entered_at", "document", "state", "phone", "email")
