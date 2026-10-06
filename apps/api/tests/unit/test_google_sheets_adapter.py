from urllib.parse import unquote, urlparse

import pytest

from gerec_api.automation.google_sheets_adapter import (
    FIXED_HEADERS,
    GoogleSheetsAdapter,
    InvalidWorkbookError,
)


def test_reads_all_tabs_with_variable_question_columns() -> None:
    question_a = "qual_o_tipo_de_seguro?"
    question_b = "quantas_vidas?"
    headers_a = [*FIXED_HEADERS, question_a, "lead_status"]
    headers_b = [*FIXED_HEADERS, question_a, question_b, "lead_status"]
    responses = {
        "metadata": {"sheets": [{"properties": {"title": "Campanha A"}}, {"properties": {"title": "Campanha B"}}]},
        "Campanha A": {"values": [headers_a, ["lead-a", "2026-10-01", None, None, None, None, "campaign-a", "Campanha A", None, None, None, None, "empresarial", "novo"]]},
        "Campanha B": {"values": [headers_b, ["lead-b", "2026-10-02", None, None, None, None, "campaign-b", "Campanha B", None, None, None, None, "vida", "10", "novo"]]},
    }

    def fetch(url: str) -> dict:
        if "fields=sheets.properties" in url:
            return responses["metadata"]
        title = unquote(urlparse(url).path.rsplit("/", 1)[-1]).split("!", 1)[0]
        return responses[title]

    rows = list(GoogleSheetsAdapter("sheet", "ignored", "token", fetch=fetch).read())

    assert [row.source_lead_id for row in rows] == ["lead-a", "lead-b"]
    assert rows[0].campaign_name == "Campanha A"
    assert rows[1].source_payload[question_b] == "10"
    assert rows[1].source_payload["source_sheet_name"] == "Campanha B"


def test_rejects_a_tab_without_lead_status_as_last_column() -> None:
    responses = {
        "metadata": {"sheets": [{"properties": {"title": "Campanha"}}]},
        "Campanha": {"values": [[*FIXED_HEADERS, "lead_status", "extra"]]},
    }

    def fetch(url: str) -> dict:
        if "fields=sheets.properties" in url:
            return responses["metadata"]
        return responses["Campanha"]

    with pytest.raises(InvalidWorkbookError, match="must end with lead_status"):
        list(GoogleSheetsAdapter("sheet", "ignored", "token", fetch=fetch).read())
