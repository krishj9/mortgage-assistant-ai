from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import Response, StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import get_borrower_session, get_current_user, get_db
from app.core.security import verify_borrower_session, verify_token
from app.models.document import ExtractionStatus
from app.services import document_event_hub, documents_service
from app.workers.document_pipeline import run_document_pipeline
from fastapi.security import OAuth2PasswordBearer


router = APIRouter(prefix="/documents", tags=["documents"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/staff/login", auto_error=False)

_TERMINAL_STATUSES = frozenset(
    {ExtractionStatus.succeeded.value, ExtractionStatus.failed.value}
)
_SSE_HEARTBEAT_SEC = 15.0


def _document_to_dict(doc) -> dict:
    return {
        "id": doc.id,
        "deal_id": doc.deal_id,
        "original_filename": doc.original_filename,
        "mime_type": doc.mime_type,
        "predicted_type": doc.predicted_type,
        "classification_confidence": doc.classification_confidence,
        "extraction_status": doc.extraction_status,
    }


def _verify_document_access(doc, token: str) -> None:
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        payload = verify_token(token)
        if payload.get("type") == "staff":
            return
        _, deal_id = verify_borrower_session(token)
        if int(doc.deal_id) != int(deal_id):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Deal access denied")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc


def _event_from_doc(doc) -> dict:
    error = None
    if doc.extraction_status == ExtractionStatus.failed.value:
        error = "Document processing failed."
    return document_event_hub.build_event(
        doc.id,
        status=doc.extraction_status,
        predicted_type=doc.predicted_type,
        classification_confidence=doc.classification_confidence,
        error=error,
    )


def _format_sse(event: dict) -> str:
    return f"data: {json.dumps(event)}\n\n"


@router.post("", status_code=status.HTTP_201_CREATED)
def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    borrower_session: dict = Depends(get_borrower_session),
):
    deal_id = int(borrower_session["deal_id"])
    content = file.file.read()
    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty file")

    doc = documents_service.create_document(
        db=db,
        deal_id=deal_id,
        filename=file.filename or "upload.bin",
        mime_type=file.content_type or "application/octet-stream",
        content=content,
    )
    background_tasks.add_task(run_document_pipeline, doc.id)
    return _document_to_dict(doc)


@router.get("")
def list_documents(
    deal_id: int = Query(...),
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    docs = documents_service.list_documents(db, deal_id=deal_id)
    return [_document_to_dict(d) for d in docs]


@router.get("/{document_id}")
def get_document(
    document_id: int,
    db: Session = Depends(get_db),
    token: str | None = Depends(oauth2_scheme),
):
    doc = documents_service.get_document(db, document_id)
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    _verify_document_access(doc, token)
    return _document_to_dict(doc)


@router.get("/{document_id}/events")
async def document_events(
    document_id: int,
    db: Session = Depends(get_db),
    token: str | None = Depends(oauth2_scheme),
):
    doc = documents_service.get_document(db, document_id)
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    _verify_document_access(doc, token)

    async def event_stream():
        if doc.extraction_status in _TERMINAL_STATUSES:
            yield _format_sse(_event_from_doc(doc))
            return

        subscriber = document_event_hub.subscribe(document_id)
        iterator = subscriber.__aiter__()

        while True:
            try:
                event = await asyncio.wait_for(iterator.__anext__(), timeout=_SSE_HEARTBEAT_SEC)
            except asyncio.TimeoutError:
                yield ": ping\n\n"
                continue
            except StopAsyncIteration:
                break

            yield _format_sse(event)
            if event.get("status") in _TERMINAL_STATUSES:
                break

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/{document_id}/file")
def get_document_file(
    document_id: int,
    db: Session = Depends(get_db),
    token: str | None = Depends(oauth2_scheme),
):
    doc = documents_service.get_document(db, document_id)
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    _verify_document_access(doc, token)

    content = documents_service.load_document_bytes(doc)
    return Response(content=content, media_type=doc.mime_type)
