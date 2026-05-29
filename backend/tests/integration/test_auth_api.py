from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.user import User


@pytest.mark.asyncio
async def test_staff_login_happy(async_client: AsyncClient):
    db = SessionLocal()
    try:
        # Ensure user exists.
        user = db.execute(select(User).where(User.email == "lo@example.com")).scalar_one_or_none()
        if user is None:
            user = User(
                email="lo@example.com",
                hashed_password=hash_password("password"),
                is_active=True,
            )
            db.add(user)
            db.commit()
            db.refresh(user)
    finally:
        db.close()

    resp = await async_client.post(
        "/auth/staff/login",
        json={"email": "lo@example.com", "password": "password"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_staff_login_invalid_password(async_client: AsyncClient):
    resp = await async_client.post(
        "/auth/staff/login",
        json={"email": "lo@example.com", "password": "wrong"},
    )
    assert resp.status_code == 401

