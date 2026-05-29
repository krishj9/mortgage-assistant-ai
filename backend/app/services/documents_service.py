from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.deal_context import DealContext
from app.models.document import Document, ExtractionStatus
from app.models.document_extraction import DocumentExtraction
from app.services.storage import get_storage


def _storage_key(deal_id: int, filename: str) -> str:
    safe_name = filename.replace("/", "_")
    return f"deals/{deal_id}/{uuid.uuid4().hex}_{safe_name}"


def create_document(
    db: Session,
    deal_id: int,
    filename: str,
    mime_type: str,
    content: bytes,
) -> Document:
    storage = get_storage()
    key = _storage_key(deal_id, filename)
    uri = storage.put(key, content, mime_type)
    doc = Document(
        deal_id=deal_id,
        storage_uri=uri,
        original_filename=filename,
        mime_type=mime_type,
        extraction_status=ExtractionStatus.pending.value,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


def get_document(db: Session, document_id: int) -> Document | None:
    return db.execute(select(Document).where(Document.id == document_id)).scalar_one_or_none()


def list_documents(db: Session, deal_id: int) -> list[Document]:
    return list(
        db.execute(select(Document).where(Document.deal_id == deal_id).order_by(Document.id.asc())).scalars().all()
    )


def load_document_bytes(doc: Document) -> bytes:
    storage = get_storage()
    if doc.storage_uri.startswith("local://"):
        key = doc.storage_uri.removeprefix("local://")
    elif doc.storage_uri.startswith("s3://"):
        key = doc.storage_uri.split("/", 3)[-1]
    else:
        key = doc.storage_uri
    return storage.get(key)


def merge_into_deal_context(db: Session, deal_id: int, normalized: dict[str, Any]) -> None:
    ctx = db.execute(select(DealContext).where(DealContext.deal_id == deal_id)).scalar_one()
    income_state = dict(ctx.extracted_income or {})
    assets_state = dict(ctx.extracted_assets or {})

    income_records = list(income_state.get("records", []))
    asset_records = list(assets_state.get("records", []))
    applicant_metadata = dict(income_state.get("applicant_metadata", {}))

    if normalized.get("income"):
        income_records.extend(normalized["income"])
    if normalized.get("assets"):
        asset_records.extend(normalized["assets"])
    if normalized.get("metadata"):
        applicant_metadata.update(normalized["metadata"])

    ctx.extracted_income = {"records": income_records, "applicant_metadata": applicant_metadata}
    ctx.extracted_assets = {"records": asset_records}
    db.commit()


def apply_human_corrections_to_deal_context(db: Session, deal_id: int, corrections: dict[str, Any]) -> None:
    ctx = db.execute(select(DealContext).where(DealContext.deal_id == deal_id)).scalar_one()
    if "income" in corrections:
        ctx.extracted_income = corrections["income"]
    if "assets" in corrections:
        ctx.extracted_assets = corrections["assets"]
    db.commit()


def get_extraction(db: Session, document_id: int) -> DocumentExtraction | None:
    return db.execute(
        select(DocumentExtraction).where(DocumentExtraction.document_id == document_id)
    ).scalar_one_or_none()
