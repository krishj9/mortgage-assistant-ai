from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, EmailStr


class BorrowerCreate(BaseModel):
    name: str
    dob_placeholder: str = "0000-00-00"
    contact_email: EmailStr
    contact_phone: Optional[str] = None


class BorrowerRead(BaseModel):
    id: int
    name: str
    dob_placeholder: str
    contact_email: EmailStr
    contact_phone: Optional[str] = None
    is_active: bool

    class Config:
        from_attributes = True

