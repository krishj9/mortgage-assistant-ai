from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents.orchestrator import run_intake_turn
from app.agents.tools.application_writer import REQUIRED_FIELDS, compute_captured_fields
from app.api.deps import get_borrower_session, get_db
from app.models.chat import ChatRole, ChatTurn
from app.schemas.chat import BorrowerChatMessageIn, BorrowerChatMessageOut


router = APIRouter(prefix="/borrower/chat", tags=["borrower_chat"])


def _build_progress(snapshot: dict, missing_fields: list[str]) -> dict:
    captured = compute_captured_fields(snapshot)
    total_required = len(REQUIRED_FIELDS)
    return {
        "captured_fields": captured,
        "current_field": missing_fields[0] if missing_fields else None,
        "completed": total_required - len(missing_fields),
        "total_required": total_required,
    }


@router.post("/messages", response_model=BorrowerChatMessageOut)
def post_borrower_message(
    payload: BorrowerChatMessageIn,
    db: Session = Depends(get_db),
    borrower_session: dict = Depends(get_borrower_session),
):
    deal_id = int(borrower_session["deal_id"])

    borrower_turn = ChatTurn(
        deal_id=deal_id,
        role=ChatRole.borrower.value,
        content=payload.content,
        structured_payload={},
    )
    db.add(borrower_turn)
    db.commit()

    result = run_intake_turn(db=db, deal_id=deal_id, borrower_message=payload.content)
    assistant_message = result.get("assistant_reply", "")
    snapshot = result.get("application_snapshot", {})
    missing_fields = result.get("missing_fields", [])
    progress = _build_progress(snapshot, missing_fields)

    assistant_turn = ChatTurn(
        deal_id=deal_id,
        role=ChatRole.assistant.value,
        content=assistant_message,
        structured_payload={"missing_fields": missing_fields, **progress},
    )
    db.add(assistant_turn)
    db.commit()

    return BorrowerChatMessageOut(
        assistant_message=assistant_message,
        application_snapshot=snapshot,
        missing_fields=missing_fields,
        **progress,
    )


@router.get("/history")
def get_chat_history(
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    borrower_session: dict = Depends(get_borrower_session),
):
    deal_id = int(borrower_session["deal_id"])
    turns = db.execute(
        select(ChatTurn).where(ChatTurn.deal_id == deal_id).order_by(ChatTurn.id.asc()).limit(limit)
    ).scalars().all()
    return [
        {
            "id": t.id,
            "role": t.role,
            "content": t.content,
            "structured_payload": t.structured_payload or {},
        }
        for t in turns
    ]
