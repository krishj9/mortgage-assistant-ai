from __future__ import annotations

import json

from langchain_core.messages import HumanMessage, SystemMessage
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.agents.prompts.eligibility import ELIGIBILITY_SYSTEM_PROMPT
from app.agents.tools.rules import evaluate_eligibility
from app.models.deal_context import DealContext
from app.models.document import Document
from app.models.loan_application import LoanApplication
from app.schemas.agent_io import ConditionRefinement
from app.schemas.eligibility import ConditionsList, EligibilityResult
from app.services.bedrock.client import get_structured_model, invoke_structured


def _refine_conditions_with_llm(
    eligibility: EligibilityResult,
    conditions: ConditionsList,
    *,
    deal_id: int | None = None,
) -> ConditionsList:
    """
    Let the LLM polish condition titles/rationales only. Deterministic status, DTI,
    LTV, and the set of conditions (keyed by id) are authoritative and never changed.
    """
    if not conditions.items:
        return conditions
    try:
        model = get_structured_model(ConditionRefinement, tags=["eligibility"])
        payload = {
            "status": eligibility.status.value,
            "dti": eligibility.dti,
            "ltv": eligibility.ltv,
            "conditions": [c.model_dump() for c in conditions.items],
        }
        result = invoke_structured(
            model,
            [
                SystemMessage(content=ELIGIBILITY_SYSTEM_PROMPT),
                HumanMessage(content=json.dumps(payload)),
            ],
            tags=["eligibility"],
            metadata={"deal_id": str(deal_id)} if deal_id else None,
        )
        if not isinstance(result, ConditionRefinement):
            return conditions
        refined_by_id = {item.id: item for item in result.items}
        merged = []
        for original in conditions.items:
            refined = refined_by_id.get(original.id)
            if refined is None:
                merged.append(original)
                continue
            # Keep authoritative fields; accept only title/rationale refinements.
            merged.append(
                original.model_copy(
                    update={
                        "title": refined.title or original.title,
                        "rationale": refined.rationale or original.rationale,
                    }
                )
            )
        return ConditionsList(items=merged)
    except Exception:
        return conditions


def run_eligibility_agent(db: Session, deal_id: int) -> tuple[EligibilityResult, ConditionsList]:
    loan_app = db.execute(select(LoanApplication).where(LoanApplication.deal_id == deal_id)).scalar_one()
    ctx = db.execute(select(DealContext).where(DealContext.deal_id == deal_id)).scalar_one()
    doc_count = db.execute(
        select(func.count()).select_from(Document).where(Document.deal_id == deal_id)
    ).scalar_one()

    deal_context_snapshot = {
        "extracted_income": ctx.extracted_income or {},
        "extracted_assets": ctx.extracted_assets or {},
        "extracted_liabilities": ctx.extracted_liabilities or {},
    }
    eligibility, conditions = evaluate_eligibility(
        loan_app.data or {},
        deal_context_snapshot,
        document_count=int(doc_count or 0),
    )
    conditions = _refine_conditions_with_llm(eligibility, conditions, deal_id=deal_id)
    return eligibility, conditions
