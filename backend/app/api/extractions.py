from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.schemas.deal_context import ExtractionPatch
from app.services import documents_service


router = APIRouter(prefix="/documents", tags=["extractions"])


@router.get("/{document_id}/extraction")
def get_document_extraction(
    document_id: int,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    extraction = documents_service.get_extraction(db, document_id)
    if extraction is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Extraction not found")
    return {
        "id": extraction.id,
        "document_id": extraction.document_id,
        "raw_ocr": extraction.raw_ocr,
        "normalized": extraction.normalized,
        "confidence": extraction.confidence,
        "human_corrections": extraction.human_corrections,
        "status": extraction.status,
    }


@router.put("/{document_id}/extraction")
def update_document_extraction(
    document_id: int,
    payload: ExtractionPatch,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    doc = documents_service.get_document(db, document_id)
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    extraction = documents_service.get_extraction(db, document_id)
    if extraction is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Extraction not found")

    extraction.human_corrections = payload.human_corrections
    db.commit()

    merged = {**extraction.normalized, **payload.human_corrections}
    documents_service.apply_human_corrections_to_deal_context(db, deal_id=doc.deal_id, corrections=merged)
    db.refresh(extraction)

    return {
        "id": extraction.id,
        "document_id": extraction.document_id,
        "normalized": extraction.normalized,
        "human_corrections": extraction.human_corrections,
        "status": extraction.status,
    }
