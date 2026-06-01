# Synthetic PDF Generator

Standalone tool that generates **W-2** and **pay stub** PDFs for manual upload testing. Field values match the committed text fixtures in [`samples/`](../../samples/) (Alice Borrower, Acme Corp, etc.).

Generated PDFs are written to `output/` (gitignored).

## Setup

```bash
cd tools/synthetic-pdf-generator
uv sync
```

## Generate

```bash
uv run python generate.py
```

Options:

| Flag | Description |
|------|-------------|
| `--output-dir PATH` | Output directory (default: `./output`) |
| `--w2-only` | Generate W-2 only |
| `--paystub-only` | Generate pay stub only |

Output files:

- `output/synthetic_w2.pdf`
- `output/synthetic_pay_stub.pdf`

## Use with the app

### Borrower portal

1. Start backend and frontend (see root [README](../../README.md)).
2. Log in as borrower (deal 1, `alice@example.com`).
3. Upload `output/synthetic_pay_stub.pdf` and/or `output/synthetic_w2.pdf` during the documents phase.
4. In the LO console, confirm `raw_ocr.text` contains parsed content and `normalized.income` has employer and gross pay.

The borrower UI receives processing updates via **SSE** (`GET /documents/{id}/events`), not polling.

### Diagnose LlamaCloud

```bash
cd ../../backend
uv run python -m scripts.diagnose_llamaindex \
  --file ../tools/synthetic-pdf-generator/output/synthetic_pay_stub.pdf
```

## Fixture alignment

Data is defined in [`fixture_data.py`](fixture_data.py) and mirrors:

- [`samples/synthetic_pay_stub.txt`](../../samples/synthetic_pay_stub.txt) — gross **$8,500.00**, bi-weekly
- [`samples/synthetic_w2.txt`](../../samples/synthetic_w2.txt) — Box 1 **$96,000.00**

Use filenames containing `pay_stub` or `w2` so the document classifier routes them correctly.
