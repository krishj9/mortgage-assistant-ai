from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.tools.extraction_mapper import map_extraction
from app.agents.tools.ocr_runner import run_ocr
from app.models.document import DocumentType
from app.schemas.agent_io import DocumentClassification
from app.services.bedrock.client import get_structured_model
from app.services.ocr.base import OcrResult

# Below this deterministic confidence, defer to the LLM classifier.
_LLM_CLASSIFY_THRESHOLD = 0.75

_DOC_CLASSIFY_PROMPT = (
    "You classify mortgage documents. Given a filename and OCR text, return the most "
    "likely document type and a confidence between 0 and 1."
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
    if "1003" in name or "application" in name:
        return DocumentType.application_1003.value, 0.8
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
        result = model.invoke(
            [SystemMessage(content=_DOC_CLASSIFY_PROMPT), HumanMessage(content=human)]
        )
        if isinstance(result, DocumentClassification):
            return result.predicted_type, float(result.confidence)
    except Exception:
        pass
    return None


def run_document_understanding(
    document_bytes: bytes,
    filename: str,
    document_id: int,
    doc_type_hint: str | None = None,
) -> tuple[str, float, OcrResult, dict, dict]:
    ocr = run_ocr(document_bytes, doc_type_hint=doc_type_hint)
    predicted_type, confidence = classify_document(filename, ocr.text)
    if doc_type_hint:
        predicted_type = doc_type_hint
        confidence = max(confidence, 0.8)
    elif confidence < _LLM_CLASSIFY_THRESHOLD:
        llm_result = _llm_classify_document(filename, ocr.text)
        if llm_result and llm_result[1] > confidence:
            predicted_type, confidence = llm_result
    normalized = map_extraction(predicted_type, ocr, document_id)
    field_confidence = {k: confidence for k in normalized.keys()}
    return predicted_type, confidence, ocr, normalized, field_confidence
