from __future__ import annotations

from typing import Callable

from app.agents.document_errors import UnsupportedDocumentError
from app.agents.tools.extraction_mapper import map_extraction
from app.agents.tools.ocr_runner import run_ocr
from app.core.config import settings
from app.models.document import DocumentType
from app.schemas.agent_io import DocumentClassification
from app.services.bedrock.client import get_structured_model, invoke_structured
from app.services.llamaindex.client import LlamaIndexError
from app.services.llamaindex.document_mapper import map_document_extraction
from app.services.llamaindex.extract import extract_structured
from app.services.llamaindex.parse import parse_document, parse_result_to_ocr
from app.services.ocr.base import OcrResult
from langchain_core.messages import HumanMessage, SystemMessage

SUPPORTED_DOC_TYPES = frozenset(
    {
        DocumentType.pay_stub.value,
        DocumentType.w2.value,
        DocumentType.bank_statement.value,
    }
)

_LLM_CLASSIFY_THRESHOLD = 0.75

_DOC_CLASSIFY_PROMPT = (
    "You classify mortgage documents. Given a filename and OCR text, return the most "
    "likely document type: pay_stub, w2, or bank_statement only."
)


def classify_document(filename: str, ocr_text: str) -> tuple[str, float]:
    name = filename.lower()
    text = ocr_text.lower()
    if "pay" in name and "stub" in name:
        return DocumentType.pay_stub.value, 0.9
    if "w2" in name or "w-2" in name:
        return DocumentType.w2.value, 0.9
    if "bank" in name or "statement" in name:
        return DocumentType.bank_statement.value, 0.85
    if "pay stub" in text or "gross pay" in text:
        return DocumentType.pay_stub.value, 0.75
    if "w-2" in text or "wages" in text:
        return DocumentType.w2.value, 0.75
    if "ending balance" in text or "account number" in text:
        return DocumentType.bank_statement.value, 0.75
    return DocumentType.unknown.value, 0.4


def _llm_classify_document(filename: str, ocr_text: str) -> tuple[str, float] | None:
    try:
        model = get_structured_model(DocumentClassification, tags=["document_understanding"])
        human = (
            f"Filename: {filename}\n\n"
            f"OCR text (truncated):\n\"\"\"{ocr_text[:2000]}\"\"\""
        )
        result = invoke_structured(
            model,
            [SystemMessage(content=_DOC_CLASSIFY_PROMPT), HumanMessage(content=human)],
            tags=["document_understanding"],
        )
        if isinstance(result, DocumentClassification):
            return result.predicted_type, float(result.confidence)
    except Exception:
        pass
    return None


def _classify_with_optional_llm(
    filename: str,
    ocr_text: str,
    doc_type_hint: str | None,
) -> tuple[str, float]:
    predicted_type, confidence = classify_document(filename, ocr_text)
    if doc_type_hint:
        predicted_type = doc_type_hint
        confidence = max(confidence, 0.8)
    elif confidence < _LLM_CLASSIFY_THRESHOLD:
        llm_result = _llm_classify_document(filename, ocr_text)
        if llm_result and llm_result[1] > confidence:
            predicted_type, confidence = llm_result
    return predicted_type, confidence


def _ensure_supported_type(predicted_type: str) -> None:
    if predicted_type not in SUPPORTED_DOC_TYPES:
        raise UnsupportedDocumentError(
            "Only pay stubs, W-2s, and bank statements are accepted."
        )


def _run_textract_understanding(
    document_bytes: bytes,
    filename: str,
    document_id: int,
    doc_type_hint: str | None,
    on_stage: Callable[[str], None] | None,
) -> tuple[str, float, OcrResult, dict, dict]:
    if on_stage:
        on_stage("parsing")
    ocr = run_ocr(document_bytes, doc_type_hint=doc_type_hint)
    if on_stage:
        on_stage("classifying")
    predicted_type, confidence = _classify_with_optional_llm(filename, ocr.text, doc_type_hint)
    _ensure_supported_type(predicted_type)
    if on_stage:
        on_stage("extracting")
    normalized = map_extraction(predicted_type, ocr, document_id)
    field_confidence = {k: confidence for k in normalized.keys()}
    return predicted_type, confidence, ocr, normalized, field_confidence


def _run_llamaindex_understanding(
    document_bytes: bytes,
    filename: str,
    document_id: int,
    doc_type_hint: str | None,
    on_stage: Callable[[str], None] | None,
) -> tuple[str, float, OcrResult, dict, dict]:
    try:
        settings.require_llama_cloud_key()
    except ValueError as exc:
        raise UnsupportedDocumentError(str(exc)) from exc

    if on_stage:
        on_stage("parsing")
    parsed = parse_document(document_bytes, filename, document_id=document_id)
    ocr = parse_result_to_ocr(parsed)

    if on_stage:
        on_stage("classifying")
    predicted_type, confidence = _classify_with_optional_llm(filename, ocr.text, doc_type_hint)
    _ensure_supported_type(predicted_type)

    if on_stage:
        on_stage("extracting")
    extracted = extract_structured(parsed.parse_job_id, predicted_type)  # type: ignore[arg-type]
    ocr.raw["extract_job_input"] = parsed.parse_job_id
    normalized = map_document_extraction(predicted_type, extracted, document_id)  # type: ignore[arg-type]

    field_confidence = {k: confidence for k in normalized.keys()}
    return predicted_type, confidence, ocr, normalized, field_confidence


def run_document_understanding(
    document_bytes: bytes,
    filename: str,
    document_id: int,
    doc_type_hint: str | None = None,
    on_stage: Callable[[str], None] | None = None,
) -> tuple[str, float, OcrResult, dict, dict]:
    if settings.effective_document_parser() == "textract":
        return _run_textract_understanding(
            document_bytes, filename, document_id, doc_type_hint, on_stage
        )

    try:
        return _run_llamaindex_understanding(
            document_bytes, filename, document_id, doc_type_hint, on_stage
        )
    except LlamaIndexError as exc:
        raise UnsupportedDocumentError(str(exc)) from exc
