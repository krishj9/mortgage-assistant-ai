from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


class PayStubExtraction(BaseModel):
    employer: Optional[str] = Field(default=None, description="Employer or company name")
    employee_name: Optional[str] = Field(default=None, description="Employee full name")
    gross_pay: Optional[float] = Field(
        default=None, description="Gross pay for the pay period (numeric, no currency symbol)"
    )
    net_pay: Optional[float] = Field(
        default=None, description="Net pay after deductions (numeric, no currency symbol)"
    )
    pay_frequency: Optional[str] = Field(
        default=None,
        description="Pay frequency such as weekly, bi-weekly, semi-monthly, or monthly",
    )
    pay_period_start: Optional[str] = Field(default=None, description="Pay period start date")
    pay_period_end: Optional[str] = Field(default=None, description="Pay period end date")
    ytd_gross: Optional[float] = Field(
        default=None, description="Year-to-date gross earnings (numeric, no currency symbol)"
    )


class W2Extraction(BaseModel):
    employer_name: Optional[str] = Field(default=None, description="Employer name from Form W-2")
    employee_name: Optional[str] = Field(default=None, description="Employee name from Form W-2")
    box_1_wages: Optional[float] = Field(
        default=None,
        description="Box 1 wages, tips, and other compensation (numeric, no currency symbol)",
    )
    tax_year: Optional[str] = Field(default=None, description="Tax year of the W-2 form")
    employer_ein: Optional[str] = Field(default=None, description="Employer EIN if present")


class BankStatementExtraction(BaseModel):
    bank_name: Optional[str] = Field(default=None, description="Name of the financial institution")
    account_type: Optional[str] = Field(
        default=None, description="Account type such as checking or savings"
    )
    ending_balance: Optional[float] = Field(
        default=None, description="Ending balance on the statement (numeric, no currency symbol)"
    )
    average_balance: Optional[float] = Field(
        default=None, description="Average balance if shown (numeric, no currency symbol)"
    )
    statement_period_start: Optional[str] = Field(default=None, description="Statement period start date")
    statement_period_end: Optional[str] = Field(default=None, description="Statement period end date")
