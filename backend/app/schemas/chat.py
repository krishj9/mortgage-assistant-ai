from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel


class BorrowerChatMessageIn(BaseModel):
    content: str


class ChatTurnRead(BaseModel):
    id: int
    role: str
    content: str
    structured_payload: dict


class CapturedField(BaseModel):
    path: str
    label: str
    value: Any


class BorrowerChatMessageOut(BaseModel):
    assistant_message: str
    application_snapshot: dict
    missing_fields: list[str]
    captured_fields: list[CapturedField]
    current_field: Optional[str] = None
    completed: int
    total_required: int

