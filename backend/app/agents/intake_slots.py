from __future__ import annotations

import re
from typing import Any

from app.agents.tools.application_writer import REQUIRED_FIELDS

# Map human-readable missing-field labels to JSON paths.
_LABEL_TO_PATH: dict[str, str] = {label: path for path, label in REQUIRED_FIELDS}


def _parse_money_token(raw: str) -> float | None:
    token = raw.strip().replace(",", "").replace("$", "")
    if not token:
        return None
    k_match = re.fullmatch(r"([0-9]+(?:\.[0-9]{1,2})?)([kK])", token)
    if k_match:
        return float(k_match.group(1)) * 1000
    num_match = re.fullmatch(r"[0-9]+(?:\.[0-9]{1,2})?", token)
    if num_match:
        return float(token)
    return None


def _all_money_in(text: str) -> list[float]:
    amounts: list[float] = []
    for match in re.finditer(
        r"\$?\s*([0-9]{1,3}(?:,[0-9]{3})+|[0-9]+(?:\.[0-9]{1,2})?)([kK])?",
        text,
    ):
        amount = _parse_money_token(match.group(0))
        if amount is not None:
            amounts.append(amount)
    return amounts


def _single_money_in(text: str) -> float | None:
    amounts = _all_money_in(text)
    if len(amounts) == 1:
        return amounts[0]
    return None


def _first_money_in(text: str) -> float | None:
    amounts = _all_money_in(text)
    return amounts[0] if amounts else None


def _money_after_keyword(text: str, keywords: str) -> float | None:
    """First monetary value appearing after any of the keywords."""
    lower = text.lower()
    best_idx = -1
    for keyword in keywords.split("|"):
        idx = lower.find(keyword)
        if idx == -1:
            continue
        if best_idx == -1 or idx < best_idx:
            best_idx = idx
    if best_idx == -1:
        return None
    tail = text[best_idx:]
    # Drop the keyword itself so a numeric keyword (unlikely) is not matched.
    return _first_money_in(tail)


def try_l0_slot_parse(message: str, next_missing_label: str | None) -> dict[str, Any]:
    """
    L0 deterministic extraction when we know which single field we are collecting.
    Returns a partial patch dict (may be empty).
    """
    if not next_missing_label:
        return {}

    text = message.strip()
    lower = text.lower()
    patch: dict[str, Any] = {}

    if next_missing_label == "Contact email":
        email_match = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
        if email_match:
            patch["contact"] = {"contact_email": email_match.group(0)}

    elif next_missing_label == "Borrower full name":
        name_match = re.search(
            r"(?:my name is|i am|i'm|this is)\s+([A-Za-z]+(?:\s+[A-Za-z]+)+)", lower
        )
        if name_match:
            patch["identity"] = {"borrower_name": name_match.group(1).title()}
        elif re.fullmatch(r"[A-Za-z]+(?:\s+[A-Za-z]+)+", text):
            patch["identity"] = {"borrower_name": text.title()}

    elif next_missing_label == "Employment status":
        if "employed" in lower or "full-time" in lower or "full time" in lower:
            patch["employment"] = {"employment_status": "employed"}

    elif next_missing_label == "Income amount":
        amount = _money_after_keyword(text, "income|salary|earn|earning|make|paid")
        if amount is None:
            amount = _parse_money_token(text)
        if amount is None:
            amount = _single_money_in(text)
        if amount is not None:
            patch["income"] = {"income_amount": amount}

    elif next_missing_label == "Income frequency":
        if re.search(r"\b(monthly|per month|/month|each month)\b", lower):
            patch["income"] = {"income_frequency": "monthly"}
        elif re.search(r"\b(annual|annually|yearly|per year|/year)\b", lower):
            patch["income"] = {"income_frequency": "annual"}

    elif next_missing_label == "Property status":
        if "under contract" in lower:
            patch["property"] = {"property_status": "under_contract"}
        elif "shopping" in lower or "still looking" in lower:
            patch["property"] = {"property_status": "shopping"}
        elif "refinance" in lower or "refi" in lower:
            patch["property"] = {"property_status": "refinance"}

    elif next_missing_label == "Property value/purchase price":
        amount = _money_after_keyword(
            text, "purchase price|property value|home value|house price|price"
        )
        if amount is None:
            amount = _single_money_in(text)
        if amount is not None:
            patch["property"] = {"property_value_or_purchase_price": amount}

    elif next_missing_label == "Loan purpose":
        if "purchase" in lower or "buy" in lower:
            patch["loan_purpose"] = {"loan_purpose": "purchase"}
        elif "refinance" in lower or "refi" in lower:
            patch["loan_purpose"] = {"loan_purpose": "refinance"}

    return patch


def is_l0_confident(message: str, patch: dict[str, Any], next_missing_label: str | None) -> bool:
    """True when the patch clearly answers the expected single missing field."""
    if not patch or not next_missing_label:
        return False
    if len(_all_money_in(message)) > 1 and next_missing_label in {
        "Income amount",
        "Property value/purchase price",
    }:
        return False
    path = _LABEL_TO_PATH.get(next_missing_label)
    if not path:
        return False
    cur: Any = patch
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return False
        cur = cur[part]
    if cur is None or (isinstance(cur, str) and not str(cur).strip()):
        return False
    return True


def extract_patch_from_message(message: str) -> dict[str, Any]:
    """
    Best-effort multi-field regex extract across all known slots.

    Used for tests and as an optional aggregate fast-path; production intake uses
    try_l0_slot_parse keyed on the next missing field.
    """
    patch: dict[str, Any] = {}
    for _path, label in REQUIRED_FIELDS:
        slot = try_l0_slot_parse(message, label)
        for key, value in slot.items():
            if key not in patch:
                patch[key] = value
            elif isinstance(value, dict) and isinstance(patch[key], dict):
                patch[key] = {**patch[key], **value}
            else:
                patch[key] = value
    return patch
