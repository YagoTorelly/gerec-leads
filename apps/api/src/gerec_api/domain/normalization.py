"""Normalize source rows into the stable ingestion contract."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal
from hashlib import sha256
import json
import re
from typing import Any, Mapping
from zoneinfo import ZoneInfo

from gerec_api.domain.documents import InvalidDocumentError, require_valid_document


SAO_PAULO = ZoneInfo("America/Sao_Paulo")
MOCK_QUESTION_HEADER = "voc\u00ea_tem_cnpj_ou_mei?"
MOCK_PROJECTION_HEADERS = (MOCK_QUESTION_HEADER, "full_name", "phone_number", "email")


class SourceRowValidationError(ValueError):
    """The row lacks the stable source identity required for idempotency."""


@dataclass(frozen=True)
class NormalizedSourceRow:
    """Versioned internal shape shared by workbook and future source adapters."""

    source_lead_id: str
    source_entered_at: datetime | None
    source_snapshot_id: str | None
    campaign_external_id: str | None
    campaign_name: str | None
    company_name: str | None
    document_normalized: str | None
    state: str | None
    contact_name: str | None
    phone_normalized: str | None
    email_normalized: str | None
    ad_external_id: str | None
    ad_name: str | None
    source_projection: dict[str, Any]
    source_payload: dict[str, Any]
    data_issues: tuple[str, ...]
    row_hash: str


def normalize_source_row(
    row: Mapping[str, Any], *, required_fields: set[str] | None = None
) -> NormalizedSourceRow:
    """Normalize one source row without making commercial decisions or inventing identity."""
    source_lead_id = _text(_first(row, "source_lead_id", "sourceLeadId", "id"))
    if source_lead_id is None:
        raise SourceRowValidationError("source lead id is required")

    source_entered_at = normalize_datetime(
        _first(row, "source_entered_at", "sourceEnteredAt", "created_time", "entry_date")
    )
    campaign_external_id = _text(_first(row, "campaign_external_id", "campaignExternalId", "campaign_id"))
    campaign_name = _text(_first(row, "campaign_name", "campaignName"))
    company_name = _text(_first(row, "company_name", "companyName"))
    document_normalized = normalize_valid_document(
        _first(row, "document", "document_number", "documentNormalized", "cnpj", "cpf_cnpj")
    )
    state = normalize_state(_first(row, "state", "estado", "uf"))
    contact_name = _text(_first(row, "contact_name", "contactName", "full_name", "name"))
    phone_normalized = normalize_phone(_first(row, "phone", "phone_number", "phoneNormalized"))
    email_normalized = normalize_email(_first(row, "email", "email_normalized", "emailNormalized"))
    source_snapshot_id = _text(_first(row, "source_snapshot_id", "sourceSnapshotId"))

    required_fields = required_fields or {
        "source_entered_at", "document", "state", "contact_name", "phone", "email"
    }
    issues: list[str] = []
    for field, value in (
        ("source_entered_at", source_entered_at),
        ("document", document_normalized),
        ("state", state),
        ("contact_name", contact_name),
        ("phone", phone_normalized),
        ("email", email_normalized),
    ):
        if value is None and field in required_fields:
            issues.append(field)
    if campaign_external_id is None and campaign_name is None:
        issues.append("campaign")

    source_projection = {
        header: _json_safe(row.get(header))
        for header in MOCK_PROJECTION_HEADERS
        if header in row
    }
    source_payload = {
        str(key): _json_safe(value)
        for key, value in row.items()
        if key not in {"source_snapshot_id", "sourceSnapshotId"}
    }
    hash_payload = {
        "sourceLeadId": source_lead_id,
        "sourceEnteredAt": _json_safe(source_entered_at),
        "campaignExternalId": campaign_external_id,
        "campaignName": campaign_name,
        "companyName": company_name,
        "documentNormalized": document_normalized,
        "state": state,
        "contactName": contact_name,
        "phoneNormalized": phone_normalized,
        "emailNormalized": email_normalized,
        "adExternalId": _text(_first(row, "ad_external_id", "adExternalId", "ad_id")),
        "adName": _text(_first(row, "ad_name", "adName")),
        "sourceProjection": source_projection,
        "sourcePayload": source_payload,
    }
    row_hash = sha256(
        json.dumps(hash_payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()

    return NormalizedSourceRow(
        source_lead_id=source_lead_id,
        source_entered_at=source_entered_at,
        source_snapshot_id=source_snapshot_id,
        campaign_external_id=campaign_external_id,
        campaign_name=campaign_name,
        company_name=company_name,
        document_normalized=document_normalized,
        state=state,
        contact_name=contact_name,
        phone_normalized=phone_normalized,
        email_normalized=email_normalized,
        ad_external_id=hash_payload["adExternalId"],
        ad_name=hash_payload["adName"],
        source_projection=source_projection,
        source_payload=source_payload,
        data_issues=tuple(issues),
        row_hash=row_hash,
    )


def normalize_valid_document(value: Any) -> str | None:
    text = _text(value)
    if text is None:
        return None
    try:
        return require_valid_document(text)
    except InvalidDocumentError:
        return None


def normalize_phone(value: Any) -> str | None:
    text = _text(value)
    if text is None:
        return None
    digits = "".join(character for character in text if character.isdigit())
    if len(digits) in (10, 11):
        digits = f"55{digits}"
    if len(digits) not in (12, 13) or not digits.startswith("55"):
        return None
    return digits


def normalize_email(value: Any) -> str | None:
    text = _text(value)
    if text is None:
        return None
    normalized = text.casefold()
    if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", normalized):
        return None
    return normalized


def normalize_state(value: Any) -> str | None:
    text = _text(value)
    if text is None:
        return None
    candidate = text.casefold()
    if len(text) == 2:
        abbreviation = text.upper()
        return abbreviation if abbreviation in _STATE_NAMES.values() else None
    return _STATE_NAMES.get(candidate)


def normalize_datetime(value: Any) -> datetime | None:
    if value is None or value == "":
        return None
    parsed: datetime
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, date):
        parsed = datetime.combine(value, datetime.min.time())
    else:
        text = str(value).strip()
        try:
            parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        except ValueError:
            parsed = _parse_local_datetime(text)
            if parsed is None:
                return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=SAO_PAULO)
    return parsed.astimezone(UTC)


def _parse_local_datetime(value: str) -> datetime | None:
    for pattern in ("%d/%m/%Y %H:%M", "%d/%m/%Y", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, pattern)
        except ValueError:
            continue
    return None


def _first(row: Mapping[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in row:
            return row[key]
    return None


def _text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _json_safe(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    return value


_STATE_NAMES = {
    "acre": "AC",
    "alagoas": "AL",
    "amap\u00e1": "AP",
    "amazonas": "AM",
    "bahia": "BA",
    "cear\u00e1": "CE",
    "distrito federal": "DF",
    "esp\u00edrito santo": "ES",
    "goi\u00e1s": "GO",
    "maranh\u00e3o": "MA",
    "mato grosso": "MT",
    "mato grosso do sul": "MS",
    "minas gerais": "MG",
    "par\u00e1": "PA",
    "para\u00edba": "PB",
    "paran\u00e1": "PR",
    "pernambuco": "PE",
    "piau\u00ed": "PI",
    "rio de janeiro": "RJ",
    "rio grande do norte": "RN",
    "rio grande do sul": "RS",
    "rond\u00f4nia": "RO",
    "roraima": "RR",
    "santa catarina": "SC",
    "s\u00e3o paulo": "SP",
    "sergipe": "SE",
    "tocantins": "TO",
}
