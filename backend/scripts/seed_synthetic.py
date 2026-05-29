from __future__ import annotations

import os

from sqlalchemy import select

from app.core.config import settings
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.borrower import Borrower
from app.models.deal import Deal, DealStatus
from app.models.deal_context import DealContext
from app.models.loan_application import LoanApplication
from app.models.message import Messages
from app.models.user import User


def main() -> None:
    seed_staff_password = os.environ.get("SEED_STAFF_PASSWORD", "password")
    db = SessionLocal()
    try:
        staff = db.execute(select(User).where(User.email == "lo@example.com")).scalar_one_or_none()
        if staff is None:
            staff = User(
                email="lo@example.com",
                hashed_password=hash_password(seed_staff_password),
                is_active=True,
            )
            db.add(staff)
            db.commit()
            db.refresh(staff)

        borrowers = [
            ("Alice Borrower", "alice@example.com"),
            ("Bob Borrower", "bob@example.com"),
            ("Carol Borrower", "carol@example.com"),
        ]

        for name, email in borrowers:
            b = db.execute(select(Borrower).where(Borrower.contact_email == email)).scalar_one_or_none()
            if b is None:
                b = Borrower(
                    name=name,
                    dob_placeholder="0000-00-00",
                    contact_email=email,
                    contact_phone=None,
                    is_active=True,
                )
                db.add(b)
                db.commit()
                db.refresh(b)

            # Create an empty deal + skeletons if the borrower has no deals yet.
            existing_deal = db.execute(select(Deal).where(Deal.borrower_id == b.id).limit(1)).scalar_one_or_none()
            if existing_deal is None:
                deal = Deal(borrower_id=b.id, status=DealStatus.intake_in_progress)
                db.add(deal)
                db.flush()

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

        print("Seed completed.")
        print("Staff credentials: lo@example.com / (SEED_STAFF_PASSWORD or 'password').")
        print("Database URL:", settings.DATABASE_URL)
    finally:
        db.close()


if __name__ == "__main__":
    main()

