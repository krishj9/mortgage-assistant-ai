from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from llama_cloud.types.parsing_get_response import ParsingGetResponse

from app.core.config import settings
from app.services.llamaindex.client import (
    LlamaIndexError,
    get_client,
    get_job_id,
    get_job_status,
    wait_for_job,
)
from app.services.ocr.base import OcrResult

_KV_LINE = re.compile(r"^([^:]+?):\s+(.+?)\s*$")


@dataclass
class ParseResult:
    text: str
    parse_job_id: str
    key_values: dict[str, str] = field(default_factory=dict)
    raw: dict[str, Any] = field(default_factory=dict)


def _extract_parsed_text(response: ParsingGetResponse) -> str:
    if response.text_full:
        return response.text_full
    if response.text and response.text.pages:
        return "\n".join(page.text for page in response.text.pages if page.text)
    if response.markdown_full:
        return response.markdown_full
    if response.markdown and response.markdown.pages:
        parts: list[str] = []
        for page in response.markdown.pages:
            markdown = getattr(page, "markdown", None)
            if markdown:
                parts.append(markdown)
        if parts:
            return "\n".join(parts)
    return ""


def _derive_key_values(text: str) -> dict[str, str]:
    key_values: dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("=") or line.startswith("-"):
            continue
        match = _KV_LINE.match(line)
        if match:
            key_values[match.group(1).strip()] = match.group(2).strip()
    return key_values


def parse_document(
    document_bytes: bytes,
    filename: str,
    *,
    document_id: int | None = None,
) -> ParseResult:
    client = get_client()
    tier = settings.LLAMA_PARSE_TIER

    parse_job = client.parsing.create(
        tier=tier,  # type: ignore[arg-type]
        version="latest",
        upload_file=(filename, document_bytes),
    )

    completed = wait_for_job(
        parse_job,
        get_job=lambda job_id: client.parsing.get(job_id),
        job_kind="parse",
        document_id=document_id,
    )

    parse_job_id = get_job_id(completed)
    result = client.parsing.get(parse_job_id, expand=["text", "markdown"])
    text = _extract_parsed_text(result)
    if not text.strip():
        raise LlamaIndexError(f"LlamaParse job {parse_job_id} returned empty text")

    key_values = _derive_key_values(text)
    return ParseResult(
        text=text,
        parse_job_id=parse_job_id,
        key_values=key_values,
        raw={
            "source": "llamaparse",
            "parse_job_id": parse_job_id,
            "tier": tier,
            "status": get_job_status(completed),
        },
    )


def parse_result_to_ocr(parsed: ParseResult) -> OcrResult:
    return OcrResult(
        text=parsed.text,
        key_values=dict(parsed.key_values),
        tables=[],
        raw=dict(parsed.raw),
    )
