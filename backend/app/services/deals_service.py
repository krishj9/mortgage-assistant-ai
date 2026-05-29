from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.deal import Deal, DealStatus
from app.models.deal_context import DealContext
from app.models.loan_application import LoanApplication
from app.models.message import Messages


def create_deal(db: Session, borrower_id: int) -> Deal:
    deal = Deal(borrower_id=borrower_id, status=DealStatus.intake_in_progress)
    db.add(deal)
    db.flush()  # get deal.id

    db.add(LoanApplication(deal_id=deal.id, data={}))
    db.add(DealContext(deal_id=deal.id, extracted_income={}, extracted_assets={}, extracted_liabilities={}))
    db.add(
        Messages(
            deal_id=deal.id,
            internal_notes="",
            borrower_message="",
            internal_draft="",
            borrower_draft="",
            internal_approved=False,
            borrower_approved=False,
        )
    )

    db.commit()
    db.refresh(deal)
    return deal


def get_deal(db: Session, deal_id: int) -> Optional[Deal]:
    return db.execute(select(Deal).where(Deal.id == deal_id)).scalar_one_or_none()


def list_deals(db: Session, filter_by_status: Optional[DealStatus] = None) -> list[Deal]:
    stmt = select(Deal)
    if filter_by_status is not None:
        stmt = stmt.where(Deal.status == filter_by_status)
    return list(db.execute(stmt).scalars().all())


def transition_status(db: Session, deal_id: int, next_status: DealStatus) -> Deal:
    deal = get_deal(db, deal_id)
    if deal is None:
        raise ValueError("Deal not found")
    deal.status = next_status
    db.commit()
    db.refresh(deal)
    return deal

