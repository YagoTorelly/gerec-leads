"""Fronteira de persist\u00eancia das empresas."""

from collections.abc import Mapping
from typing import Any

from pymongo.collection import Collection
from pymongo.results import InsertOneResult

from gerec_api.domain.documents import prepare_company_for_persistence


class CompanyRepository:
    """Persiste empresas somente depois da valida\u00e7\u00e3o de identidade do dom\u00ednio."""

    def __init__(self, companies: Collection) -> None:
        self._companies = companies

    def insert(self, company: Mapping[str, Any]) -> InsertOneResult:
        """Valida checksum, normaliza e persiste a empresa em uma \u00fanica fronteira."""
        return self._companies.insert_one(prepare_company_for_persistence(company))
