from __future__ import annotations

# Last-resort templates when Bedrock is entirely unavailable.
FIELD_PROMPTS: dict[str, str] = {
    "Borrower full name": "What's your full legal name?",
    "Contact email": "What's the best email to reach you?",
    "Employment status": "Are you currently employed?",
    "Income amount": "How much do you earn (before taxes)?",
    "Income frequency": "Is that income monthly or annual?",
    "Property status": (
        "Where are you in the process — under contract on a home, still shopping, "
        "or refinancing a home you already own?"
    ),
    "Property value/purchase price": "What's the purchase price or estimated property value?",
    "Loan purpose": "Is this loan for a purchase or a refinance?",
}


def field_aware_reply(missing_fields: list[str], *, made_progress: bool) -> str:
    """Deterministic fallback only when all LLM calls fail."""
    if not missing_fields:
        return (
            "Thanks! Your intake details look complete for now. "
            "Next step: please upload your initial documents."
        )
    next_label = missing_fields[0]
    question = FIELD_PROMPTS.get(next_label, f"Could you share your {next_label.lower()}?")
    if made_progress:
        return f"Got it, thanks! {question}"
    return question
