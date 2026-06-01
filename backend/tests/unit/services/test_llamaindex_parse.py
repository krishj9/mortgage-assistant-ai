from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.services.llamaindex.client import LlamaIndexError, wait_for_job
from app.services.llamaindex.parse import _derive_key_values, _extract_parsed_text, parse_document


class _FakePage:
    def __init__(self, text: str):
        self.text = text


class _FakeText:
    def __init__(self, pages):
        self.pages = pages


class _FakeResponse:
    def __init__(self, text_full=None, text=None, markdown_full=None, markdown=None):
        self.text_full = text_full
        self.text = text
        self.markdown_full = markdown_full
        self.markdown = markdown


def test_extract_parsed_text_prefers_text_full():
    response = _FakeResponse(text_full="hello world")
    assert _extract_parsed_text(response) == "hello world"


def test_extract_parsed_text_joins_pages():
    response = _FakeResponse(text=_FakeText([_FakePage("line1"), _FakePage("line2")]))
    assert _extract_parsed_text(response) == "line1\nline2"


def test_derive_key_values():
    text = "Employer: Acme Corp\nGross Pay: 8500.00\n"
    kv = _derive_key_values(text)
    assert kv["Employer"] == "Acme Corp"
    assert kv["Gross Pay"] == "8500.00"


def test_parse_document_success(monkeypatch):
    client = MagicMock()
    parse_job = MagicMock(id="pjb-1", status="PENDING")
    completed_job = MagicMock(id="pjb-1", status="COMPLETED")
    get_response = _FakeResponse(
        text_full="Employer: Acme Corp\nGross Pay: 8500.00",
    )

    client.parsing.create.return_value = parse_job
    client.parsing.get.return_value = get_response

    monkeypatch.setattr("app.services.llamaindex.parse.get_client", lambda: client)
    monkeypatch.setattr(
        "app.services.llamaindex.parse.wait_for_job",
        lambda job, **kwargs: completed_job,
    )

    result = parse_document(b"Employer: Acme Corp\nGross Pay: 8500.00", "pay_stub.txt")

    assert result.parse_job_id == "pjb-1"
    assert "Acme Corp" in result.text
    assert result.key_values["Employer"] == "Acme Corp"
    assert result.raw["source"] == "llamaparse"


def test_parse_document_empty_text_raises(monkeypatch):
    client = MagicMock()
    parse_job = MagicMock(id="pjb-2", status="PENDING")
    completed_job = MagicMock(id="pjb-2", status="COMPLETED")

    client.parsing.create.return_value = parse_job
    client.parsing.get.return_value = _FakeResponse(text_full="   ")

    monkeypatch.setattr("app.services.llamaindex.parse.get_client", lambda: client)
    monkeypatch.setattr(
        "app.services.llamaindex.parse.wait_for_job",
        lambda job, **kwargs: completed_job,
    )

    with pytest.raises(LlamaIndexError, match="empty text"):
        parse_document(b" ", "pay_stub.txt")


def test_wait_for_job_raises_on_failure():
    job = MagicMock(id="job-fail", status="FAILED", error_message="boom")

    def _get(_job_id):
        return job

    with pytest.raises(LlamaIndexError, match="failed"):
        wait_for_job(job, get_job=_get, job_kind="parse")
