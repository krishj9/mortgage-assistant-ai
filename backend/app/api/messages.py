from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.schemas.eligibility import MessageApprovalIn, MessagesUpdate
from app.services import messages_service


router = APIRouter(prefix="/deals", tags=["messages"])


@router.get("/{deal_id}/messages")
def get_deal_messages(
    deal_id: int,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    return messages_service.get_messages_for_staff(db, deal_id=deal_id)


@router.put("/{deal_id}/messages")
def update_deal_messages(
    deal_id: int,
    payload: MessagesUpdate,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    return messages_service.update_message_drafts(db, deal_id=deal_id, payload=payload)


@router.post("/{deal_id}/messages/approve")
def approve_deal_messages(
    deal_id: int,
    payload: MessageApprovalIn,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    try:
        return messages_service.approve_message_channel(
            db,
            deal_id=deal_id,
            user_id=int(user["user_id"]),
            payload=payload,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
