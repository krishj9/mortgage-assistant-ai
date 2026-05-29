from __future__ import annotations

from sqlalchemy.orm import Session

from app.services.messages_service import get_messages_row


def borrower_may_view_message(db: Session, deal_id: int) -> bool:
    row = get_messages_row(db, deal_id)
    return bool(row.borrower_approved)


def get_approved_borrower_message(db: Session, deal_id: int) -> str | None:
    row = get_messages_row(db, deal_id)
    if not row.borrower_approved:
        return None
    text = (row.borrower_draft or row.borrower_message or "").strip()
    return text or None
