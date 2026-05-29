from __future__ import annotations

from pydantic import BaseModel, EmailStr


class StaffLoginRequest(BaseModel):
    email: EmailStr
    password: str


class BorrowerSessionRequest(BaseModel):
    deal_id: int
    borrower_email: EmailStr


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

