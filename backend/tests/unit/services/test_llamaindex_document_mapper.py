from __future__ import annotations

from app.services.llamaindex.document_mapper import map_bank_statement_extraction


def test_map_bank_statement_extraction():
    data = {
        "bank_name": "Demo Bank",
        "account_type": "checking",
        "ending_balance": 12500.5,
    }
    out = map_bank_statement_extraction(data, document_id=3)
    assert out["assets"][0]["average_balance"] == 12500.5
    assert out["assets"][0]["account_type"] == "checking"
