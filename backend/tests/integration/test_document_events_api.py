from __future__ import annotations

import asyncio
import json
import uuid

import pytest
from httpx import AsyncClient

from app.core.security import sign_borrower_session
from app.db.session import SessionLocal
from app.models.borrower import Borrower
from app.models.deal import Deal, DealStatus
from app.models.deal_context import DealContext
from app.models.loan_application import LoanApplication
from app.models.message import Messages
from app.services import document_event_hub


def _seed_deal(db):
    unique = uuid.uuid4().hex[:8]
    borrower = Borrower(
        name="SSE Borrower",
        dob_placeholder="0000-00-00",
        contact_email=f"sse_{unique}@example.com",
        contact_phone=None,
        is_active=True,
    )
    db.add(borrower)
    db.flush()
    deal = Deal(borrower_id=borrower.id, status=DealStatus.docs_pending)
    db.add(deal)
    db.flush()
    db.add(LoanApplication(deal_id=deal.id, data={}))
    db.add(
        DealContext(
            deal_id=deal.id,
            extracted_income={},
            extracted_assets={},
            extracted_liabilities={},
        )
    )
    db.add(
        Messages(
            deal_id=deal.id,
            internal_notes="",
            borrower_message="",
            internal_approved=False,
            borrower_approved=False,
        )
    )
    db.commit()
    return borrower.id, deal.id


@pytest.mark.asyncio
async def test_document_events_stream(async_client: AsyncClient, monkeypatch):
    document_event_hub.reset_for_tests()
    monkeypatch.setattr("app.api.documents.run_document_pipeline", lambda _document_id: None)

    db = SessionLocal()
    try:
        borrower_id, _deal_id = _seed_deal(db)
        token = sign_borrower_session(deal_id=_deal_id, borrower_id=borrower_id)
    finally:
        db.close()

    files = {"file": ("pay_stub.txt", b"Employer: Acme\nGross Pay: 5000", "text/plain")}
    upload = await async_client.post(
        "/documents",
        files=files,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert upload.status_code == 201
    document_id = upload.json()["id"]

    events: list[dict] = []

    async def collect_events() -> None:
        async with async_client.stream(
            "GET",
            f"/documents/{document_id}/events",
            headers={"Authorization": f"Bearer {token}"},
        ) as response:
            assert response.status_code == 200
            assert response.headers["content-type"].startswith("text/event-stream")
            async for line in response.aiter_lines():
                if not line.startswith("data: "):
                    continue
                events.append(json.loads(line[6:]))
                if events[-1].get("status") in ("succeeded", "failed"):
                    return

    collector = asyncio.create_task(collect_events())
    await asyncio.sleep(0.05)

    document_event_hub.publish(
        document_id,
        document_event_hub.build_event(document_id, status="running", stage="parsing"),
    )
    document_event_hub.publish(
        document_id,
        document_event_hub.build_event(
            document_id,
            status="succeeded",
            predicted_type="pay_stub",
            classification_confidence=0.9,
        ),
    )

    await asyncio.wait_for(collector, timeout=2.0)

    assert events
    assert events[-1]["status"] == "succeeded"
    assert events[-1]["predicted_type"] == "pay_stub"
