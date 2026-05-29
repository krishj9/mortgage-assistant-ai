from __future__ import annotations

from sqlalchemy import ForeignKey, Integer
from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class LoanApplication(Base, TimestampMixin):
    __tablename__ = "loan_applications"

    deal_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("deals.id"), primary_key=True, nullable=False
    )
    # Canonical structured payload captured from borrower chat.
    data: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    deal = relationship("Deal", backref="loan_application")

