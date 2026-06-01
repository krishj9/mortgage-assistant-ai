from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PayStubFixture:
    employer: str = "Acme Corp"
    employer_address: str = "100 Market Street, San Francisco, CA 94105"
    employee: str = "Alice Borrower"
    employee_address: str = "42 Demo Lane, San Francisco, CA 94102"
    employee_id: str = "AB-1042"
    pay_date: str = "04/15/2026"
    pay_period: str = "04/01/2026 - 04/15/2026"
    pay_frequency: str = "Bi-Weekly"
    regular_hours: float = 80.00
    hourly_rate: float = 53.85
    gross_pay: float = 8500.00
    federal_tax: float = 1275.00
    state_tax: float = 425.00
    social_security: float = 527.00
    medicare: float = 123.25
    net_pay: float = 6149.75
    ytd_gross: float = 34000.00
    disclaimer: str = "Synthetic document for MVP demo and testing only."


@dataclass(frozen=True)
class W2Fixture:
    tax_year: str = "2025"
    employer_name: str = "Acme Corp"
    employer_ein: str = "12-3456789"
    employer_address: str = "100 Market Street, San Francisco, CA 94105"
    employee_name: str = "Alice Borrower"
    employee_ssn: str = "***-**-1234"
    employee_address: str = "42 Demo Lane, San Francisco, CA 94102"
    box_1_wages: float = 96000.00
    box_2_federal_tax: float = 18240.00
    box_3_ss_wages: float = 96000.00
    box_4_ss_tax: float = 5952.00
    box_5_medicare_wages: float = 96000.00
    box_6_medicare_tax: float = 1392.00
    box_12a_401k: float = 6000.00
    state: str = "CA"
    state_wages: float = 96000.00
    state_income_tax: float = 6720.00
    disclaimer: str = "Synthetic document for MVP demo and testing only."


PAY_STUB = PayStubFixture()
W2 = W2Fixture()

W2_OUTPUT_NAME = "synthetic_w2.pdf"
PAY_STUB_OUTPUT_NAME = "synthetic_pay_stub.pdf"
