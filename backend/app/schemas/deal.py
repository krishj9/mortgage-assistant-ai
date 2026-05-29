from __future__ import annotations

import enum
from typing import Literal, Optional

from pydantic import BaseModel


class DealStatus(str, enum.Enum):
    intake_in_progress = "intake_in_progress"
    docs_pending = "docs_pending"
    extraction_in_progress = "extraction_in_progress"
    ready_for_review = "ready_for_review"
    lo_approved = "lo_approved"
    closed = "closed"


class DealCreate(BaseModel):
    borrower_id: int


class DealPatch(BaseModel):
    status: DealStatus


class DealRead(BaseModel):
    id: int
    borrower_id: int
    status: DealStatus

    class Config:
        from_attributes = True

