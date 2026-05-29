from __future__ import annotations

import re

from app.services.ocr.base import OcrResult

# Lines like "Employer: Acme Corp" or "Box 1 Wages: 96000.00"
_KV_LINE = re.compile(r"^([^:]+?):\s+(.+?)\s*$")


def analyze(document_bytes: bytes, doc_type_hint: str | None = None) -> OcrResult:
    """
    Local OCR for MVP dev: treat document bytes as UTF-8 text and parse label:value lines.
    Works with synthetic .txt pay stubs, W-2s, and bank statements without AWS Textract.
    """
    text = document_bytes.decode("utf-8", errors="replace")
    key_values: dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("=") or line.startswith("-"):
            continue
        match = _KV_LINE.match(line)
        if match:
            key_values[match.group(1).strip()] = match.group(2).strip()

    return OcrResult(
        text=text,
        key_values=key_values,
        tables=[],
        raw={"source": "local_ocr", "doc_type_hint": doc_type_hint},
    )
