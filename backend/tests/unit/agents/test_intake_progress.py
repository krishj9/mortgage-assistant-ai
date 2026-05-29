from __future__ import annotations

from app.agents.intake_progress import needs_guidance, still_stuck_on_field
from app.schemas.agent_io import IntakeTurn


def test_still_stuck_detects_no_progress():
    assert still_stuck_on_field(["Contact email"], ["Contact email"])


def test_needs_guidance_any_invalid_field():
    for field in ("Contact email", "Income amount", "Loan purpose", "Property status"):
        assert needs_guidance(
            missing_before=[field],
            missing_after=[field],
            borrower_message="not a valid answer",
            turn=IntakeTurn(assistant_message="", intent="answer"),
        )
