from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.borrower import Borrower
from app.models.deal import Deal, DealStatus
from app.models.deal_context import DealContext
from app.models.loan_application import LoanApplication
from app.models.message import Messages
from app.models.user import User


def _full_application() -> dict:
    return {
        "identity": {"borrower_name": "Eligibility Test"},
        "contact": {"contact_email": "elig@example.com"},
        "employment": {"employment_status": "employed"},
        "income": {"income_amount": 8000, "income_frequency": "monthly"},
        "liabilities": {"monthly_debts": [{"monthly_payment": 500}]},
        "property": {
            "property_status": "shopping",
            "property_value_or_purchase_price": 500000,
            "estimated_housing_payment": 1800,
        },
        "loan_purpose": {"loan_purpose": "purchase", "desired_down_payment": 100000},
    }


def _seed_ready_deal(db):
    unique = uuid.uuid4().hex[:8]
    staff = db.execute(select(User).where(User.email == "lo@example.com")).scalar_one_or_none()
    if staff is None:
        staff = User(email="lo@example.com", hashed_password=hash_password("password"), is_active=True)
        db.add(staff)
        db.flush()

    borrower = Borrower(
        name="Eligibility Borrower",
        dob_placeholder="0000-00-00",
        contact_email=f"elig_{unique}@example.com",
        contact_phone=None,
        is_active=True,
    )
    db.add(borrower)
    db.flush()
    deal = Deal(borrower_id=borrower.id, status=DealStatus.docs_pending)
    db.add(deal)
    db.flush()
    db.add(LoanApplication(deal_id=deal.id, data=_full_application()))
    db.add(
        DealContext(
            deal_id=deal.id,
            extracted_income={
                "records": [
                    {"gross_income": 8000, "pay_frequency": "monthly", "source_document_id": 1},
                    {"gross_income": 8000, "pay_frequency": "monthly", "source_document_id": 2},
                ]
            },
            extracted_assets={"records": []},
            extracted_liabilities={},
        )
    )
    db.add(
        Messages(
            deal_id=deal.id,
            internal_notes="",
            borrower_message="",
            internal_draft="",
            borrower_draft="",
        )
    )
    db.commit()
    return staff.id, deal.id


@pytest.mark.asyncio
async def test_eligibility_run_persists_results(async_client: AsyncClient):
    db = SessionLocal()
    try:
        _, deal_id = _seed_ready_deal(db)
    finally:
        db.close()

    login = await async_client.post(
        "/auth/staff/login",
        json={"email": "lo@example.com", "password": "password"},
    )
    token = login.json()["access_token"]

    run = await async_client.post(
        f"/deals/{deal_id}/eligibility/run",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert run.status_code == 200
    body = run.json()
    assert body["eligibility"]["dti"] is not None
    assert body["eligibility"]["ltv"] is not None
    assert len(body["conditions"]["items"]) >= 1
    assert body["messages"]["internal_draft"]
    assert body["messages"]["borrower_draft"]
    assert body["deal_status"] == "ready_for_review"

    get_resp = await async_client.get(
        f"/deals/{deal_id}/eligibility",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert get_resp.status_code == 200

    db = SessionLocal()
    try:
        deal = db.execute(select(Deal).where(Deal.id == deal_id)).scalar_one()
        assert deal.status == DealStatus.ready_for_review
    finally:
        db.close()
