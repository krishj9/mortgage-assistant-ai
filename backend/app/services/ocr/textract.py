from __future__ import annotations

import boto3

from app.core.config import settings
from app.models.document import DocumentType
from app.services.ocr.base import OcrResult


def _parse_blocks(blocks: list[dict]) -> OcrResult:
    lines: list[str] = []
    key_values: dict[str, str] = {}
    for block in blocks:
        if block.get("BlockType") == "LINE" and "Text" in block:
            lines.append(block["Text"])
        if block.get("BlockType") == "KEY_VALUE_SET" and block.get("EntityTypes") == ["KEY"]:
            key_text = block.get("Text")
            if key_text:
                key_values[key_text] = key_text
    return OcrResult(text="\n".join(lines), key_values=key_values, tables=[], raw={"blocks": blocks})


def analyze(document_bytes: bytes, doc_type_hint: str | None = None) -> OcrResult:
    client = boto3.client("textract", region_name=settings.TEXTRACT_REGION)
    if doc_type_hint == DocumentType.bank_statement.value:
        response = client.analyze_expense(Document={"Bytes": document_bytes})
        summary = response.get("ExpenseDocuments", [{}])[0]
        text_parts = []
        for field in summary.get("SummaryFields", []):
            label = (field.get("LabelDetection") or {}).get("Text")
            value = (field.get("ValueDetection") or {}).get("Text")
            if label and value:
                text_parts.append(f"{label}: {value}")
        return OcrResult(
            text="\n".join(text_parts),
            key_values={p.split(":")[0]: p.split(":", 1)[1].strip() for p in text_parts if ":" in p},
            tables=[],
            raw=response,
        )

    response = client.analyze_document(
        Document={"Bytes": document_bytes},
        FeatureTypes=["FORMS", "TABLES"],
    )
    return _parse_blocks(response.get("Blocks", []))
