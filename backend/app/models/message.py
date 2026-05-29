from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class Messages(Base, TimestampMixin):
    __tablename__ = "messages"

    deal_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("deals.id"), primary_key=True, nullable=False
    )

    # Legacy columns (kept for backward compatibility).
    internal_notes: Mapped[str] = mapped_column(Text, nullable=False, default="")
    borrower_message: Mapped[str] = mapped_column(Text, nullable=False, default="")

    # Draft messages produced by the messaging agent (Phase 4).
    internal_draft: Mapped[str] = mapped_column(Text, nullable=False, default="")
    borrower_draft: Mapped[str] = mapped_column(Text, nullable=False, default="")

    internal_approved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    borrower_approved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    approved_by_user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    deal = relationship("Deal", backref="messages")

