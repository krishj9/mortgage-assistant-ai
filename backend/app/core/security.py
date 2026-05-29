from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import jwt
from passlib.context import CryptContext

from app.core.config import settings


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return pwd_context.verify(password, hashed_password)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def create_access_token(subject: str, token_type: str, expires_in_seconds: int) -> str:
    now = _utcnow()
    payload = {
        "sub": subject,
        "type": token_type,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=expires_in_seconds)).timestamp()),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def verify_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])


def sign_borrower_session(deal_id: int, borrower_id: int) -> str:
    """
    Borrower-scoped session token for MVP.
    Encodes both deal_id and borrower_id to enforce scoping.
    """
    now = _utcnow()
    payload = {
        "sub": str(borrower_id),
        "type": "borrower",
        "deal_id": deal_id,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=settings.BORROWER_TOKEN_EXPIRE_SECONDS)).timestamp()),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def verify_borrower_session(token: str) -> tuple[int, int]:
    """
    Returns (borrower_id, deal_id).
    Raises on invalid token.
    """
    payload = verify_token(token)
    if payload.get("type") != "borrower":
        raise ValueError("Invalid token type")
    borrower_id = int(payload["sub"])
    deal_id = int(payload["deal_id"])
    return borrower_id, deal_id

