from __future__ import annotations

from typing import Any

from app.agents.intake_slots import extract_patch_from_message


def score_intake_l0_case(case: dict[str, Any]) -> dict[str, Any]:
    inp = case["input"]
    expected = case["expected"]
    field = inp["missing_fields"][0] if inp.get("missing_fields") else None
    patch = extract_patch_from_message(inp["message"])
    errors: list[str] = []

    if expected.get("intent") == "meta" and patch:
        errors.append("expected no patch for meta intent")

    if "employer" in expected:
        employer = (patch or {}).get("employment", {}).get("employer")
        if employer != expected["employer"]:
            errors.append(f"employer mismatch: {employer} != {expected['employer']}")

    if "email" in expected:
        email = (patch or {}).get("contact", {}).get("contact_email")
        if email != expected["email"]:
            errors.append(f"email mismatch: {email} != {expected['email']}")

    score = 1.0 if not errors else 0.0
    return {"score": score, "errors": errors, "patch": patch}
