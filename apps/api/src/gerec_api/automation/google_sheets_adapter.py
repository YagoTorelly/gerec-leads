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


FIXED_HEADERS = EXPECTED_HEADERS[:12]
LEAD_STATUS_HEADER = "lead_status"


class GoogleSheetsAdapter:
    """Read every campaign tab while allowing a variable question section."""

    def __init__(
        self,
        spreadsheet_id: str,
        range_name: str,
        access_token: str,
        *,
        skip_source_ids: set[str] | None = None,
        fetch: Callable[[str], dict[str, Any]] | None = None,
    ) -> None:
        if not spreadsheet_id or not range_name or not access_token:
            raise ValueError("Google Sheets spreadsheet, range and access token are required")
        self._spreadsheet_id = spreadsheet_id
        self._range_name = range_name
        self._access_token = access_token
        self._fetch = fetch or self._fetch_json
        self._skip_source_ids = skip_source_ids or set()

    @classmethod
    def from_env(cls) -> "GoogleSheetsAdapter":
        service_account_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "")
        access_token = os.environ.get("GOOGLE_SHEETS_ACCESS_TOKEN", "")
        skip_ids = {item.strip() for item in os.environ.get("GOOGLE_SHEETS_SKIP_SOURCE_LEAD_IDS", "").split(",") if item.strip()}
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
            skip_source_ids=skip_ids,
        )

    def read(self) -> Iterable[NormalizedSourceRow]:
        for sheet_title in self._sheet_titles():
            yield from self._read_sheet(sheet_title)

    def _sheet_titles(self) -> Iterable[str]:
        response = self._fetch(self._metadata_url)
        metadata = response.get("sheets")
        # Keep the narrow one-range adapter contract usable in isolated tests.
        if not isinstance(metadata, list) and isinstance(response.get("values"), list):
            yield self._range_name.split("!", 1)[0] or "Leads"
            return
        if not isinstance(metadata, list) or not metadata:
            raise InvalidWorkbookError("Google Sheets response has no tabs")
        for sheet in metadata:
            properties = sheet.get("properties") if isinstance(sheet, dict) else None
            title = properties.get("title") if isinstance(properties, dict) else None
            if isinstance(title, str) and title.strip():
                yield title.strip()

    def _read_sheet(self, sheet_title: str) -> Iterable[NormalizedSourceRow]:
        values = self._fetch(self._values_url(sheet_title)).get("values")
        if not isinstance(values, list) or not values:
            raise InvalidWorkbookError(f"Google Sheets tab {sheet_title!r} has no headers")
        headers = tuple(str(value).strip() for value in values[0])
        self._validate_headers(sheet_title, headers)
        for source_values in values[1:]:
            row = [*source_values, *([None] * (len(headers) - len(source_values)))]
            row = row[: len(headers)]
            if str(row[0]).strip() in self._skip_source_ids:
                continue
            if any(value is not None and str(value).strip() for value in row):
                payload = dict(zip(headers, row, strict=True))
                payload["source_sheet_name"] = sheet_title
                if not payload.get("campaign_name"):
                    payload["campaign_name"] = sheet_title
                yield normalize_source_row(
                    payload,
                    required_fields={"contact_name", "phone", "email"},
                )

    @staticmethod
    def _validate_headers(sheet_title: str, headers: tuple[str, ...]) -> None:
        if len(headers) <= len(FIXED_HEADERS):
            raise InvalidWorkbookError(
                f"Google Sheets tab {sheet_title!r} must contain fixed columns and lead_status"
            )
        if headers[: len(FIXED_HEADERS)] != FIXED_HEADERS:
            raise InvalidWorkbookError(
                f"Google Sheets tab {sheet_title!r} has invalid fixed columns A-L"
            )
        if headers[-1] != LEAD_STATUS_HEADER:
            raise InvalidWorkbookError(
                f"Google Sheets tab {sheet_title!r} must end with lead_status"
            )
        if len(set(headers)) != len(headers):
            raise InvalidWorkbookError(
                f"Google Sheets tab {sheet_title!r} contains duplicate headers"
            )

    @property
    def _metadata_url(self) -> str:
        return f"https://sheets.googleapis.com/v4/spreadsheets/{quote(self._spreadsheet_id, safe='')}?fields=sheets.properties"

    def _values_url(self, sheet_title: str) -> str:
        range_name = f"{sheet_title}!A:ZZ"
        return f"https://sheets.googleapis.com/v4/spreadsheets/{quote(self._spreadsheet_id, safe='')}/values/{quote(range_name, safe='')}"

    def _fetch_json(self, url: str) -> dict[str, Any]:
        request = Request(url, headers={"Authorization": f"Bearer {self._access_token}"})
        with urlopen(request, timeout=15) as response:  # nosec B310: fixed Google endpoint.
            return json.loads(response.read().decode("utf-8"))
