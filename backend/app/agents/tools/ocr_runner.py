from __future__ import annotations

import logging

from botocore.exceptions import BotoCoreError, ClientError

from app.core.config import settings
from app.services.ocr import local as local_ocr
from app.services.ocr import textract
from app.services.ocr.base import OcrResult

logger = logging.getLogger(__name__)


def run_ocr(document_bytes: bytes, doc_type_hint: str | None = None) -> OcrResult:
    """Textract-only OCR used when DOCUMENT_PARSER=textract."""
    try:
        return textract.analyze(document_bytes, doc_type_hint=doc_type_hint)
    except (ClientError, BotoCoreError) as exc:
        logger.warning(
            "Textract unavailable (%s); falling back to local text parser for dev fixtures.",
            exc,
        )
        return local_ocr.analyze(document_bytes, doc_type_hint=doc_type_hint)
