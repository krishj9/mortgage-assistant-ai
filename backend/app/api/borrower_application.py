from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_borrower_session, get_db
from app.models.loan_application import LoanApplication
from app.services.approval_service import get_approved_borrower_message


router = APIRouter(prefix="/borrower", tags=["borrower"])


@router.get("/application")
def get_borrower_application(
    db: Session = Depends(get_db),
    borrower_session: dict = Depends(get_borrower_session),
):
    deal_id = int(borrower_session["deal_id"])
    loan_app = db.execute(select(LoanApplication).where(LoanApplication.deal_id == deal_id)).scalar_one()
    approved_message = get_approved_borrower_message(db, deal_id=deal_id)
    return {
        "deal_id": deal_id,
        "application": loan_app.data or {},
        "approved_borrower_message": approved_message,
    }
