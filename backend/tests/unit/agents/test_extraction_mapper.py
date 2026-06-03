from __future__ import annotations

import json
from pathlib import Path

from app.agents.tools.extraction_mapper import map_bank_statement, map_pay_stub, map_w2
from app.services.ocr.base import OcrResult

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures" / "ocr"


def _load(name: str) -> OcrResult:
    payload = json.loads((FIXTURES / name).read_text())
    return OcrResult(
        text=payload.get("text", ""),
        key_values=payload.get("key_values", {}),
        tables=[],
        raw=payload,
    )


def test_map_pay_stub():
    ocr = _load("pay_stub_sample.json")
    out = map_pay_stub(ocr, document_id=1)
    assert out["income"]
    assert out["income"][0]["gross_income"] == 8500.0
    assert out["income"][0]["employer"] == "Acme Corp"


def test_map_w2_from_fixture():
    ocr = _load("w2_sample.json")
    out = map_w2(ocr, document_id=2)
    assert out["income"][0]["gross_income"] == 96000.0
    assert out["income"][0]["pay_frequency"] == "annual"


def test_map_w2_from_text():
    ocr = OcrResult(text="Employer: Acme\nWages: 96000.00", key_values={"Employer": "Acme"})
    out = map_w2(ocr, document_id=2)
    assert out["income"][0]["gross_income"] == 96000.0


def test_map_bank_statement_from_fixture():
    ocr = _load("bank_statement_sample.json")
    out = map_bank_statement(ocr, document_id=3)
    assert out["assets"][0]["average_balance"] == 12500.5


def test_map_bank_statement():
    ocr = OcrResult(text="Ending Balance: 12500.50", key_values={})
    out = map_bank_statement(ocr, document_id=3)
    assert out["assets"][0]["average_balance"] == 12500.5
