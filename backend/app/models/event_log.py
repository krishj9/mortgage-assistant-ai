from __future__ import annotations

import enum
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class EventKind(str, enum.Enum):
    intake_complete = "intake_complete"
    document_extracted = "document_extracted"
    eligibility_computed = "eligibility_computed"
    messages_approved = "messages_approved"


class EventLog(Base):
    __tablename__ = "event_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    deal_id: Mapped[int] = mapped_column(ForeignKey("deals.id"), index=True, nullable=False)
    kind: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    payload_snapshot: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
