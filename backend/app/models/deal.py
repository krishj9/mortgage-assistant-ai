from __future__ import annotations

import enum

from sqlalchemy import Enum as SqlEnum, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class DealStatus(str, enum.Enum):
    intake_in_progress = "intake_in_progress"
    docs_pending = "docs_pending"
    extraction_in_progress = "extraction_in_progress"
    ready_for_review = "ready_for_review"
    lo_approved = "lo_approved"
    closed = "closed"


class Deal(Base, TimestampMixin):
    __tablename__ = "deals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    borrower_id: Mapped[int] = mapped_column(ForeignKey("borrowers.id"), index=True, nullable=False)
    status: Mapped[DealStatus] = mapped_column(
        SqlEnum(DealStatus, name="deal_status"), default=DealStatus.intake_in_progress, nullable=False
    )

    borrower = relationship("Borrower", backref="deals")

