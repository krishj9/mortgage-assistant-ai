from __future__ import annotations

from app.schemas.agent_io import IntakeTurn

_META_INTENTS = frozenset({"clarify_question", "recap_request", "smalltalk"})


def still_stuck_on_field(missing_before: list[str], missing_after: list[str]) -> bool:
    """True when the first missing field did not change — the latest answer did not advance intake."""
    if not missing_before or not missing_after:
        return False
    return missing_before[0] == missing_after[0]


def is_meta_intent(turn: IntakeTurn | None) -> bool:
    """True when the borrower is not trying to fill the current field (question, recap, etc.)."""
    return turn is not None and turn.intent in _META_INTENTS


def needs_guidance(
    *,
    missing_before: list[str],
    missing_after: list[str],
    borrower_message: str,
    turn: IntakeTurn | None,
) -> bool:
    """
    True when the borrower replied but intake did not move past the current field,
    so the LLM should guide them toward a valid answer.
    """
    if not borrower_message.strip() or not missing_before:
        return False
    if is_meta_intent(turn):
        return False
    return still_stuck_on_field(missing_before, missing_after)
