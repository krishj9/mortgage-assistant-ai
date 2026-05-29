from __future__ import annotations

import enum
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class DocumentType(str, enum.Enum):
    pay_stub = "pay_stub"
    w2 = "w2"
    bank_statement = "bank_statement"
    application_1003 = "application_1003"
    unknown = "unknown"


class ExtractionStatus(str, enum.Enum):
    pending = "pending"
    running = "running"
    succeeded = "succeeded"
    failed = "failed"


class Document(Base, TimestampMixin):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    deal_id: Mapped[int] = mapped_column(ForeignKey("deals.id"), index=True, nullable=False)
    storage_uri: Mapped[str] = mapped_column(String(1024), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(128), nullable=False, default="application/pdf")
    predicted_type: Mapped[str] = mapped_column(String(64), nullable=False, default=DocumentType.unknown.value)
    classification_confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    extraction_status: Mapped[str] = mapped_column(
        String(64), nullable=False, default=ExtractionStatus.pending.value
    )
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
