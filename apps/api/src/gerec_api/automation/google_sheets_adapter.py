"""Read the definitive Google Sheets source without exposing credentials to clients."""

from __future__ import annotations

import json
import os
from collections.abc import Callable, Iterable
from typing import Any
from urllib.parse import quote
from urllib.request import Request, urlopen

from google.auth.transport.requests import Request as GoogleAuthRequest
from google.oauth2 import service_account

from gerec_api.automation.workbook_adapter import EXPECTED_HEADERS, InvalidWorkbookError
from gerec_api.domain.normalization import NormalizedSourceRow, normalize_source_row


class GoogleSheetsAdapter:
    """Read one complete `Leads!A:Q` snapshot through the Sheets Values API."""

    def __init__(
        self,
        spreadsheet_id: str,
        range_name: str,
        access_token: str,
        *,
        fetch: Callable[[str], dict[str, Any]] | None = None,
    ) -> None:
        if not spreadsheet_id or not range_name or not access_token:
            raise ValueError("Google Sheets spreadsheet, range and access token are required")
        self._spreadsheet_id = spreadsheet_id
        self._range_name = range_name
        self._access_token = access_token
        self._fetch = fetch or self._fetch_json

    @classmethod
    def from_env(cls) -> "GoogleSheetsAdapter":
        service_account_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "")
        access_token = os.environ.get("GOOGLE_SHEETS_ACCESS_TOKEN", "")
        if service_account_json:
            credentials = service_account.Credentials.from_service_account_info(
                json.loads(service_account_json),
                scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"],
            )
            credentials.refresh(GoogleAuthRequest())
            access_token = credentials.token or ""
        return cls(
            os.environ.get("GOOGLE_SHEETS_SPREADSHEET_ID", ""),
            os.environ.get("GOOGLE_SHEETS_RANGE", "Leads!A:Q"),
            access_token,
        )

    def read(self) -> Iterable[NormalizedSourceRow]:
        values = self._fetch(self._url).get("values")
        if not isinstance(values, list) or not values:
            raise InvalidWorkbookError("Google Sheets response has no headers")
        if tuple(values[0]) != EXPECTED_HEADERS:
            raise InvalidWorkbookError("Google Sheets headers do not match the exact A-Q contract")
        for source_values in values[1:]:
            row = [*source_values, *([None] * (len(EXPECTED_HEADERS) - len(source_values)))]
            row = row[: len(EXPECTED_HEADERS)]
            if any(value is not None and str(value).strip() for value in row):
                yield normalize_source_row(
                    dict(zip(EXPECTED_HEADERS, row, strict=True)),
                    required_fields={"contact_name", "phone", "email"},
                )

    @property
    def _url(self) -> str:
        return f"https://sheets.googleapis.com/v4/spreadsheets/{quote(self._spreadsheet_id, safe='')}/values/{quote(self._range_name, safe='')}"

    def _fetch_json(self, url: str) -> dict[str, Any]:
        request = Request(url, headers={"Authorization": f"Bearer {self._access_token}"})
        with urlopen(request, timeout=15) as response:  # nosec B310: fixed Google endpoint.
            return json.loads(response.read().decode("utf-8"))
