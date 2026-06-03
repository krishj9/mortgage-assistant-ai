from __future__ import annotations

import re
from typing import Any

FORBIDDEN_PHRASES = (
    "pre-approved",
    "pre approved",
    "guaranteed",
    "final approval",
    "binding commitment",
)


def score_messaging_drafts(internal_draft: str, borrower_draft: str) -> dict[str, Any]:
    errors: list[str] = []
    if len(internal_draft.strip()) < 20:
        errors.append("internal_draft too short")
    if len(borrower_draft.strip()) < 20:
        errors.append("borrower_draft too short")
    combined = f"{internal_draft} {borrower_draft}".lower()
    for phrase in FORBIDDEN_PHRASES:
        if phrase in combined:
            errors.append(f"forbidden phrase: {phrase}")
    score = 1.0 if not errors else max(0.0, 1.0 - 0.25 * len(errors))
    return {"score": score, "errors": errors}


def score_messaging_case(case: dict[str, Any], drafts: tuple[str, str]) -> float:
    result = score_messaging_drafts(drafts[0], drafts[1])
    expected_forbidden = case.get("expected", {}).get("forbidden_phrases", [])
    combined = f"{drafts[0]} {drafts[1]}".lower()
    for phrase in expected_forbidden:
        if phrase.lower() in combined:
            result["score"] = min(result["score"], 0.5)
    return float(result["score"])
