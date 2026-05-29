from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class EligibilityStatus(str, Enum):
    green = "green"
    yellow = "yellow"
    red = "red"


class RuleEvaluation(BaseModel):
    rule_id: str
    passed: bool
    message: str
    value: Optional[float] = None
    threshold: Optional[float] = None


class EligibilityResult(BaseModel):
    status: EligibilityStatus
    dti: Optional[float] = None
    ltv: Optional[float] = None
    monthly_income: Optional[float] = None
    monthly_debts: Optional[float] = None
    estimated_housing_payment: Optional[float] = None
    loan_amount: Optional[float] = None
    property_value: Optional[float] = None
    rule_evaluations: list[RuleEvaluation] = Field(default_factory=list)
    computed_at: datetime = Field(default_factory=lambda: datetime.utcnow())
    eligibility_approved: bool = False
    lo_status_override: Optional[EligibilityStatus] = None


class Condition(BaseModel):
    id: str
    code: str
    title: str
    rationale: str
    required_doc_type: Optional[str] = None


class ConditionsList(BaseModel):
    items: list[Condition] = Field(default_factory=list)


class EligibilityPatch(BaseModel):
    status: Optional[EligibilityStatus] = None
    conditions: Optional[ConditionsList] = None


class MessagesUpdate(BaseModel):
    internal_draft: Optional[str] = None
    borrower_draft: Optional[str] = None


class MessageApprovalIn(BaseModel):
    channel: Literal["internal", "borrower"]
    approved: bool = True
