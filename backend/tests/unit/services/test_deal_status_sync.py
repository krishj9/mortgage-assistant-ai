from __future__ import annotations

import uuid

from app.db.session import SessionLocal
from app.models.borrower import Borrower
from app.models.deal import Deal, DealStatus
from app.models.deal_context import DealContext
from app.models.document import Document, ExtractionStatus
from app.models.loan_application import LoanApplication
from app.models.message import Messages
from app.services.deals_service import sync_deal_status_from_documents


def _seed_deal(db, *, status: DealStatus = DealStatus.docs_pending) -> int:
    unique = uuid.uuid4().hex[:8]
    borrower = Borrower(
        name="Status Borrower",
        dob_placeholder="0000-00-00",
        contact_email=f"status_{unique}@example.com",
        contact_phone=None,
        is_active=True,
    )
    db.add(borrower)
    db.flush()
    deal = Deal(borrower_id=borrower.id, status=status)
    db.add(deal)
    db.flush()
    db.add(LoanApplication(deal_id=deal.id, data={}))
    db.add(DealContext(deal_id=deal.id, extracted_income={}, extracted_assets={}, extracted_liabilities={}))
    db.add(Messages(deal_id=deal.id, internal_notes="", borrower_message="", internal_approved=False, borrower_approved=False))
    db.commit()
    return deal.id


def test_sync_moves_to_extraction_in_progress_when_doc_pending():
    db = SessionLocal()
    try:
        deal_id = _seed_deal(db)
        db.add(
            Document(
                deal_id=deal_id,
                storage_uri="local://x",
                original_filename="pay_stub.pdf",
                mime_type="application/pdf",
                extraction_status=ExtractionStatus.pending.value,
            )
        )
        db.commit()

        sync_deal_status_from_documents(db, deal_id)
        deal = db.get(Deal, deal_id)
        assert deal.status == DealStatus.extraction_in_progress
    finally:
        db.close()


def test_sync_moves_to_ready_for_review_when_doc_succeeded():
    db = SessionLocal()
    try:
        deal_id = _seed_deal(db)
        db.add(
            Document(
                deal_id=deal_id,
                storage_uri="local://x",
                original_filename="w2.pdf",
                mime_type="application/pdf",
                predicted_type="w2",
                extraction_status=ExtractionStatus.succeeded.value,
            )
        )
        db.commit()

        sync_deal_status_from_documents(db, deal_id)
        deal = db.get(Deal, deal_id)
        assert deal.status == DealStatus.ready_for_review
    finally:
        db.close()


def test_sync_keeps_docs_pending_when_all_docs_failed():
    db = SessionLocal()
    try:
        deal_id = _seed_deal(db)
        db.add(
            Document(
                deal_id=deal_id,
                storage_uri="local://x",
                original_filename="bad.pdf",
                mime_type="application/pdf",
                extraction_status=ExtractionStatus.failed.value,
            )
        )
        db.commit()

        sync_deal_status_from_documents(db, deal_id)
        deal = db.get(Deal, deal_id)
        assert deal.status == DealStatus.docs_pending
    finally:
        db.close()
