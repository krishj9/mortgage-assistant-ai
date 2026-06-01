from __future__ import annotations

from app.services.llamaindex.income_mapper import map_income_extraction, map_pay_stub_extraction, map_w2_extraction


def test_map_pay_stub_extraction():
    data = {
        "employer": "Acme Corp",
        "employee_name": "Alice Borrower",
        "gross_pay": 8500.0,
        "pay_frequency": "Bi-Weekly",
        "ytd_gross": 34000.0,
    }
    out = map_pay_stub_extraction(data, document_id=7)
    income = out["income"][0]
    assert income["gross_income"] == 8500.0
    assert income["employer"] == "Acme Corp"
    assert income["pay_frequency"] == "biweekly"
    assert income["source_document_id"] == 7


def test_map_w2_extraction():
    data = {
        "employer_name": "Acme Corp",
        "employee_name": "Alice Borrower",
        "box_1_wages": 96000.0,
        "tax_year": "2025",
    }
    out = map_w2_extraction(data, document_id=8)
    income = out["income"][0]
    assert income["gross_income"] == 96000.0
    assert income["employer"] == "Acme Corp"
    assert income["pay_frequency"] == "annual"


def test_map_income_extraction_dispatches():
    out = map_income_extraction(
        "w2",
        {"employer_name": "Acme", "box_1_wages": "96000.00"},
        document_id=9,
    )
    assert out["income"][0]["gross_income"] == 96000.0
