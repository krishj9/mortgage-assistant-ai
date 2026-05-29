from __future__ import annotations

from app.agents.intake_slots import is_l0_confident, try_l0_slot_parse


def test_l0_income_amount_keyed():
    patch = try_l0_slot_parse("I make about $8,500 a month", "Income amount")
    assert patch["income"]["income_amount"] == 8500.0
    assert is_l0_confident("I make about $8,500 a month", patch, "Income amount")


def test_l0_income_frequency_keyed():
    patch = try_l0_slot_parse("monthly", "Income frequency")
    assert patch["income"]["income_frequency"] == "monthly"
    assert is_l0_confident("monthly", patch, "Income frequency")


def test_l0_email_keyed():
    patch = try_l0_slot_parse("you can reach me at jane@example.com", "Contact email")
    assert patch["contact"]["contact_email"] == "jane@example.com"
    assert is_l0_confident("you can reach me at jane@example.com", patch, "Contact email")


def test_l0_not_confident_when_no_match():
    patch = try_l0_slot_parse("I'm not sure yet", "Income amount")
    assert patch == {}
    assert not is_l0_confident("I'm not sure yet", patch, "Income amount")


def test_l0_ambiguous_multiple_amounts_defers_to_llm():
    msg = "purchase price is 450000 and I put down 90000"
    patch = try_l0_slot_parse(msg, "Property value/purchase price")
    # Keyword anchors to purchase price, but two amounts present -> not confident.
    assert not is_l0_confident(msg, patch, "Property value/purchase price")


def test_l0_loan_purpose_keyed():
    patch = try_l0_slot_parse("I want to refinance my home", "Loan purpose")
    assert patch["loan_purpose"]["loan_purpose"] == "refinance"
    assert is_l0_confident("I want to refinance my home", patch, "Loan purpose")
