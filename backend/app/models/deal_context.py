from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class DealContext(Base, TimestampMixin):
    __tablename__ = "deal_contexts"

    deal_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("deals.id"), primary_key=True, nullable=False
    )

    # Normalized extracted entities (initially empty; filled after document pipeline in Phase 3).
    extracted_income: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    extracted_assets: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    extracted_liabilities: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    # Computed metrics and status flags (legacy; mirrored from eligibility for API compat).
    computed_metrics: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    status_flags: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    # Eligibility agent outputs (Phase 4).
    eligibility: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    conditions: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    deal = relationship("Deal", backref="deal_context")

