from __future__ import annotations

import re
from typing import Any, Literal

from app.schemas.deal_context import AssetRecord, IncomeRecord
from app.services.llamaindex.income_mapper import (
    _coerce_float,
    map_pay_stub_extraction,
    map_w2_extraction,
)

SupportedDocType = Literal["pay_stub", "w2", "bank_statement"]


def map_bank_statement_extraction(data: dict[str, Any], document_id: int) -> dict[str, Any]:
    balance = _coerce_float(data.get("ending_balance")) or _coerce_float(data.get("average_balance"))
    record = AssetRecord(
        account_type=(data.get("account_type") or "checking").lower(),
        average_balance=balance,
        recent_large_deposits=[],
        source_document_id=document_id,
    )
    return {"assets": [record.model_dump(mode="json")], "metadata": {}}


def map_document_extraction(
    doc_type: SupportedDocType,
    data: dict[str, Any],
    document_id: int,
) -> dict[str, Any]:
    if doc_type == "pay_stub":
        return map_pay_stub_extraction(data, document_id)
    if doc_type == "w2":
        return map_w2_extraction(data, document_id)
    return map_bank_statement_extraction(data, document_id)
