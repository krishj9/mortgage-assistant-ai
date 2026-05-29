from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class DocumentExtraction(Base, TimestampMixin):
    __tablename__ = "document_extractions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id"), unique=True, index=True, nullable=False
    )
    raw_ocr: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    normalized: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    confidence: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    human_corrections: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    status: Mapped[str] = mapped_column(String(64), nullable=False, default="pending")
