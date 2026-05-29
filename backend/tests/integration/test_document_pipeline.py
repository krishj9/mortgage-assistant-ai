from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.core.security import sign_borrower_session
from app.db.session import SessionLocal
from app.models.borrower import Borrower
from app.models.deal import Deal, DealStatus
from app.models.deal_context import DealContext
from app.models.document import Document
from app.models.document_extraction import DocumentExtraction
from app.models.loan_application import LoanApplication
from app.models.message import Messages
from app.services.ocr.base import OcrResult
from app.workers.document_pipeline import run_document_pipeline


def _seed_deal(db):
    unique = uuid.uuid4().hex[:8]
    borrower = Borrower(
        name="Doc Borrower",
        dob_placeholder="0000-00-00",
        contact_email=f"doc_{unique}@example.com",
        contact_phone=None,
        is_active=True,
    )
    db.add(borrower)
    db.flush()
    deal = Deal(borrower_id=borrower.id, status=DealStatus.docs_pending)
    db.add(deal)
    db.flush()
    db.add(LoanApplication(deal_id=deal.id, data={}))
    db.add(DealContext(deal_id=deal.id, extracted_income={}, extracted_assets={}, extracted_liabilities={}))
    db.add(Messages(deal_id=deal.id, internal_notes="", borrower_message="", internal_approved=False, borrower_approved=False))
    db.commit()
    return borrower.id, deal.id


@pytest.mark.asyncio
async def test_document_upload_and_pipeline(async_client: AsyncClient, monkeypatch):
    db = SessionLocal()
    try:
        borrower_id, deal_id = _seed_deal(db)
        token = sign_borrower_session(deal_id=deal_id, borrower_id=borrower_id)
    finally:
        db.close()

    def _fake_understanding(document_bytes, filename, document_id, doc_type_hint=None):
        ocr = OcrResult(text="Gross Pay: 5000", key_values={"Employer": "Acme"})
        normalized = {
            "income": [
                {
                    "gross_income": 5000.0,
                    "pay_frequency": "monthly",
                    "employer": "Acme",
                    "source_document_id": document_id,
                }
            ]
        }
        return "pay_stub", 0.9, ocr, normalized, {"income": 0.9}

    monkeypatch.setattr(
        "app.workers.document_pipeline.run_document_understanding",
        _fake_understanding,
    )

    files = {"file": ("pay_stub.txt", b"Employer: Acme\nGross Pay: 5000", "text/plain")}
    upload = await async_client.post(
        "/documents",
        files=files,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert upload.status_code == 201
    document_id = upload.json()["id"]

    run_document_pipeline(document_id)

    db = SessionLocal()
    try:
        doc = db.execute(select(Document).where(Document.id == document_id)).scalar_one()
        assert doc.extraction_status == "succeeded"
        extraction = db.execute(
            select(DocumentExtraction).where(DocumentExtraction.document_id == document_id)
        ).scalar_one()
        assert extraction.normalized.get("income")
        ctx = db.execute(select(DealContext).where(DealContext.deal_id == deal_id)).scalar_one()
        assert ctx.extracted_income.get("records")
    finally:
        db.close()
