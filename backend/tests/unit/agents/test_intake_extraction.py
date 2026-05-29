from __future__ import annotations

from app.agents.nodes.intake_agent import extract_patch_from_message


def test_income_standalone_number():
    patch = extract_patch_from_message("8500")
    assert patch["income"]["income_amount"] == 8500.0


def test_income_with_dollar_and_monthly():
    patch = extract_patch_from_message("I earn $8,500 per month")
    assert patch["income"]["income_amount"] == 8500.0
    assert patch["income"]["income_frequency"] == "monthly"


def test_income_salary_is_k():
    patch = extract_patch_from_message("My salary is 75k annually")
    assert patch["income"]["income_amount"] == 75000.0
    assert patch["income"]["income_frequency"] == "annual"


def test_income_keyword_form():
    patch = extract_patch_from_message("My income is $5200")
    assert patch["income"]["income_amount"] == 5200.0
