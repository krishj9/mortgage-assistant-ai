from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.core.security import sign_borrower_session
from app.db.session import SessionLocal
from app.models.borrower import Borrower
from app.models.deal import Deal, DealStatus
from app.models.deal_context import DealContext
from app.models.event_log import EventKind, EventLog
from app.models.loan_application import LoanApplication
from app.models.message import Messages
from app.services.event_log_service import record_event


def _seed_deal(db):
    unique = uuid.uuid4().hex[:8]
    borrower = Borrower(
        name="Obs Borrower",
        dob_placeholder="0000-00-00",
        contact_email=f"obs_{unique}@example.com",
        contact_phone=None,
        is_active=True,
    )
    db.add(borrower)
    db.flush()
    deal = Deal(borrower_id=borrower.id, status=DealStatus.docs_pending)
    db.add(deal)
    db.flush()
    db.add(LoanApplication(deal_id=deal.id, data={}))
    db.add(DealContext(deal_id=deal.id, extracted_income={}, extracted_assets={}, extracted_liabilities={}))
    db.add(Messages(deal_id=deal.id, internal_notes="", borrower_message="", internal_approved=False, borrower_approved=False))
    db.commit()
    return borrower.id, deal.id


@pytest.mark.asyncio
async def test_readyz_endpoint(async_client: AsyncClient):
    resp = await async_client.get("/readyz")
    assert resp.status_code in (200, 503)
    body = resp.json()
    assert "checks" in body
    assert "database" in body["checks"]


@pytest.mark.asyncio
async def test_event_log_recorded_on_manual_emit():
    db = SessionLocal()
    try:
        _, deal_id = _seed_deal(db)
        record_event(db, deal_id=deal_id, kind=EventKind.intake_complete, payload={"test": True})
        rows = db.execute(select(EventLog).where(EventLog.deal_id == deal_id)).scalars().all()
        assert len(rows) == 1
        assert rows[0].kind == EventKind.intake_complete.value
    finally:
        db.close()


@pytest.mark.asyncio
async def test_healthz(async_client: AsyncClient):
    resp = await async_client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
