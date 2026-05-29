from __future__ import annotations

import uuid

from app.agents.tools.application_writer import apply_application_patch
from app.db.session import SessionLocal
from app.models.borrower import Borrower
from app.models.deal import Deal, DealStatus
from app.models.deal_context import DealContext
from app.models.loan_application import LoanApplication
from app.models.message import Messages


def _create_deal(db):
    unique = uuid.uuid4().hex[:8]
    borrower = Borrower(
        name="Patch Test Borrower",
        dob_placeholder="0000-00-00",
        contact_email=f"patch_test_{unique}@example.com",
        contact_phone=None,
        is_active=True,
    )
    db.add(borrower)
    db.flush()

    deal = Deal(borrower_id=borrower.id, status=DealStatus.intake_in_progress)
    db.add(deal)
    db.flush()

    db.add(LoanApplication(deal_id=deal.id, data={}))
    db.add(DealContext(deal_id=deal.id, extracted_income={}, extracted_assets={}, extracted_liabilities={}))
    db.add(Messages(deal_id=deal.id, internal_notes="", borrower_message="", internal_approved=False, borrower_approved=False))
    db.commit()
    return deal.id


def test_apply_patch_and_compute_missing_fields():
    db = SessionLocal()
    try:
        deal_id = _create_deal(db)

        snapshot, missing = apply_application_patch(
            db,
            deal_id=deal_id,
            patch={
                "identity": {"borrower_name": "Jane Borrower"},
                "contact": {"contact_email": "jane@example.com"},
                "employment": {"employment_status": "employed"},
                "income": {"income_amount": 7500, "income_frequency": "monthly"},
                "property": {"property_status": "shopping", "property_value_or_purchase_price": 500000},
                "loan_purpose": {"loan_purpose": "purchase"},
            },
        )
        assert snapshot["identity"]["borrower_name"] == "Jane Borrower"
        assert "Loan purpose" not in missing
        assert len(missing) == 0
    finally:
        db.close()

