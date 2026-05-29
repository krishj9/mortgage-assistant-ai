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
from app.models.document import Document
from app.models.document_extraction import DocumentExtraction
from app.models.loan_application import LoanApplication
from app.models.message import Messages
from app.models.user import User


def _seed(db):
    unique = uuid.uuid4().hex[:8]
    staff = db.execute(select(User).where(User.email == "lo@example.com")).scalar_one_or_none()
    if staff is None:
        staff = User(email="lo@example.com", hashed_password=hash_password("password"), is_active=True)
        db.add(staff)
        db.commit()

    borrower = Borrower(
        name="Corr Borrower",
        dob_placeholder="0000-00-00",
        contact_email=f"corr_{unique}@example.com",
        contact_phone=None,
        is_active=True,
    )
    db.add(borrower)
    db.flush()
    deal = Deal(borrower_id=borrower.id, status=DealStatus.docs_pending)
    db.add(deal)
    db.flush()
    db.add(LoanApplication(deal_id=deal.id, data={}))
    db.add(DealContext(deal_id=deal.id, extracted_income={"records": []}, extracted_assets={"records": []}, extracted_liabilities={}))
    db.add(Messages(deal_id=deal.id, internal_notes="", borrower_message="", internal_approved=False, borrower_approved=False))
    doc = Document(
        deal_id=deal.id,
        storage_uri="local://deals/1/sample.txt",
        original_filename="sample.txt",
        mime_type="text/plain",
        predicted_type="pay_stub",
        classification_confidence=0.9,
        extraction_status="succeeded",
    )
    db.add(doc)
    db.flush()
    db.add(
        DocumentExtraction(
            document_id=doc.id,
            raw_ocr={},
            normalized={"income": {"records": [{"gross_income": 1000}]}},
            confidence={},
            human_corrections={},
            status="succeeded",
        )
    )
    db.commit()
    return deal.id, doc.id


@pytest.mark.asyncio
async def test_extraction_correction_updates_deal_context(async_client: AsyncClient):
    db = SessionLocal()
    try:
        deal_id, document_id = _seed(db)
    finally:
        db.close()

    login = await async_client.post(
        "/auth/staff/login",
        json={"email": "lo@example.com", "password": "password"},
    )
    token = login.json()["access_token"]

    patch = {
        "human_corrections": {
            "income": {"records": [{"gross_income": 5500, "employer": "Corrected Inc"}]}
        }
    }
    resp = await async_client.put(
        f"/documents/{document_id}/extraction",
        json=patch,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200

    db = SessionLocal()
    try:
        ctx = db.execute(select(DealContext).where(DealContext.deal_id == deal_id)).scalar_one()
        assert ctx.extracted_income["records"][0]["gross_income"] == 5500
    finally:
        db.close()
