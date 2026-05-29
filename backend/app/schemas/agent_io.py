from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.eligibility import Condition
from app.schemas.loan_application import (
    AssetsData,
    ContactData,
    EmploymentData,
    IdentityData,
    IncomeData,
    LiabilitiesData,
    LoanPurposeData,
    PropertyData,
)


class LoanApplicationPatch(BaseModel):
    """Partial intake update extracted from a single borrower turn (L1 structured output)."""

    model_config = ConfigDict(extra="forbid")

    identity: Optional[IdentityData] = None
    contact: Optional[ContactData] = None
    employment: Optional[EmploymentData] = None
    income: Optional[IncomeData] = None
    assets: Optional[AssetsData] = None
    liabilities: Optional[LiabilitiesData] = None
    property: Optional[PropertyData] = None
    loan_purpose: Optional[LoanPurposeData] = None


class IntakeTurnResult(BaseModel):
    """Borrower-facing assistant message (L2 structured output)."""

    model_config = ConfigDict(extra="forbid")

    assistant_message: str
    clarification_field: Optional[str] = None


class IntakeTurn(BaseModel):
    """Unified per-turn intake output: extraction patch + classified intent + reply."""

    model_config = ConfigDict(extra="forbid")

    assistant_message: str = Field(
        description="Short, warm borrower-facing reply (1-2 sentences)."
    )
    intent: Literal[
        "answer", "clarify_question", "recap_request", "smalltalk", "correction"
    ] = Field(
        default="answer",
        description="What the borrower's latest message is doing.",
    )
    patch: Optional[LoanApplicationPatch] = Field(
        default=None,
        description="Fields clearly provided this turn; null/omit anything not stated.",
    )
    target_field: Optional[str] = Field(
        default=None,
        description="Human label of the field this reply is asking about or clarifying.",
    )


class IntakeGuidance(BaseModel):
    """Borrower-facing guidance when an answer could not be saved (invalid or ambiguous)."""

    model_config = ConfigDict(extra="forbid")

    assistant_message: str = Field(
        description=(
            "Warm 1-2 sentence reply acknowledging what the borrower said and "
            "guiding them to a valid answer with allowed options or format examples."
        )
    )


class MessageDrafts(BaseModel):
    model_config = ConfigDict(extra="forbid")

    internal_draft: str
    borrower_draft: str


class ConditionRefinement(BaseModel):
    """LLM may refine condition titles/rationales only - not status, DTI, or LTV."""

    model_config = ConfigDict(extra="forbid")

    items: list[Condition] = Field(default_factory=list)


class DocumentClassification(BaseModel):
    model_config = ConfigDict(extra="forbid")

    predicted_type: Literal["pay_stub", "w2", "bank_statement", "application_1003", "unknown"]
    confidence: float = Field(ge=0.0, le=1.0)


def patch_to_dict(patch: LoanApplicationPatch) -> dict:
    """Drop unset fields so merges do not overwrite saved values with nulls."""
    return patch.model_dump(mode="json", exclude_none=True)
