from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.agents.document_errors import UnsupportedDocumentError
from app.agents.nodes import document_understanding_agent as dua
from app.services.llamaindex.parse import ParseResult
from app.services.ocr.base import OcrResult


def test_classify_pay_stub_from_filename():
    predicted, confidence = dua.classify_document("synthetic_pay_stub.pdf", "")
    assert predicted == "pay_stub"
    assert confidence >= 0.75


def test_run_document_understanding_llamaindex_pay_stub(monkeypatch):
    monkeypatch.setattr(dua.settings, "DOCUMENT_PARSER", "llamaindex")
    monkeypatch.setattr(dua.settings, "LLAMA_CLOUD_API_KEY", "llx-test")

    parsed = ParseResult(
        text="Employer: Acme Corp\nGross Pay: 8500.00",
        parse_job_id="pjb-test-123",
        key_values={"Employer": "Acme Corp"},
        raw={"source": "llamaparse"},
    )

    monkeypatch.setattr(dua, "parse_document", lambda *_args, **_kwargs: parsed)
    monkeypatch.setattr(
        dua,
        "extract_structured",
        lambda _job_id, _doc_type: {
            "employer": "Acme Corp",
            "gross_pay": 8500.0,
            "pay_frequency": "bi-weekly",
        },
    )

    predicted, confidence, ocr, normalized, _field_confidence = dua.run_document_understanding(
        b"Employer: Acme Corp\nGross Pay: 8500.00",
        "synthetic_pay_stub.txt",
        document_id=11,
    )

    assert predicted == "pay_stub"
    assert confidence >= 0.75
    assert ocr.raw["source"] == "llamaparse"
    assert normalized["income"][0]["gross_income"] == 8500.0


def test_run_document_understanding_llamaindex_bank_statement(monkeypatch):
    monkeypatch.setattr(dua.settings, "DOCUMENT_PARSER", "llamaindex")
    monkeypatch.setattr(dua.settings, "LLAMA_CLOUD_API_KEY", "llx-test")

    parsed = ParseResult(
        text="Ending Balance: 12500.50\nAccount Number: 1234",
        parse_job_id="pjb-bank-1",
        key_values={},
        raw={"source": "llamaparse"},
    )

    monkeypatch.setattr(dua, "parse_document", lambda *_args, **_kwargs: parsed)
    monkeypatch.setattr(
        dua,
        "extract_structured",
        lambda _job_id, _doc_type: {
            "account_type": "checking",
            "ending_balance": 12500.5,
        },
    )

    predicted, _confidence, _ocr, normalized, _field_confidence = dua.run_document_understanding(
        b"Ending Balance: 12500.50",
        "bank_statement_jan.pdf",
        document_id=12,
    )

    assert predicted == "bank_statement"
    assert normalized["assets"][0]["average_balance"] == 12500.5


def test_run_document_understanding_textract_path(monkeypatch):
    monkeypatch.setattr(dua.settings, "DOCUMENT_PARSER", "textract")

    monkeypatch.setattr(
        dua,
        "run_ocr",
        lambda *_args, **_kwargs: OcrResult(
            text="Ending Balance: 12500.50",
            key_values={},
            raw={"source": "textract"},
        ),
    )

    predicted, _confidence, ocr, normalized, _field_confidence = dua.run_document_understanding(
        b"Ending Balance: 12500.50",
        "bank_statement_jan.pdf",
        document_id=13,
    )

    assert predicted == "bank_statement"
    assert ocr.raw["source"] == "textract"
    assert normalized["assets"][0]["average_balance"] == 12500.5


def test_run_document_understanding_rejects_unknown_type(monkeypatch):
    monkeypatch.setattr(dua.settings, "DOCUMENT_PARSER", "textract")
    monkeypatch.setattr(
        dua,
        "run_ocr",
        lambda *_args, **_kwargs: OcrResult(text="random content", key_values={}, raw={}),
    )

    with pytest.raises(UnsupportedDocumentError):
        dua.run_document_understanding(
            b"random content",
            "generic_document.pdf",
            document_id=14,
        )


def test_run_document_understanding_requires_llama_key(monkeypatch):
    monkeypatch.setattr(dua.settings, "DOCUMENT_PARSER", "llamaindex")
    monkeypatch.setattr(dua.settings, "LLAMA_CLOUD_API_KEY", "")

    with pytest.raises(UnsupportedDocumentError):
        dua.run_document_understanding(
            b"Employer: Acme Corp\nGross Pay: 8500.00",
            "synthetic_pay_stub.txt",
            document_id=15,
        )
