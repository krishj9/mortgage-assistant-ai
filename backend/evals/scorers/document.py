from __future__ import annotations

from typing import Any

from app.agents.nodes.document_understanding_agent import classify_document
from app.agents.tools.extraction_mapper import map_pay_stub, map_w2
from app.services.ocr.base import OcrResult


def score_document_case(case: dict[str, Any]) -> dict[str, Any]:
    inp = case["input"]
    expected = case["expected"]
    predicted_type, confidence = classify_document(inp["filename"], inp["text"])
    errors: list[str] = []
    if predicted_type != expected["predicted_type"]:
        errors.append(f"type mismatch: {predicted_type} != {expected['predicted_type']}")

    gross = None
    if predicted_type == "pay_stub":
        ocr = OcrResult(text=inp["text"], key_values={}, tables=[], raw={})
        normalized = map_pay_stub(ocr, document_id=1)
        gross = normalized.get("income", [{}])[0].get("gross_income")
    elif predicted_type == "w2":
        ocr = OcrResult(text=inp["text"], key_values={}, tables=[], raw={})
        normalized = map_w2(ocr, document_id=1)
        gross = normalized.get("income", [{}])[0].get("gross_income")

    if "gross_income" in expected and gross is not None:
        if abs(float(gross) - float(expected["gross_income"])) > 0.01:
            errors.append(f"gross_income mismatch: {gross} != {expected['gross_income']}")

    score = 1.0 if not errors else max(0.0, 1.0 - 0.33 * len(errors))
    return {
        "score": score,
        "errors": errors,
        "predicted_type": predicted_type,
        "confidence": confidence,
    }
