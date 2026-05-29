from __future__ import annotations

import re
from typing import Any

from app.schemas.deal_context import ApplicantMetadata, AssetRecord, IncomeRecord
from app.services.ocr.base import OcrResult


def _find_amount(text: str, labels: list[str]) -> float | None:
    lower = text.lower()
    for label in labels:
        pattern = rf"{re.escape(label.lower())}\s*[:#]?\s*\$?\s*([0-9]{{2,9}}(?:\.[0-9]{{1,2}})?)"
        match = re.search(pattern, lower)
        if match:
            return float(match.group(1))
    return None


def map_pay_stub(ocr: OcrResult, document_id: int) -> dict[str, Any]:
    gross = _find_amount(ocr.text, ["gross pay", "gross", "total pay"])
    employer = ocr.key_values.get("Employer") or ocr.key_values.get("employer")
    record = IncomeRecord(
        gross_income=gross,
        pay_frequency="monthly",
        employer=employer,
        source_document_id=document_id,
    )
    return {"income": [record.model_dump(mode="json")], "metadata": {}}


def map_w2(ocr: OcrResult, document_id: int) -> dict[str, Any]:
    wages = _find_amount(ocr.text, ["wages", "box 1", "compensation"])
    employer = (
        ocr.key_values.get("Employer")
        or ocr.key_values.get("employer name")
        or ocr.key_values.get("Employer Name")
    )
    record = IncomeRecord(
        gross_income=wages,
        pay_frequency="annual",
        employer=employer,
        source_document_id=document_id,
    )
    return {"income": [record.model_dump(mode="json")], "metadata": {}}


def map_bank_statement(ocr: OcrResult, document_id: int) -> dict[str, Any]:
    balance = _find_amount(ocr.text, ["ending balance", "balance", "average balance"])
    record = AssetRecord(
        account_type="checking",
        average_balance=balance,
        recent_large_deposits=[],
        source_document_id=document_id,
    )
    return {"assets": [record.model_dump(mode="json")], "metadata": {}}


def map_application_1003(ocr: OcrResult, document_id: int) -> dict[str, Any]:
    name = ocr.key_values.get("Borrower Name") or ocr.key_values.get("Name")
    address = ocr.key_values.get("Address")
    metadata = ApplicantMetadata(
        name=name,
        address=address,
        employer=None,
        source_document_id=document_id,
    )
    return {"income": [], "assets": [], "metadata": metadata.model_dump(mode="json")}


MAPPERS = {
    "pay_stub": map_pay_stub,
    "w2": map_w2,
    "bank_statement": map_bank_statement,
    "application_1003": map_application_1003,
}


def map_extraction(doc_type: str, ocr: OcrResult, document_id: int) -> dict[str, Any]:
    mapper = MAPPERS.get(doc_type, map_application_1003)
    return mapper(ocr, document_id)
