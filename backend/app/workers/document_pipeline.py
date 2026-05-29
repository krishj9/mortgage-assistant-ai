from __future__ import annotations

import structlog

from sqlalchemy.orm import Session

from app.agents.nodes.document_understanding_agent import run_document_understanding
from app.db.session import SessionLocal
from app.models.document import ExtractionStatus
from app.models.document_extraction import DocumentExtraction
from app.services import documents_service

logger = structlog.get_logger()


def run_document_pipeline(document_id: int) -> None:
    db: Session = SessionLocal()
    try:
        doc = documents_service.get_document(db, document_id)
        if doc is None:
            return

        doc.extraction_status = ExtractionStatus.running.value
        db.commit()

        content = documents_service.load_document_bytes(doc)
        predicted_type, confidence, ocr, normalized, field_confidence = run_document_understanding(
            document_bytes=content,
            filename=doc.original_filename,
            document_id=doc.id,
        )

        doc.predicted_type = predicted_type
        doc.classification_confidence = confidence
        doc.extraction_status = ExtractionStatus.succeeded.value

        extraction = documents_service.get_extraction(db, doc.id)
        if extraction is None:
            extraction = DocumentExtraction(document_id=doc.id)
            db.add(extraction)

        extraction.raw_ocr = ocr.raw
        extraction.normalized = normalized
        extraction.confidence = field_confidence
        extraction.status = "succeeded"

        db.commit()
        documents_service.merge_into_deal_context(db, deal_id=doc.deal_id, normalized=normalized)

        logger.info(
            "document_extracted",
            document_id=document_id,
            deal_id=doc.deal_id,
            predicted_type=predicted_type,
        )
    except Exception as exc:
        db.rollback()
        doc = documents_service.get_document(db, document_id)
        if doc is not None:
            doc.extraction_status = ExtractionStatus.failed.value
            db.commit()
        logger.exception("document_extraction_failed", document_id=document_id, error=str(exc))
    finally:
        db.close()
