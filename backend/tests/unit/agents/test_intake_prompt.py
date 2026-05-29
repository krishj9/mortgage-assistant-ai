from __future__ import annotations

from app.agents.prompts.intake import INTAKE_SYSTEM_PROMPT


def test_intake_prompt_contains_one_question_constraint():
    prompt = INTAKE_SYSTEM_PROMPT.lower()
    # The assistant must still ask for a single field at a time.
    assert "one" in prompt and "field at a time" in prompt
    assert "mortgage intake assistant" in prompt


def test_intake_prompt_includes_enum_aware_field_guide():
    # The enum-aware guide must disambiguate property status (the original bug).
    assert "field guide" in INTAKE_SYSTEM_PROMPT.lower()
    assert "under_contract" in INTAKE_SYSTEM_PROMPT
    assert "refinance" in INTAKE_SYSTEM_PROMPT
