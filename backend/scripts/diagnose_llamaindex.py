from __future__ import annotations

"""
Verify LlamaCloud Parse + Extract for income documents.

Usage (from backend/):
  uv run python -m scripts.diagnose_llamaindex
  uv run python -m scripts.diagnose_llamaindex --file ../samples/synthetic_pay_stub.txt
"""

import argparse
import sys
from pathlib import Path

from app.core.config import settings
from app.services.llamaindex.client import LlamaIndexError, get_client
from app.services.llamaindex.extract import extract_income
from app.services.llamaindex.income_mapper import map_income_extraction
from app.services.llamaindex.parse import parse_document


def main() -> int:
    parser = argparse.ArgumentParser(description="Diagnose LlamaCloud Parse + Extract connectivity")
    parser.add_argument(
        "--file",
        default="../samples/synthetic_pay_stub.txt",
        help="Sample pay stub or W-2 file to parse and extract",
    )
    args = parser.parse_args()

    print(f"INCOME_DOC_PARSER={settings.INCOME_DOC_PARSER!r}")
    print(f"effective_income_doc_parser={settings.effective_income_doc_parser()!r}")
    print(f"LLAMA_PARSE_TIER={settings.LLAMA_PARSE_TIER!r}")
    print(f"LLAMA_EXTRACT_TIER={settings.LLAMA_EXTRACT_TIER!r}")
    print()

    if not settings.LLAMA_CLOUD_API_KEY.strip():
        print("LLAMA_CLOUD_API_KEY is not set.")
        print("Add LLAMA_CLOUD_API_KEY or LlamaIndex_API_KEY to backend/.env")
        return 1

    sample_path = Path(args.file)
    if not sample_path.is_file():
        print(f"Sample file not found: {sample_path.resolve()}")
        return 1

    content = sample_path.read_bytes()
    filename = sample_path.name
    doc_type = "w2" if "w2" in filename.lower() or "w-2" in filename.lower() else "pay_stub"

    try:
        get_client()
        print("LlamaCloud client initialized.")
        print(f"Parsing {sample_path.name} ({len(content)} bytes)...")
        parsed = parse_document(content, filename)
        print(f"  Parse OK — job_id={parsed.parse_job_id}, text_chars={len(parsed.text)}")

        print(f"Extracting structured {doc_type} fields from parse job...")
        extracted = extract_income(parsed.parse_job_id, doc_type)  # type: ignore[arg-type]
        normalized = map_income_extraction(doc_type, extracted, document_id=0)  # type: ignore[arg-type]
        print("  Extract OK:")
        print(f"    raw: {extracted}")
        print(f"    normalized: {normalized}")
        return 0
    except LlamaIndexError as exc:
        print(f"FAILED — {exc}")
        return 1
    except Exception as exc:
        print(f"FAILED — unexpected error: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
