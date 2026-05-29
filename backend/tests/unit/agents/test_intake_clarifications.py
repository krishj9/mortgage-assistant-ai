from __future__ import annotations

from app.agents.intake_clarifications import field_aware_reply
from app.agents.intake_progress import is_meta_intent, needs_guidance, still_stuck_on_field
from app.schemas.agent_io import IntakeTurn


def test_still_stuck_on_field():
    assert still_stuck_on_field(["Property status"], ["Property status"]) is True
    assert still_stuck_on_field(["Property status"], ["Loan purpose"]) is False


def test_needs_guidance_when_answer_did_not_advance():
    assert (
        needs_guidance(
            missing_before=["Income amount"],
            missing_after=["Income amount"],
            borrower_message="a lot",
            turn=IntakeTurn(assistant_message="", intent="answer"),
        )
        is True
    )


def test_needs_guidance_false_for_recap():
    assert (
        needs_guidance(
            missing_before=["Income amount"],
            missing_after=["Income amount"],
            borrower_message="what did I say?",
            turn=IntakeTurn(assistant_message="You said...", intent="recap_request"),
        )
        is False
    )


def test_is_meta_intent():
    assert is_meta_intent(IntakeTurn(assistant_message="hi", intent="smalltalk")) is True
    assert is_meta_intent(IntakeTurn(assistant_message="hi", intent="answer")) is False


def test_field_aware_reply_without_progress_does_not_say_thanks():
    reply = field_aware_reply(["Property status"], made_progress=False)
    assert reply.startswith("Where are you")
    assert "Thanks" not in reply.split(".")[0]
