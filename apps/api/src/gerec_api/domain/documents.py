"""Valida\u00e7\u00e3o de CPF e CNPJ antes da persist\u00eancia de empresas."""

from collections.abc import Iterable, Mapping
from typing import Any


class InvalidDocumentError(ValueError):
    """Documento ausente, malformado ou com d\u00edgitos verificadores inv\u00e1lidos."""


def normalize_document(value: str) -> str:
    """Conserva somente os d\u00edgitos usados pela identidade da empresa/contato."""
    return "".join(character for character in value if character.isdigit())


def require_valid_document(value: str) -> str:
    """Normaliza e devolve apenas CPF ou CNPJ com d\u00edgitos verificadores v\u00e1lidos."""
    normalized = normalize_document(value)
    if len(normalized) == 11 and _is_valid_cpf(normalized):
        return normalized
    if len(normalized) == 14 and _is_valid_cnpj(normalized):
        return normalized
    raise InvalidDocumentError("CPF ou CNPJ inv\u00e1lido para persist\u00eancia")


def prepare_company_for_persistence(company: Mapping[str, Any]) -> dict[str, Any]:
    """Devolve uma c\u00f3pia com CPF/CNPJ validado antes de uma escrita de empresa."""
    value = company.get("documentNormalized")
    if not isinstance(value, str):
        raise InvalidDocumentError("CPF ou CNPJ obrigat\u00f3rio para persist\u00eancia")
    prepared = dict(company)
    prepared["documentNormalized"] = require_valid_document(value)
    return prepared


def _is_valid_cpf(value: str) -> bool:
    if len(set(value)) == 1:
        return False
    return _check_digit(value[:9], (10, 9, 8, 7, 6, 5, 4, 3, 2)) == int(value[9]) and _check_digit(
        value[:10], (11, 10, 9, 8, 7, 6, 5, 4, 3, 2)
    ) == int(value[10])


def _is_valid_cnpj(value: str) -> bool:
    if len(set(value)) == 1:
        return False
    first = _check_digit(value[:12], (5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2))
    second = _check_digit(value[:12] + str(first), (6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2))
    return first == int(value[12]) and second == int(value[13])


def _check_digit(value: str, weights: Iterable[int]) -> int:
    total = sum(int(digit) * weight for digit, weight in zip(value, weights, strict=True))
    remainder = total % 11
    return 0 if remainder < 2 else 11 - remainder
