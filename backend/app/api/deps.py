from __future__ import annotations

from typing import Annotated, Generator

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from sqlalchemy.orm import Session

from app.core.security import verify_borrower_session, verify_token
from app.db.session import get_session

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/staff/login")


def get_db() -> Generator[Session, None, None]:
    yield from get_session()


def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> dict:
    """
    Returns staff user context from Bearer JWT.
    """
    try:
        payload = verify_token(token)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from e

    if payload.get("type") != "staff":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")

    return {"user_id": int(payload["sub"])}


def get_borrower_session(token: Annotated[str, Depends(oauth2_scheme)]) -> dict:
    """
    Returns borrower + deal scoping from Bearer JWT.
    """
    try:
        borrower_id, deal_id = verify_borrower_session(token)
        return {"borrower_id": borrower_id, "deal_id": deal_id}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid borrower session") from e


def require_deal_access(
    deal_id: int,
    borrower_session: dict = Depends(get_borrower_session),
    # Staff can access all deals (handled by routes that depend on get_current_user instead).
) -> dict:
    if int(borrower_session["deal_id"]) != int(deal_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Deal access denied")
    return borrower_session

