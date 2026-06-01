from __future__ import annotations

import argparse
from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from fixture_data import PAY_STUB, W2, PAY_STUB_OUTPUT_NAME, W2_OUTPUT_NAME


def _fmt_currency(amount: float) -> str:
    return f"${amount:,.2f}"


def generate_w2_pdf(path: Path, data=W2) -> None:
    c = canvas.Canvas(str(path), pagesize=letter)

    c.setTitle(f"Sample W-2 {data.tax_year}")
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, 750, f"Form W-2 Wage and Tax Statement {data.tax_year}")

    c.setFont("Helvetica", 10)
    c.drawString(50, 710, f"a Employee's social security number: {data.employee_ssn}")
    c.drawString(50, 680, f"b Employer identification number (EIN): {data.employer_ein}")
    c.drawString(50, 650, "c Employer's name, address, and ZIP code:")
    c.drawString(60, 635, f"Employer Name: {data.employer_name}")
    c.drawString(60, 620, data.employer_address)

    c.drawString(50, 570, f"e Employee's name: {data.employee_name}")
    c.drawString(50, 540, "f Employee's address and ZIP code:")
    c.drawString(60, 525, data.employee_address)

    c.drawString(350, 710, f"1 Wages, tips, other comp: {_fmt_currency(data.box_1_wages)}")
    c.drawString(350, 680, f"2 Federal income tax withheld: {_fmt_currency(data.box_2_federal_tax)}")
    c.drawString(350, 650, f"3 Social security wages: {_fmt_currency(data.box_3_ss_wages)}")
    c.drawString(350, 620, f"4 Social security tax withheld: {_fmt_currency(data.box_4_ss_tax)}")
    c.drawString(350, 590, f"5 Medicare wages and tips: {_fmt_currency(data.box_5_medicare_wages)}")
    c.drawString(350, 560, f"6 Medicare tax withheld: {_fmt_currency(data.box_6_medicare_tax)}")
    c.drawString(350, 530, f"12a Code D — 401(k): {_fmt_currency(data.box_12a_401k)}")
    c.drawString(350, 500, f"16 State wages, tips, etc: {_fmt_currency(data.state_wages)}")
    c.drawString(350, 470, f"17 State income tax: {_fmt_currency(data.state_income_tax)}")
    c.drawString(350, 440, f"State: {data.state}")

    c.rect(40, 420, 520, 320)
    c.line(340, 420, 340, 740)
    c.line(40, 670, 560, 670)
    c.line(40, 610, 340, 610)
    c.line(40, 530, 340, 530)
    c.line(340, 700, 560, 700)
    c.line(340, 640, 560, 640)
    c.line(340, 580, 560, 580)
    c.line(340, 520, 560, 520)
    c.line(340, 460, 560, 460)

    c.setFont("Helvetica-Oblique", 8)
    c.drawString(50, 400, data.disclaimer)

    c.save()


def generate_paystub_pdf(path: Path, data=PAY_STUB) -> None:
    c = canvas.Canvas(str(path), pagesize=letter)

    c.setTitle("Sample Pay Stub")
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, 750, "EARNINGS STATEMENT (PAY STUB)")

    c.setFont("Helvetica", 10)
    c.drawString(50, 710, f"Employer: {data.employer}, {data.employer_address}")
    c.drawString(50, 690, f"Employee: {data.employee}, {data.employee_address}")
    c.drawString(50, 670, f"Employee ID: {data.employee_id}")

    c.drawString(350, 710, f"Pay Period: {data.pay_period}")
    c.drawString(350, 690, f"Pay Date: {data.pay_date}")
    c.drawString(350, 670, f"Pay Frequency: {data.pay_frequency}")

    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, 630, "Earnings")
    c.setFont("Helvetica", 10)
    c.drawString(50, 610, "Description       Rate        Hours      Current        YTD")
    c.drawString(
        50,
        590,
        f"Regular           {_fmt_currency(data.hourly_rate):>10}  "
        f"{data.regular_hours:>6.2f}  {_fmt_currency(data.gross_pay):>12}  "
        f"{_fmt_currency(data.ytd_gross):>12}",
    )
    c.line(50, 605, 400, 605)

    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, 530, "Taxes")
    c.setFont("Helvetica", 10)
    c.drawString(50, 510, "Description       Current        YTD")
    c.drawString(50, 490, f"Federal Tax       {_fmt_currency(data.federal_tax):>12}")
    c.drawString(50, 470, f"Social Security   {_fmt_currency(data.social_security):>12}")
    c.drawString(50, 450, f"Medicare          {_fmt_currency(data.medicare):>12}")
    c.drawString(50, 430, f"State Tax         {_fmt_currency(data.state_tax):>12}")
    c.line(50, 505, 300, 505)

    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, 380, "Totals")
    c.setFont("Helvetica", 10)
    c.drawString(50, 360, f"Gross Pay: {_fmt_currency(data.gross_pay)}")
    total_taxes = data.federal_tax + data.state_tax + data.social_security + data.medicare
    c.drawString(250, 360, f"Taxes: {_fmt_currency(total_taxes)}")

    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, 320, f"NET PAY: {_fmt_currency(data.net_pay)}")
    c.drawString(50, 295, f"YTD GROSS: {_fmt_currency(data.ytd_gross)}")

    c.setFont("Helvetica-Oblique", 8)
    c.drawString(50, 270, data.disclaimer)

    c.save()


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate synthetic W-2 and pay stub PDFs")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parent / "output",
        help="Directory for generated PDFs (default: ./output)",
    )
    parser.add_argument("--w2-only", action="store_true", help="Generate W-2 only")
    parser.add_argument("--paystub-only", action="store_true", help="Generate pay stub only")
    args = parser.parse_args()

    if args.w2_only and args.paystub_only:
        parser.error("Use at most one of --w2-only and --paystub-only")

    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    written: list[Path] = []
    generate_w2 = not args.paystub_only
    generate_paystub = not args.w2_only

    if generate_w2:
        w2_path = output_dir / W2_OUTPUT_NAME
        generate_w2_pdf(w2_path)
        written.append(w2_path)

    if generate_paystub:
        paystub_path = output_dir / PAY_STUB_OUTPUT_NAME
        generate_paystub_pdf(paystub_path)
        written.append(paystub_path)

    for path in written:
        size = path.stat().st_size
        print(f"Generated {path} ({size:,} bytes)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
