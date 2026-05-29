from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.core.security import sign_borrower_session
from app.schemas.agent_io import IntakeGuidance, IntakeTurn, LoanApplicationPatch
from app.db.session import SessionLocal
from app.models.borrower import Borrower
from app.models.deal import Deal, DealStatus
from app.models.deal_context import DealContext
from app.models.loan_application import LoanApplication
from app.models.message import Messages


def _create_borrower_deal(db):
    unique = uuid.uuid4().hex[:8]
    borrower = Borrower(
        name="Chat Test Borrower",
        dob_placeholder="0000-00-00",
        contact_email=f"chat_test_{unique}@example.com",
        contact_phone=None,
        is_active=True,
    )
    db.add(borrower)
    db.flush()

    deal = Deal(borrower_id=borrower.id, status=DealStatus.intake_in_progress)
    db.add(deal)
    db.flush()

    db.add(LoanApplication(deal_id=deal.id, data={}))
    db.add(DealContext(deal_id=deal.id, extracted_income={}, extracted_assets={}, extracted_liabilities={}))
    db.add(Messages(deal_id=deal.id, internal_notes="", borrower_message="", internal_approved=False, borrower_approved=False))
    db.commit()
    return borrower.id, deal.id


class _FakeModel:
    """Stand-in for a structured Bedrock model: returns a preset IntakeTurn."""

    def __init__(self, result: IntakeTurn):
        self._result = result

    def invoke(self, _messages):
        return self._result


def _stub_intake(monkeypatch, result: IntakeTurn):
    monkeypatch.setattr(
        "app.agents.nodes.intake_agent.get_structured_model",
        lambda *args, **kwargs: _FakeModel(result),
    )


@pytest.mark.asyncio
async def test_borrower_chat_turn_and_completion(async_client: AsyncClient, monkeypatch):
    db = SessionLocal()
    try:
        borrower_id, deal_id = _create_borrower_deal(db)
        token = sign_borrower_session(deal_id=deal_id, borrower_id=borrower_id)
    finally:
        db.close()

    # The multi-field message is fully captured by deterministic L0 extraction;
    # the LLM turn returns no extra patch here.
    _stub_intake(monkeypatch, IntakeTurn(assistant_message="Thanks!", patch=LoanApplicationPatch()))

    payload = {
        "content": (
            "My name is Jane Borrower, I am employed, my income is 8000 monthly, "
            "I am shopping, purchase price 500000, loan purpose purchase, email jane@example.com"
        )
    }
    r = await async_client.post(
        "/borrower/chat/messages",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    body = r.json()
    assert "assistant_message" in body
    assert body["missing_fields"] == []
    assert body["completed"] == body["total_required"]
    assert any(f["label"] == "Income amount" for f in body["captured_fields"])

    hist = await async_client.get(
        "/borrower/chat/history",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert hist.status_code == 200
    turns = hist.json()
    assert len(turns) >= 2
    assert turns[0]["role"] == "borrower"
    assert turns[1]["role"] == "assistant"


@pytest.mark.asyncio
async def test_clarify_question_does_not_repeat(async_client: AsyncClient, monkeypatch):
    """An ambiguous answer surfaces the LLM's clarifying reply and saves nothing."""
    db = SessionLocal()
    try:
        borrower_id, deal_id = _create_borrower_deal(db)
        token = sign_borrower_session(deal_id=deal_id, borrower_id=borrower_id)
    finally:
        db.close()

    clarify = IntakeTurn(
        assistant_message=(
            "When you say you own the home, do you mean you'd like to refinance it?"
        ),
        intent="clarify_question",
        patch=None,
        target_field="Property status",
    )
    _stub_intake(monkeypatch, clarify)

    r = await async_client.post(
        "/borrower/chat/messages",
        json={"content": "Own"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["assistant_message"] == clarify.assistant_message
    # Nothing was saved, so no captured fields and the form is still incomplete.
    assert body["captured_fields"] == []
    assert body["completed"] == 0


@pytest.mark.asyncio
async def test_own_without_llm_uses_guidance_llm(async_client: AsyncClient, monkeypatch):
    """When the primary turn fails, a guidance LLM call handles any invalid field answer."""
    db = SessionLocal()
    try:
        borrower_id, deal_id = _create_borrower_deal(db)
        token = sign_borrower_session(deal_id=deal_id, borrower_id=borrower_id)
        loan_app = db.execute(
            select(LoanApplication).where(LoanApplication.deal_id == deal_id)
        ).scalar_one()
        loan_app.data = {
            "identity": {"borrower_name": "Alice Borrower"},
            "contact": {"contact_email": "alice@example.com"},
            "employment": {"employment_status": "employed"},
            "income": {"income_amount": 8000, "income_frequency": "monthly"},
        }
        db.commit()
    finally:
        db.close()

    guidance_text = (
        "Thanks — when you say you own the home, are you looking to refinance it, "
        "or are you under contract to buy a different property?"
    )

    def _structured_factory(schema, **_kwargs):
        if schema is IntakeGuidance:
            return _FakeModel(IntakeGuidance(assistant_message=guidance_text))
        raise RuntimeError("primary intake turn unavailable")

    monkeypatch.setattr(
        "app.agents.nodes.intake_agent.get_structured_model",
        _structured_factory,
    )

    r = await async_client.post(
        "/borrower/chat/messages",
        json={"content": "Own"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["assistant_message"] == guidance_text
    assert body["missing_fields"][0] == "Property status"


@pytest.mark.asyncio
async def test_invalid_email_triggers_guidance_llm(async_client: AsyncClient, monkeypatch):
    """Any field with an invalid answer triggers guidance, not a generic repeat."""
    db = SessionLocal()
    try:
        borrower_id, deal_id = _create_borrower_deal(db)
        token = sign_borrower_session(deal_id=deal_id, borrower_id=borrower_id)
        loan_app = db.execute(
            select(LoanApplication).where(LoanApplication.deal_id == deal_id)
        ).scalar_one()
        loan_app.data = {"identity": {"borrower_name": "Jane Borrower"}}
        db.commit()
    finally:
        db.close()

    guidance_text = "That doesn't look like an email — could you share one like name@example.com?"

    def _structured_factory(schema, **_kwargs):
        if schema is IntakeGuidance:
            return _FakeModel(IntakeGuidance(assistant_message=guidance_text))
        return _FakeModel(IntakeTurn(assistant_message="", patch=None))

    monkeypatch.setattr(
        "app.agents.nodes.intake_agent.get_structured_model",
        _structured_factory,
    )

    r = await async_client.post(
        "/borrower/chat/messages",
        json={"content": "not-an-email"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["assistant_message"] == guidance_text
    assert body["missing_fields"][0] == "Contact email"


@pytest.mark.asyncio
async def test_recap_request_is_answered(async_client: AsyncClient, monkeypatch):
    """A recap request is answered conversationally rather than re-asking a field."""
    db = SessionLocal()
    try:
        borrower_id, deal_id = _create_borrower_deal(db)
        token = sign_borrower_session(deal_id=deal_id, borrower_id=borrower_id)
    finally:
        db.close()

    recap = IntakeTurn(
        assistant_message="So far you've shared your name. Next, what's your email?",
        intent="recap_request",
        patch=None,
    )
    _stub_intake(monkeypatch, recap)

    r = await async_client.post(
        "/borrower/chat/messages",
        json={"content": "what have I told you so far?"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["assistant_message"] == recap.assistant_message
    assert body["current_field"] is not None
