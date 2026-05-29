from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.borrower import Borrower
from app.models.deal import Deal, DealStatus
from app.models.deal_context import DealContext
from app.models.loan_application import LoanApplication
from app.schemas.deal import DealCreate, DealPatch


router = APIRouter(prefix="/deals", tags=["deals"])


@router.post("", status_code=status.HTTP_201_CREATED)
def create_deal(
    payload: DealCreate,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    # Minimal creation: create Deal + skeleton LoanApplication + DealContext.
    from app.services.deals_service import create_deal as svc_create_deal

    deal = svc_create_deal(db=db, borrower_id=payload.borrower_id)

    loan_app = db.execute(
        select(LoanApplication).where(LoanApplication.deal_id == deal.id)
    ).scalar_one()
    deal_context = db.execute(
        select(DealContext).where(DealContext.deal_id == deal.id)
    ).scalar_one()

    return {
        "deal": {"id": deal.id, "borrower_id": deal.borrower_id, "status": deal.status.value},
        "loan_application": {"deal_id": loan_app.deal_id, "data": loan_app.data},
        "deal_context": {
            "deal_id": deal_context.deal_id,
            "extracted_income": deal_context.extracted_income,
            "extracted_assets": deal_context.extracted_assets,
            "extracted_liabilities": deal_context.extracted_liabilities,
            "computed_metrics": deal_context.computed_metrics,
            "status_flags": deal_context.status_flags,
            "eligibility": deal_context.eligibility,
            "conditions": deal_context.conditions,
        },
    }


@router.get("")
def list_deals(
    status_filter: Optional[DealStatus] = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    stmt = select(Deal, Borrower).join(Borrower, Borrower.id == Deal.borrower_id)
    if status_filter is not None:
        stmt = stmt.where(Deal.status == status_filter)
    rows = db.execute(stmt.order_by(Deal.updated_at.desc())).all()
    return [
        {
            "id": deal.id,
            "borrower_id": deal.borrower_id,
            "borrower_name": borrower.name,
            "status": deal.status.value,
            "updated_at": deal.updated_at.isoformat() if deal.updated_at else None,
        }
        for deal, borrower in rows
    ]


@router.get("/{deal_id}")
def get_deal(
    deal_id: int,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    from app.services.deals_service import get_deal as svc_get_deal

    deal = svc_get_deal(db=db, deal_id=deal_id)
    if deal is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deal not found")

    loan_app = db.execute(
        select(LoanApplication).where(LoanApplication.deal_id == deal.id)
    ).scalar_one()
    deal_context = db.execute(
        select(DealContext).where(DealContext.deal_id == deal.id)
    ).scalar_one()

    return {
        "deal": {"id": deal.id, "borrower_id": deal.borrower_id, "status": deal.status.value},
        "loan_application": {"deal_id": loan_app.deal_id, "data": loan_app.data},
        "deal_context": {
            "deal_id": deal_context.deal_id,
            "extracted_income": deal_context.extracted_income,
            "extracted_assets": deal_context.extracted_assets,
            "extracted_liabilities": deal_context.extracted_liabilities,
            "computed_metrics": deal_context.computed_metrics,
            "status_flags": deal_context.status_flags,
            "eligibility": deal_context.eligibility,
            "conditions": deal_context.conditions,
        },
    }


@router.patch("/{deal_id}")
def patch_deal_status(
    deal_id: int,
    payload: DealPatch,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    from app.services.deals_service import transition_status

    try:
        deal = transition_status(db=db, deal_id=deal_id, next_status=payload.status)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deal not found")

    return {"deal_id": deal.id, "status": deal.status.value}

