from app.agents.prompts.messaging import MESSAGING_SYSTEM_PROMPT


def test_messaging_prompt_contains_guardrails():
    assert "final approval" in MESSAGING_SYSTEM_PROMPT.lower()
    assert "internal" in MESSAGING_SYSTEM_PROMPT.lower()
    assert "borrower" in MESSAGING_SYSTEM_PROMPT.lower()
