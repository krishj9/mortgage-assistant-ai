from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents.nodes.eligibility_agent import run_eligibility_agent
from app.agents.nodes.messaging_agent import run_messaging_agent
from app.models.deal import DealStatus
from app.models.deal_context import DealContext
from app.models.loan_application import LoanApplication
from app.models.message import Messages
from app.schemas.eligibility import ConditionsList, EligibilityPatch, EligibilityResult
from app.services.deals_service import transition_status


def _sync_computed_metrics(ctx: DealContext, eligibility: EligibilityResult) -> None:
    ctx.computed_metrics = {
        "dti": eligibility.dti,
        "ltv": eligibility.ltv,
        "monthly_income": eligibility.monthly_income,
        "loan_amount": eligibility.loan_amount,
        "property_value": eligibility.property_value,
    }
    ctx.status_flags = {"eligibility_status": eligibility.status.value}


def get_deal_context(db: Session, deal_id: int) -> DealContext:
    return db.execute(select(DealContext).where(DealContext.deal_id == deal_id)).scalar_one()


def get_eligibility(db: Session, deal_id: int) -> tuple[EligibilityResult | None, ConditionsList]:
    ctx = get_deal_context(db, deal_id)
    if not ctx.eligibility:
        return None, ConditionsList.model_validate(ctx.conditions or {"items": []})
    return EligibilityResult.model_validate(ctx.eligibility), ConditionsList.model_validate(
        ctx.conditions or {"items": []}
    )


def persist_eligibility(
    db: Session,
    deal_id: int,
    eligibility: EligibilityResult,
    conditions: ConditionsList,
) -> None:
    ctx = get_deal_context(db, deal_id)
    ctx.eligibility = eligibility.model_dump(mode="json")
    ctx.conditions = conditions.model_dump(mode="json")
    _sync_computed_metrics(ctx, eligibility)
    db.commit()


def run_eligibility_flow(db: Session, deal_id: int) -> dict:
    eligibility, conditions = run_eligibility_agent(db, deal_id)
    persist_eligibility(db, deal_id, eligibility, conditions)

    loan_app = db.execute(select(LoanApplication).where(LoanApplication.deal_id == deal_id)).scalar_one()
    internal_draft, borrower_draft = run_messaging_agent(loan_app.data or {}, eligibility, conditions)

    messages = db.execute(select(Messages).where(Messages.deal_id == deal_id)).scalar_one()
    messages.internal_draft = internal_draft
    messages.borrower_draft = borrower_draft
    messages.internal_notes = internal_draft
    messages.borrower_message = borrower_draft
    messages.internal_approved = False
    messages.borrower_approved = False
    messages.approved_by_user_id = None
    messages.approved_at = None
    db.commit()

    transition_status(db, deal_id=deal_id, next_status=DealStatus.ready_for_review)

    return {
        "eligibility": eligibility.model_dump(mode="json"),
        "conditions": conditions.model_dump(mode="json"),
        "messages": {
            "internal_draft": internal_draft,
            "borrower_draft": borrower_draft,
            "internal_approved": False,
            "borrower_approved": False,
        },
        "deal_status": DealStatus.ready_for_review.value,
    }


def patch_eligibility(db: Session, deal_id: int, patch: EligibilityPatch) -> tuple[EligibilityResult, ConditionsList]:
    ctx = get_deal_context(db, deal_id)
    current = EligibilityResult.model_validate(ctx.eligibility) if ctx.eligibility else None
    if current is None:
        raise ValueError("Eligibility has not been computed yet")

    if patch.status is not None:
        current.lo_status_override = patch.status
        current.status = patch.status

    conditions = ConditionsList.model_validate(ctx.conditions or {"items": []})
    if patch.conditions is not None:
        conditions = patch.conditions

    persist_eligibility(db, deal_id, current, conditions)
    return current, conditions


def approve_eligibility(db: Session, deal_id: int) -> EligibilityResult:
    ctx = get_deal_context(db, deal_id)
    if not ctx.eligibility:
        raise ValueError("Eligibility has not been computed yet")
    current = EligibilityResult.model_validate(ctx.eligibility)
    current.eligibility_approved = True
    persist_eligibility(db, deal_id, current, ConditionsList.model_validate(ctx.conditions or {"items": []}))
    return current
