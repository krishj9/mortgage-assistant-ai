from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.agents.tools.application_writer import compute_missing_fields
from app.schemas.eligibility import (
    Condition,
    ConditionsList,
    EligibilityResult,
    EligibilityStatus,
    RuleEvaluation,
)


@dataclass(frozen=True)
class RulesConfig:
    dti_green_max: float = 0.43
    dti_yellow_max: float = 0.50
    ltv_green_max: float = 0.80
    ltv_yellow_max: float = 0.95


def _monthly_from_income(amount: float | None, frequency: str | None) -> float | None:
    if amount is None:
        return None
    if frequency == "annual":
        return amount / 12.0
    return amount


def _extracted_monthly_income(deal_context: dict[str, Any]) -> float:
    income_state = deal_context.get("extracted_income") or {}
    records = income_state.get("records") or []
    total = 0.0
    found = False
    for rec in records:
        gross = rec.get("gross_income")
        if gross is None:
            continue
        freq = (rec.get("pay_frequency") or "monthly").lower()
        monthly = gross if freq == "monthly" else gross / 12.0
        total += monthly
        found = True
    return total if found else 0.0


def _monthly_debts(application: dict[str, Any]) -> float:
    liabilities = application.get("liabilities") or {}
    debts = liabilities.get("monthly_debts") or []
    return sum(float(d.get("monthly_payment") or 0) for d in debts)


def _estimate_housing_payment(application: dict[str, Any], monthly_income: float | None) -> float:
    prop = application.get("property") or {}
    explicit = prop.get("estimated_housing_payment")
    if explicit is not None:
        return float(explicit)
    if monthly_income and monthly_income > 0:
        return monthly_income * 0.28
    return 0.0


def _loan_amount(application: dict[str, Any]) -> float | None:
    prop = application.get("property") or {}
    price = prop.get("property_value_or_purchase_price")
    if price is None:
        return None
    loan_purpose = application.get("loan_purpose") or {}
    down = loan_purpose.get("desired_down_payment") or 0
    return max(float(price) - float(down), 0.0)


def _property_value(application: dict[str, Any]) -> float | None:
    prop = application.get("property") or {}
    val = prop.get("property_value_or_purchase_price")
    return float(val) if val is not None else None


def compute_monthly_income(application: dict[str, Any], deal_context: dict[str, Any]) -> float | None:
    income = application.get("income") or {}
    app_monthly = _monthly_from_income(income.get("income_amount"), income.get("income_frequency"))
    extracted = _extracted_monthly_income(deal_context)
    if app_monthly is not None and extracted > 0:
        return max(app_monthly, extracted)
    if app_monthly is not None:
        return app_monthly
    if extracted > 0:
        return extracted
    return None


def compute_dti(
    monthly_income: float | None,
    monthly_debts: float,
    housing_payment: float,
) -> float | None:
    if not monthly_income or monthly_income <= 0:
        return None
    return (monthly_debts + housing_payment) / monthly_income


def compute_ltv(loan_amount: float | None, property_value: float | None) -> float | None:
    if loan_amount is None or property_value is None or property_value <= 0:
        return None
    return loan_amount / property_value


def _status_from_metrics(
    dti: float | None,
    ltv: float | None,
    missing_fields: list[str],
    config: RulesConfig,
) -> EligibilityStatus:
    if missing_fields:
        return EligibilityStatus.red

    status = EligibilityStatus.green
    if dti is not None:
        if dti > config.dti_yellow_max:
            return EligibilityStatus.red
        if dti > config.dti_green_max:
            status = EligibilityStatus.yellow
    if ltv is not None:
        if ltv > config.ltv_yellow_max:
            return EligibilityStatus.red
        if ltv > config.ltv_green_max and status != EligibilityStatus.red:
            status = EligibilityStatus.yellow
    if dti is None or ltv is None:
        return EligibilityStatus.yellow
    return status


def build_rule_evaluations(
    dti: float | None,
    ltv: float | None,
    missing_fields: list[str],
    config: RulesConfig,
) -> list[RuleEvaluation]:
    evals: list[RuleEvaluation] = []
    if missing_fields:
        evals.append(
            RuleEvaluation(
                rule_id="required_fields",
                passed=False,
                message=f"Missing required fields: {', '.join(missing_fields)}",
            )
        )
    else:
        evals.append(
            RuleEvaluation(rule_id="required_fields", passed=True, message="Required intake fields present")
        )

    if dti is not None:
        evals.append(
            RuleEvaluation(
                rule_id="dti",
                passed=dti <= config.dti_green_max,
                message=f"DTI {dti:.1%}",
                value=dti,
                threshold=config.dti_green_max,
            )
        )
    else:
        evals.append(RuleEvaluation(rule_id="dti", passed=False, message="DTI could not be computed"))

    if ltv is not None:
        evals.append(
            RuleEvaluation(
                rule_id="ltv",
                passed=ltv <= config.ltv_green_max,
                message=f"LTV {ltv:.1%}",
                value=ltv,
                threshold=config.ltv_green_max,
            )
        )
    else:
        evals.append(RuleEvaluation(rule_id="ltv", passed=False, message="LTV could not be computed"))

    return evals


def build_conditions(
    application: dict[str, Any],
    deal_context: dict[str, Any],
    dti: float | None,
    ltv: float | None,
    missing_fields: list[str],
    document_count: int,
) -> ConditionsList:
    items: list[Condition] = []

    if missing_fields:
        items.append(
            Condition(
                id=str(uuid4()),
                code="missing_intake_fields",
                title="Complete application intake",
                rationale=f"Still missing: {', '.join(missing_fields)}",
            )
        )

    prop_val = _property_value(application)
    if prop_val is None:
        items.append(
            Condition(
                id=str(uuid4()),
                code="missing_property_value",
                title="Confirm property value",
                rationale="Purchase price or property value is required to compute LTV.",
            )
        )

    income_records = (deal_context.get("extracted_income") or {}).get("records") or []
    pay_stub_count = sum(1 for r in income_records if r.get("source_document_id"))
    if pay_stub_count < 2:
        items.append(
            Condition(
                id=str(uuid4()),
                code="single_pay_stub",
                title="Provide a second recent pay stub",
                rationale="Two recent pay stubs help verify stable monthly income.",
                required_doc_type="pay_stub",
            )
        )

    if not income_records:
        items.append(
            Condition(
                id=str(uuid4()),
                code="missing_income_documentation",
                title="Upload income documentation",
                rationale="Upload a pay stub or W-2 so we can verify income.",
                required_doc_type="pay_stub",
            )
        )

    asset_records = (deal_context.get("extracted_assets") or {}).get("records") or []
    for asset in asset_records:
        if asset.get("large_deposit_flag"):
            items.append(
                Condition(
                    id=str(uuid4()),
                    code="large_deposit_unclear",
                    title="Explain large deposit",
                    rationale="A recent large deposit needs a brief explanation or source documentation.",
                    required_doc_type="bank_statement",
                )
            )
            break

    if dti is not None and dti > RulesConfig().dti_green_max:
        items.append(
            Condition(
                id=str(uuid4()),
                code="elevated_dti",
                title="Review debt obligations",
                rationale=f"Estimated DTI is {dti:.1%}; additional income or liability detail may be needed.",
            )
        )

    if ltv is not None and ltv > RulesConfig().ltv_green_max:
        items.append(
            Condition(
                id=str(uuid4()),
                code="elevated_ltv",
                title="Review down payment / loan amount",
                rationale=f"Estimated LTV is {ltv:.1%}; verify down payment and property value.",
            )
        )

    if document_count == 0:
        items.append(
            Condition(
                id=str(uuid4()),
                code="no_documents_uploaded",
                title="Upload supporting documents",
                rationale="Upload pay stubs, W-2, or bank statements to support the application.",
            )
        )

    return ConditionsList(items=items[:5])


def evaluate_eligibility(
    application: dict[str, Any],
    deal_context: dict[str, Any],
    *,
    document_count: int = 0,
    config: RulesConfig | None = None,
) -> tuple[EligibilityResult, ConditionsList]:
    cfg = config or RulesConfig()
    missing = compute_missing_fields(application)
    monthly_income = compute_monthly_income(application, deal_context)
    monthly_debts = _monthly_debts(application)
    housing = _estimate_housing_payment(application, monthly_income)
    loan_amt = _loan_amount(application)
    prop_val = _property_value(application)
    dti = compute_dti(monthly_income, monthly_debts, housing)
    ltv = compute_ltv(loan_amt, prop_val)
    status = _status_from_metrics(dti, ltv, missing, cfg)
    rule_evals = build_rule_evaluations(dti, ltv, missing, cfg)
    conditions = build_conditions(application, deal_context, dti, ltv, missing, document_count)

    result = EligibilityResult(
        status=status,
        dti=dti,
        ltv=ltv,
        monthly_income=monthly_income,
        monthly_debts=monthly_debts,
        estimated_housing_payment=housing,
        loan_amount=loan_amt,
        property_value=prop_val,
        rule_evaluations=rule_evals,
        computed_at=datetime.now(timezone.utc),
    )
    return result, conditions
