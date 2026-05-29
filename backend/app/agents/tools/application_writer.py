from __future__ import annotations

from typing import Any

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.loan_application import LoanApplication
from app.schemas.loan_application import LoanApplicationData


def _format_validation_error(exc: ValidationError) -> str:
    parts: list[str] = []
    for err in exc.errors()[:4]:
        loc = ".".join(str(part) for part in err.get("loc", ()))
        msg = err.get("msg", "invalid value")
        parts.append(f"{loc}: {msg}" if loc else msg)
    return "; ".join(parts)


REQUIRED_FIELDS = [
    ("identity.borrower_name", "Borrower full name"),
    ("contact.contact_email", "Contact email"),
    ("employment.employment_status", "Employment status"),
    ("income.income_amount", "Income amount"),
    ("income.income_frequency", "Income frequency"),
    ("property.property_status", "Property status"),
    ("property.property_value_or_purchase_price", "Property value/purchase price"),
    ("loan_purpose.loan_purpose", "Loan purpose"),
]


def _deep_merge(base: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    result = dict(base)
    for k, v in patch.items():
        if isinstance(v, dict) and isinstance(result.get(k), dict):
            result[k] = _deep_merge(result[k], v)
        else:
            result[k] = v
    return result


def get_field_value(snapshot: dict[str, Any], path: str) -> Any:
    cur: Any = snapshot
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


def _is_present(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str) and not value.strip():
        return False
    return True


def compute_missing_fields(snapshot: dict[str, Any]) -> list[str]:
    missing: list[str] = []
    for path, label in REQUIRED_FIELDS:
        if not _is_present(get_field_value(snapshot, path)):
            missing.append(label)
    return missing


def compute_captured_fields(snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    """Required fields that have a value, with their human label and current value."""
    captured: list[dict[str, Any]] = []
    for path, label in REQUIRED_FIELDS:
        value = get_field_value(snapshot, path)
        if _is_present(value):
            captured.append({"path": path, "label": label, "value": value})
    return captured


def get_application_snapshot(db: Session, deal_id: int) -> tuple[dict, list[str]]:
    loan_app = db.execute(select(LoanApplication).where(LoanApplication.deal_id == deal_id)).scalar_one()
    missing = compute_missing_fields(loan_app.data or {})
    return loan_app.data or {}, missing


def apply_application_patch(db: Session, deal_id: int, patch: dict[str, Any]) -> tuple[dict, list[str]]:
    loan_app = db.execute(select(LoanApplication).where(LoanApplication.deal_id == deal_id)).scalar_one()
    merged = _deep_merge(loan_app.data or {}, patch)
    validated = LoanApplicationData.model_validate(merged)

    loan_app.data = validated.model_dump(mode="json")
    db.commit()
    db.refresh(loan_app)
    missing = compute_missing_fields(loan_app.data)
    return loan_app.data, missing


def try_apply_application_patch(
    db: Session, deal_id: int, patch: dict[str, Any]
) -> tuple[dict, list[str], bool, str | None]:
    """Apply patch; return (snapshot, missing_fields, applied, validation_error)."""
    if not patch:
        snapshot, missing = get_application_snapshot(db, deal_id)
        return snapshot, missing, False, None
    try:
        snapshot, missing = apply_application_patch(db, deal_id, patch)
        return snapshot, missing, True, None
    except ValidationError as exc:
        db.rollback()
        snapshot, missing = get_application_snapshot(db, deal_id)
        return snapshot, missing, False, _format_validation_error(exc)

