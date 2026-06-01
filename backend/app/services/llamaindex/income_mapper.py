from __future__ import annotations

import re
from typing import Any, Literal

from app.schemas.deal_context import AssetRecord, IncomeRecord

_FREQ_ALIASES = {
    "weekly": "weekly",
    "bi-weekly": "biweekly",
    "biweekly": "biweekly",
    "semi-monthly": "semi-monthly",
    "semimonthly": "semi-monthly",
    "monthly": "monthly",
    "annual": "annual",
    "yearly": "annual",
}


def _normalize_pay_frequency(value: str | None) -> str | None:
    if not value:
        return None
    key = value.strip().lower()
    return _FREQ_ALIASES.get(key, re.sub(r"\s+", " ", key))


def map_pay_stub_extraction(data: dict[str, Any], document_id: int) -> dict[str, Any]:
    record = IncomeRecord(
        gross_income=_coerce_float(data.get("gross_pay")),
        pay_frequency=_normalize_pay_frequency(data.get("pay_frequency")) or "monthly",
        employer=data.get("employer"),
        source_document_id=document_id,
    )
    return {"income": [record.model_dump(mode="json")], "metadata": {}}


def map_w2_extraction(data: dict[str, Any], document_id: int) -> dict[str, Any]:
    record = IncomeRecord(
        gross_income=_coerce_float(data.get("box_1_wages")),
        pay_frequency="annual",
        employer=data.get("employer_name"),
        source_document_id=document_id,
    )
    return {"income": [record.model_dump(mode="json")], "metadata": {}}


def _coerce_float(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        cleaned = value.replace("$", "").replace(",", "").strip()
        if not cleaned:
            return None
        try:
            return float(cleaned)
        except ValueError:
            return None
    return None


def map_income_extraction(
    doc_type: Literal["pay_stub", "w2"],
    data: dict[str, Any],
    document_id: int,
) -> dict[str, Any]:
    if doc_type == "pay_stub":
        return map_pay_stub_extraction(data, document_id)
    return map_w2_extraction(data, document_id)
