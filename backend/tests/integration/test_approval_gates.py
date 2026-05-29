from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.core.security import hash_password, sign_borrower_session
from app.db.session import SessionLocal
from app.models.borrower import Borrower
from app.models.deal import Deal, DealStatus
from app.models.deal_context import DealContext
from app.models.loan_application import LoanApplication
from app.models.message import Messages
from app.models.user import User


def _seed_deal_with_messages(db, *, borrower_approved: bool):
    unique = uuid.uuid4().hex[:8]
    borrower = Borrower(
        name="Approval Borrower",
        dob_placeholder="0000-00-00",
        contact_email=f"appr_{unique}@example.com",
        contact_phone=None,
        is_active=True,
    )
    db.add(borrower)
    db.flush()
    deal = Deal(borrower_id=borrower.id, status=DealStatus.ready_for_review)
    db.add(deal)
    db.flush()
    db.add(LoanApplication(deal_id=deal.id, data={"identity": {"borrower_name": "Approval Borrower"}}))
    db.add(DealContext(deal_id=deal.id, extracted_income={}, extracted_assets={}, extracted_liabilities={}))
    db.add(
        Messages(
            deal_id=deal.id,
            internal_draft="Internal only",
            borrower_draft="Borrower visible after approval",
            internal_notes="Internal only",
            borrower_message="Borrower visible after approval",
            borrower_approved=borrower_approved,
        )
    )
    db.commit()
    return borrower.id, deal.id


@pytest.mark.asyncio
async def test_borrower_application_hides_message_until_approved(async_client: AsyncClient):
    db = SessionLocal()
    try:
        borrower_id, deal_id = _seed_deal_with_messages(db, borrower_approved=False)
        token = sign_borrower_session(deal_id=deal_id, borrower_id=borrower_id)
    finally:
        db.close()

    resp = await async_client.get(
        "/borrower/application",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["approved_borrower_message"] is None


@pytest.mark.asyncio
async def test_borrower_application_shows_approved_message(async_client: AsyncClient):
    db = SessionLocal()
    try:
        borrower_id, deal_id = _seed_deal_with_messages(db, borrower_approved=True)
        token = sign_borrower_session(deal_id=deal_id, borrower_id=borrower_id)
    finally:
        db.close()

    resp = await async_client.get(
        "/borrower/application",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert "Borrower visible" in resp.json()["approved_borrower_message"]


@pytest.mark.asyncio
async def test_staff_message_approval_flow(async_client: AsyncClient):
    db = SessionLocal()
    try:
        staff = User(email="lo@example.com", hashed_password=hash_password("password"), is_active=True)
        existing = db.execute(select(User).where(User.email == "lo@example.com")).scalar_one_or_none()
        if existing is None:
            db.add(staff)
            db.commit()
        _, deal_id = _seed_deal_with_messages(db, borrower_approved=False)
    finally:
        db.close()

    login = await async_client.post(
        "/auth/staff/login",
        json={"email": "lo@example.com", "password": "password"},
    )
    token = login.json()["access_token"]

    approve = await async_client.post(
        f"/deals/{deal_id}/messages/approve",
        json={"channel": "borrower", "approved": True},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert approve.status_code == 200
    assert approve.json()["borrower_approved"] is True
