from __future__ import annotations

from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class Borrower(Base, TimestampMixin):
    __tablename__ = "borrowers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    # Phase-1 uses DOB placeholder tokens (synthetic only).
    dob_placeholder: Mapped[str] = mapped_column(String(32), nullable=False, default="0000-00-00")
    contact_email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    contact_phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

