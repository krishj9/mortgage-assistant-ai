from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, EmailStr, Field


class IdentityData(BaseModel):
    borrower_name: Optional[str] = None
    dob_placeholder: Optional[str] = Field(
        default=None, description="Synthetic DOB placeholder; no real PII in MVP."
    )


class ContactData(BaseModel):
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = None


class EmploymentData(BaseModel):
    employment_status: Optional[Literal["employed"]] = None
    employer_name: Optional[str] = None


class IncomeData(BaseModel):
    income_amount: Optional[float] = None
    income_frequency: Optional[Literal["monthly", "annual"]] = None


class AssetAccount(BaseModel):
    account_type: Optional[str] = None
    balance: Optional[float] = None


class AssetsData(BaseModel):
    accounts: list[AssetAccount] = Field(default_factory=list)


class LiabilityDebt(BaseModel):
    debt_type: Optional[str] = None
    monthly_payment: Optional[float] = None


class LiabilitiesData(BaseModel):
    monthly_debts: list[LiabilityDebt] = Field(default_factory=list)


class PropertyData(BaseModel):
    property_status: Optional[Literal["under_contract", "shopping", "refinance"]] = None
    property_value_or_purchase_price: Optional[float] = None
    # Placeholder for later computations.
    estimated_housing_payment: Optional[float] = None


class LoanPurposeData(BaseModel):
    loan_purpose: Optional[Literal["purchase", "refinance"]] = None
    desired_down_payment: Optional[float] = None
    cash_available: Optional[float] = None


class LoanApplicationData(BaseModel):
    identity: IdentityData = Field(default_factory=IdentityData)
    contact: ContactData = Field(default_factory=ContactData)
    employment: EmploymentData = Field(default_factory=EmploymentData)
    income: IncomeData = Field(default_factory=IncomeData)
    assets: AssetsData = Field(default_factory=AssetsData)
    liabilities: LiabilitiesData = Field(default_factory=LiabilitiesData)
    property: PropertyData = Field(default_factory=PropertyData)
    loan_purpose: LoanPurposeData = Field(default_factory=LoanPurposeData)

    class Config:
        extra = "forbid"

