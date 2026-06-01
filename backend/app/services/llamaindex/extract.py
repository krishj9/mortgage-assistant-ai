from __future__ import annotations

from typing import Any, Literal

from app.core.config import settings
from app.schemas.llamaindex_income import BankStatementExtraction, PayStubExtraction, W2Extraction
from app.services.llamaindex.client import LlamaIndexError, get_client, wait_for_job

_DOC_SCHEMAS = {
    "pay_stub": PayStubExtraction,
    "w2": W2Extraction,
    "bank_statement": BankStatementExtraction,
}

SupportedDocType = Literal["pay_stub", "w2", "bank_statement"]


def extract_structured(parse_job_id: str, doc_type: SupportedDocType) -> dict[str, Any]:
    schema_model = _DOC_SCHEMAS[doc_type]
    client = get_client()
    tier = settings.LLAMA_EXTRACT_TIER

    job = client.extract.create(
        file_input=parse_job_id,
        configuration={
            "data_schema": schema_model.model_json_schema(),
            "extraction_target": "per_doc",
            "tier": tier,
        },
    )

    completed = wait_for_job(
        job,
        get_job=lambda job_id: client.extract.get(job_id),
        job_kind="extract",
    )

    if completed.extract_result is None:
        raise LlamaIndexError(f"LlamaExtract job {completed.id} returned no extract_result")

    if isinstance(completed.extract_result, dict):
        return completed.extract_result
    if isinstance(completed.extract_result, list) and completed.extract_result:
        first = completed.extract_result[0]
        if isinstance(first, dict):
            return first

    raise LlamaIndexError(f"LlamaExtract job {completed.id} returned unexpected result shape")


def extract_income(parse_job_id: str, doc_type: Literal["pay_stub", "w2"]) -> dict[str, Any]:
    """Backward-compatible alias for income document types."""
    return extract_structured(parse_job_id, doc_type)  # type: ignore[arg-type]
