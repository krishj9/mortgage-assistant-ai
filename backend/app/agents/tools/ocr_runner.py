from __future__ import annotations

import logging

from botocore.exceptions import BotoCoreError, ClientError

from app.core.config import settings
from app.services.ocr import local as local_ocr
from app.services.ocr import textract
from app.services.ocr.base import OcrResult

logger = logging.getLogger(__name__)


def run_ocr(document_bytes: bytes, doc_type_hint: str | None = None) -> OcrResult:
    backend = settings.OCR_BACKEND.lower().strip()

    if backend == "local":
        return local_ocr.analyze(document_bytes, doc_type_hint=doc_type_hint)

    if backend == "textract":
        return textract.analyze(document_bytes, doc_type_hint=doc_type_hint)

    # auto: prefer Textract when subscribed; fall back for local dev without Textract.
    try:
        return textract.analyze(document_bytes, doc_type_hint=doc_type_hint)
    except (ClientError, BotoCoreError) as exc:
        logger.warning(
            "Textract unavailable (%s); using local OCR parser for this document.",
            exc,
        )
        return local_ocr.analyze(document_bytes, doc_type_hint=doc_type_hint)
