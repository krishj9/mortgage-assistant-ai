from __future__ import annotations

from typing import TypedDict


class LoanCopilotState(TypedDict, total=False):
    deal_id: int
    latest_borrower_message: str
    application_snapshot: dict
    application_patch: dict
    missing_fields: list[str]
    assistant_reply: str

