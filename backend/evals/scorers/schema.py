from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from app.schemas.agent_io import (
    ConditionRefinement,
    DocumentClassification,
    IntakeGuidance,
    IntakeTurn,
    LoanApplicationPatch,
    MessageDrafts,
)


def validate_agent_io_examples() -> list[tuple[str, bool, str | None]]:
    """Return (schema_name, passed, error) for valid golden examples."""
    valid_cases: list[tuple[type, dict[str, Any], str]] = [
        (IntakeTurn, {"assistant_message": "Thanks!", "patch": None, "intent": "answer"}, "IntakeTurn"),
        (IntakeGuidance, {"assistant_message": "Please share your employer name."}, "IntakeGuidance"),
        (LoanApplicationPatch, {"employment": {"employer": "Acme Corp"}}, "LoanApplicationPatch"),
        (
            DocumentClassification,
            {"predicted_type": "pay_stub", "confidence": 0.9},
            "DocumentClassification",
        ),
        (
            MessageDrafts,
            {"internal_draft": "Internal notes", "borrower_draft": "Hi borrower"},
            "MessageDrafts",
        ),
        (
            ConditionRefinement,
            {
                "items": [
                    {
                        "id": "1",
                        "code": "single_pay_stub",
                        "title": "Pay stub",
                        "rationale": "Verify income",
                    }
                ]
            },
            "ConditionRefinement",
        ),
    ]
    results: list[tuple[str, bool, str | None]] = []
    for model, payload, name in valid_cases:
        try:
            model.model_validate(payload)
            results.append((name, True, None))
        except ValidationError as exc:
            results.append((name, False, str(exc)))
    return results


def score_schema_compliance() -> float:
    results = validate_agent_io_examples()
    if not results:
        return 0.0
    passed = sum(1 for _, ok, _ in results if ok)
    return passed / len(results)
