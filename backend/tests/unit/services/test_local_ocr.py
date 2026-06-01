from __future__ import annotations

from pathlib import Path

import pytest
from botocore.exceptions import ClientError

from app.agents.tools.extraction_mapper import map_pay_stub
from app.agents.tools.ocr_runner import run_ocr
from app.services.ocr import local as local_ocr

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures" / "documents"


def test_local_ocr_parses_pay_stub():
    content = (FIXTURES / "synthetic_pay_stub.txt").read_bytes()
    ocr = local_ocr.analyze(content)
    assert "Gross Pay" in ocr.text
    assert ocr.key_values.get("Employer") == "Acme Corp"
    assert ocr.key_values.get("Gross Pay") == "8500.00"


def test_local_ocr_parses_w2():
    content = (FIXTURES / "synthetic_w2.txt").read_bytes()
    ocr = local_ocr.analyze(content)
    assert "96000.00" in ocr.text
    assert "Acme Corp" in ocr.key_values.get("Employer Name", "")


def test_local_ocr_feeds_extraction_mapper():
    content = (FIXTURES / "synthetic_pay_stub.txt").read_bytes()
    ocr = local_ocr.analyze(content)
    out = map_pay_stub(ocr, document_id=1)
    assert out["income"][0]["gross_income"] == 8500.0


def test_run_ocr_falls_back_to_local_when_textract_unavailable(monkeypatch):
    def _raise(*_args, **_kwargs):
        raise ClientError(
            {"Error": {"Code": "SubscriptionRequiredException", "Message": "needs subscription"}},
            "AnalyzeDocument",
        )

    monkeypatch.setattr("app.agents.tools.ocr_runner.textract.analyze", _raise)

    content = (FIXTURES / "synthetic_pay_stub.txt").read_bytes()
    ocr = run_ocr(content)
    assert ocr.key_values.get("Gross Pay") == "8500.00"
