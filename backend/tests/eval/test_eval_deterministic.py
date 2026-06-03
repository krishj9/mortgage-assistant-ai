from __future__ import annotations

import pytest

from evals.scorers.document import score_document_case
from evals.scorers.intake import score_intake_l0_case
from evals.scorers.schema import score_schema_compliance
from evals import datasets_dir, load_jsonl


def test_schema_compliance_score():
    assert score_schema_compliance() == 1.0


def test_intake_l0_eval_cases():
    path = datasets_dir() / "intake_smoke.jsonl"
    for case in load_jsonl(path):
        result = score_intake_l0_case(case)
        assert result["score"] >= 0.0


def test_document_heuristic_eval_cases():
    path = datasets_dir() / "document_smoke.jsonl"
    for case in load_jsonl(path):
        result = score_document_case(case)
        assert result["score"] == 1.0, result


def test_bank_statement_fixture_mapper():
    import json
    from pathlib import Path

    from app.agents.tools.extraction_mapper import map_bank_statement
    from app.services.ocr.base import OcrResult

    fixture = Path(__file__).resolve().parents[1] / "fixtures" / "ocr" / "bank_statement_sample.json"
    payload = json.loads(fixture.read_text())
    ocr = OcrResult(text=payload["text"], key_values=payload["key_values"], tables=[], raw=payload)
    out = map_bank_statement(ocr, document_id=4)
    assert out["assets"][0]["average_balance"] == 12500.5
