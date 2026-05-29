from __future__ import annotations

from app.core.security import create_access_token, sign_borrower_session, verify_borrower_session, verify_token
from app.core.config import settings


def test_staff_token_round_trip():
    token = create_access_token(subject="1", token_type="staff", expires_in_seconds=60)
    payload = verify_token(token)
    assert payload["sub"] == "1"
    assert payload["type"] == "staff"
    assert isinstance(payload["iat"], int)


def test_borrower_token_scoped_claims():
    token = sign_borrower_session(deal_id=123, borrower_id=5)
    borrower_id, deal_id = verify_borrower_session(token)
    assert borrower_id == 5
    assert deal_id == 123

