from __future__ import annotations

from pydantic import BaseModel


class MessagesRead(BaseModel):
    deal_id: int
    internal_notes: str = ""
    borrower_message: str = ""
    internal_approved: bool = False
    borrower_approved: bool = False

    class Config:
        from_attributes = True

