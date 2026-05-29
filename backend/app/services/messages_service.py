from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.message import Messages
from app.schemas.eligibility import MessageApprovalIn, MessagesUpdate


def get_messages_row(db: Session, deal_id: int) -> Messages:
    return db.execute(select(Messages).where(Messages.deal_id == deal_id)).scalar_one()


def get_messages_for_staff(db: Session, deal_id: int) -> dict:
    row = get_messages_row(db, deal_id)
    return {
        "deal_id": deal_id,
        "internal_draft": row.internal_draft,
        "borrower_draft": row.borrower_draft,
        "internal_approved": row.internal_approved,
        "borrower_approved": row.borrower_approved,
        "approved_by_user_id": row.approved_by_user_id,
        "approved_at": row.approved_at.isoformat() if row.approved_at else None,
    }


def update_message_drafts(db: Session, deal_id: int, payload: MessagesUpdate) -> dict:
    row = get_messages_row(db, deal_id)
    if payload.internal_draft is not None:
        row.internal_draft = payload.internal_draft
        row.internal_notes = payload.internal_draft
    if payload.borrower_draft is not None:
        row.borrower_draft = payload.borrower_draft
        row.borrower_message = payload.borrower_draft
    db.commit()
    return get_messages_for_staff(db, deal_id)


def approve_message_channel(
    db: Session,
    deal_id: int,
    user_id: int,
    payload: MessageApprovalIn,
) -> dict:
    row = get_messages_row(db, deal_id)
    if payload.channel == "internal":
        if not row.internal_draft.strip():
            raise ValueError("Internal draft is empty")
        row.internal_approved = payload.approved
    elif payload.channel == "borrower":
        if not row.borrower_draft.strip():
            raise ValueError("Borrower draft is empty")
        row.borrower_approved = payload.approved
    else:
        raise ValueError("Invalid channel")

    if payload.approved:
        row.approved_by_user_id = user_id
        row.approved_at = datetime.now(timezone.utc)
    db.commit()
    return get_messages_for_staff(db, deal_id)
