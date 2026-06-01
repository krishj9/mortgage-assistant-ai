from __future__ import annotations

import structlog
from sqlalchemy.orm import Session

from app.agents.document_errors import UnsupportedDocumentError
from app.agents.nodes.document_understanding_agent import run_document_understanding
from app.db.session import SessionLocal
from app.models.document import ExtractionStatus
from app.models.document_extraction import DocumentExtraction
from app.services import document_event_hub, documents_service

logger = structlog.get_logger()


def _publish(document_id: int, **kwargs) -> None:
    document_event_hub.publish(document_id, document_event_hub.build_event(document_id, **kwargs))


def run_document_pipeline(document_id: int) -> None:
    db: Session = SessionLocal()
    try:
        doc = documents_service.get_document(db, document_id)
        if doc is None:
            return

        doc.extraction_status = ExtractionStatus.running.value
        db.commit()
        _publish(document_id, status="running", stage="queued")

        content = documents_service.load_document_bytes(doc)

        def on_stage(stage: str) -> None:
            _publish(document_id, status="running", stage=stage)

        predicted_type, confidence, ocr, normalized, field_confidence = run_document_understanding(
            document_bytes=content,
            filename=doc.original_filename,
            document_id=doc.id,
            on_stage=on_stage,
        )

        _publish(document_id, status="running", stage="merging")

        doc.predicted_type = predicted_type
        doc.classification_confidence = confidence
        doc.extraction_status = ExtractionStatus.succeeded.value

        extraction = documents_service.get_extraction(db, doc.id)
        if extraction is None:
            extraction = DocumentExtraction(document_id=doc.id)
            db.add(extraction)

        extraction.raw_ocr = {
            **ocr.raw,
            "text": ocr.text,
            "key_values": ocr.key_values,
        }
        extraction.normalized = normalized
        extraction.confidence = field_confidence
        extraction.status = "succeeded"

        db.commit()
        documents_service.merge_into_deal_context(db, deal_id=doc.deal_id, normalized=normalized)

        _publish(
            document_id,
            status="succeeded",
            predicted_type=predicted_type,
            classification_confidence=confidence,
        )

        logger.info(
            "document_extracted",
            document_id=document_id,
            deal_id=doc.deal_id,
            predicted_type=predicted_type,
        )
    except UnsupportedDocumentError as exc:
        db.rollback()
        _handle_failure(db, document_id, str(exc))
    except Exception as exc:
        db.rollback()
        _handle_failure(db, document_id, str(exc))
        logger.exception("document_extraction_failed", document_id=document_id, error=str(exc))
    finally:
        db.close()


def _handle_failure(db: Session, document_id: int, error: str) -> None:
    doc = documents_service.get_document(db, document_id)
    if doc is not None:
        doc.extraction_status = ExtractionStatus.failed.value
        db.commit()
    _publish(document_id, status="failed", error=error)
