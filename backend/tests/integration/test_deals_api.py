from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.core.security import hash_password, sign_borrower_session
from app.db.session import SessionLocal
from app.models.borrower import Borrower
from app.models.deal import Deal, DealStatus
from app.models.user import User


def _ensure_staff_user(db) -> User:
    user = db.execute(select(User).where(User.email == "lo@example.com")).scalar_one_or_none()
    if user is None:
        user = User(
            email="lo@example.com",
            hashed_password=hash_password("password"),
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


def _get_or_create_borrower(db, name: str, email: str) -> Borrower:
    borrower = db.execute(select(Borrower).where(Borrower.contact_email == email)).scalar_one_or_none()
    if borrower is None:
        borrower = Borrower(name=name, dob_placeholder="0000-00-00", contact_email=email, contact_phone=None)
        db.add(borrower)
        db.commit()
        db.refresh(borrower)
    return borrower


@pytest.mark.asyncio
async def test_deals_crud_and_staff_auth(async_client: AsyncClient):
    db = SessionLocal()
    try:
        staff = _ensure_staff_user(db)
        borrower = _get_or_create_borrower(db, "Test Borrower", "test_borrower@example.com")

        # login
        login_resp = await async_client.post(
            "/auth/staff/login",
            json={"email": "lo@example.com", "password": "password"},
        )
        assert login_resp.status_code == 200
        token = login_resp.json()["access_token"]

        # create deal
        create_resp = await async_client.post(
            "/deals",
            json={"borrower_id": borrower.id},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert create_resp.status_code == 201
        deal_payload = create_resp.json()
        deal_id = deal_payload["deal"]["id"]

        # list deals
        list_resp = await async_client.get(
            "/deals",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert list_resp.status_code == 200
        assert any(d["id"] == deal_id for d in list_resp.json())

        # get deal detail
        get_resp = await async_client.get(
            f"/deals/{deal_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert get_resp.status_code == 200
        assert get_resp.json()["deal"]["id"] == deal_id
    finally:
        db.close()


@pytest.mark.asyncio
async def test_borrower_token_cannot_list_deals(async_client: AsyncClient):
    db = SessionLocal()
    try:
        borrower = _get_or_create_borrower(db, "Scoped Borrower", "scoped_borrower@example.com")

        # Ensure the borrower has at least one deal to sign a token for.
        deal = db.execute(select(Deal).where(Deal.borrower_id == borrower.id)).scalars().first()
        if deal is None:
            deal = Deal(borrower_id=borrower.id, status=DealStatus.intake_in_progress)
            db.add(deal)
            db.flush()
            # minimal skeletons
            from app.models.deal_context import DealContext
            from app.models.loan_application import LoanApplication
            from app.models.message import Messages

            db.add(LoanApplication(deal_id=deal.id, data={}))
            db.add(DealContext(deal_id=deal.id, extracted_income={}, extracted_assets={}, extracted_liabilities={}))
            db.add(
                Messages(
                    deal_id=deal.id,
                    internal_notes="",
                    borrower_message="",
                    internal_approved=False,
                    borrower_approved=False,
                )
            )
            db.commit()
            db.refresh(deal)

        borrower_token = sign_borrower_session(deal_id=deal.id, borrower_id=borrower.id)

        resp = await async_client.get(
            "/deals",
            headers={"Authorization": f"Bearer {borrower_token}"},
        )
        # OAuth2 verification fails because token type != staff.
        assert resp.status_code in (401, 403)
    finally:
        db.close()

