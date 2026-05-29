from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.config import settings
from app.core.security import create_access_token, sign_borrower_session, verify_password
from app.models.borrower import Borrower
from app.models.deal import Deal
from app.models.user import User
from app.schemas.auth import BorrowerSessionRequest, StaffLoginRequest, TokenResponse


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/staff/login", response_model=TokenResponse)
def staff_login(
    payload: StaffLoginRequest, db: Session = Depends(get_db)
) -> TokenResponse:
    stmt = select(User).where(User.email == payload.email)
    user = db.execute(stmt).scalar_one_or_none()
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User disabled")

    token = create_access_token(
        subject=str(user.id),
        token_type="staff",
        expires_in_seconds=settings.STAFF_TOKEN_EXPIRE_SECONDS,
    )
    return TokenResponse(access_token=token)


@router.post("/borrower/session")
def create_borrower_session(
    payload: BorrowerSessionRequest, db: Session = Depends(get_db)
):
    stmt = (
        select(Deal, Borrower)
        .join(Borrower, Borrower.id == Deal.borrower_id)
        .where(Deal.id == payload.deal_id)
        .where(Borrower.contact_email == payload.borrower_email)
    )
    row = db.execute(stmt).first()
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Deal not found for borrower email"
        )
    deal, borrower = row

    token = sign_borrower_session(deal_id=int(deal.id), borrower_id=int(borrower.id))
    return {"access_token": token, "token_type": "bearer", "deal_id": int(deal.id)}

