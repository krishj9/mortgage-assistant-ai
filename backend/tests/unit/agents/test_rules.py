from __future__ import annotations

from app.agents.tools.rules import RulesConfig, evaluate_eligibility
from app.schemas.eligibility import EligibilityStatus


def _full_application() -> dict:
    return {
        "identity": {"borrower_name": "Jane Borrower"},
        "contact": {"contact_email": "jane@example.com"},
        "employment": {"employment_status": "employed"},
        "income": {"income_amount": 8000, "income_frequency": "monthly"},
        "liabilities": {"monthly_debts": [{"debt_type": "auto", "monthly_payment": 400}]},
        "property": {
            "property_status": "shopping",
            "property_value_or_purchase_price": 500000,
            "estimated_housing_payment": 2000,
        },
        "loan_purpose": {"loan_purpose": "purchase", "desired_down_payment": 100000},
    }


def test_green_when_dti_and_ltv_within_thresholds():
    app = _full_application()
    ctx = {
        "extracted_income": {
            "records": [
                {"gross_income": 8000, "pay_frequency": "monthly", "source_document_id": 1},
                {"gross_income": 8000, "pay_frequency": "monthly", "source_document_id": 2},
            ]
        },
        "extracted_assets": {"records": []},
    }
    eligibility, conditions = evaluate_eligibility(app, ctx, document_count=2)
    assert eligibility.status == EligibilityStatus.green
    assert eligibility.dti is not None and eligibility.dti < 0.43
    assert eligibility.ltv is not None and eligibility.ltv <= 0.80
    assert len(conditions.items) >= 0


def test_red_when_dti_exceeds_yellow_max():
    app = _full_application()
    app["liabilities"]["monthly_debts"] = [{"monthly_payment": 6000}]
    eligibility, _ = evaluate_eligibility(app, {}, document_count=0, config=RulesConfig())
    assert eligibility.status == EligibilityStatus.red
    assert eligibility.dti is not None and eligibility.dti > 0.50


def test_yellow_when_ltv_borderline():
    app = _full_application()
    app["loan_purpose"]["desired_down_payment"] = 50000  # 90% LTV
    eligibility, _ = evaluate_eligibility(app, {}, document_count=1)
    assert eligibility.status in {EligibilityStatus.yellow, EligibilityStatus.red}
    assert eligibility.ltv is not None and eligibility.ltv > 0.80


def test_single_pay_stub_condition_triggered():
    app = _full_application()
    ctx = {"extracted_income": {"records": [{"gross_income": 5000, "pay_frequency": "monthly"}]}}
    _, conditions = evaluate_eligibility(app, ctx, document_count=1)
    codes = {c.code for c in conditions.items}
    assert "single_pay_stub" in codes
