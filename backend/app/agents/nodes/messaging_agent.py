from __future__ import annotations

import json
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.prompts.messaging import MESSAGING_SYSTEM_PROMPT
from app.schemas.agent_io import MessageDrafts
from app.schemas.eligibility import ConditionsList, EligibilityResult
from app.services.bedrock.client import get_structured_model, invoke_structured


def _template_messages(
    eligibility: EligibilityResult,
    conditions: ConditionsList,
    borrower_name: str | None,
) -> tuple[str, str]:
    name = borrower_name or "Borrower"
    status = eligibility.status.value
    cond_lines = "\n".join(f"- {c.title}: {c.rationale}" for c in conditions.items) or "- None at this time."

    dti_line = f"DTI: {eligibility.dti:.1%}" if eligibility.dti is not None else "DTI: n/a"
    internal = f"Pre-qualification draft for {name}\nStatus: {status.upper()}\n{dti_line}"
    if eligibility.ltv is not None:
        internal += f"\nLTV: {eligibility.ltv:.1%}"
    internal += f"\n\nRecommended conditions:\n{cond_lines}\n\n(Draft — requires LO approval.)"

    borrower = (
        f"Hi {name}, thank you for your application. "
        f"Our preliminary review suggests a {status} pre-qualification picture "
        f"(informational only, not a final decision).\n\n"
        f"Next steps:\n{cond_lines}\n\n"
        "A loan officer will review these items and follow up with you."
    )
    return internal, borrower


def run_messaging_agent(
    application: dict[str, Any],
    eligibility: EligibilityResult,
    conditions: ConditionsList,
) -> tuple[str, str]:
    identity = application.get("identity") or {}
    borrower_name = identity.get("borrower_name")
    fallback_internal, fallback_borrower = _template_messages(eligibility, conditions, borrower_name)

    try:
        model = get_structured_model(MessageDrafts, tags=["messaging"])
        payload = {
            "borrower_name": borrower_name,
            "loan_purpose": (application.get("loan_purpose") or {}).get("loan_purpose"),
            "eligibility": eligibility.model_dump(mode="json"),
            "conditions": [c.model_dump() for c in conditions.items],
        }
        result = invoke_structured(
            model,
            [
                SystemMessage(content=MESSAGING_SYSTEM_PROMPT),
                HumanMessage(
                    content=(
                        "Draft an internal loan-officer summary and a borrower-facing "
                        "message based on this data:\n\n" + json.dumps(payload)
                    )
                ),
            ],
            tags=["messaging"],
        )
        if isinstance(result, MessageDrafts) and result.internal_draft.strip() and result.borrower_draft.strip():
            return result.internal_draft.strip(), result.borrower_draft.strip()
    except Exception:
        pass

    return fallback_internal, fallback_borrower
