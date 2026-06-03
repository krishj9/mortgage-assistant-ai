from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any, Iterator

_request_id: ContextVar[str | None] = ContextVar("request_id", default=None)
_deal_id: ContextVar[int | None] = ContextVar("deal_id", default=None)
_document_id: ContextVar[int | None] = ContextVar("document_id", default=None)
_user_id: ContextVar[str | None] = ContextVar("user_id", default=None)
_trace_id: ContextVar[str | None] = ContextVar("trace_id", default=None)


def bind_request_id(request_id: str | None) -> None:
    _request_id.set(request_id)


def bind_deal_id(deal_id: int | None) -> None:
    _deal_id.set(deal_id)


def bind_document_id(document_id: int | None) -> None:
    _document_id.set(document_id)


def bind_user_id(user_id: str | None) -> None:
    _user_id.set(user_id)


def bind_trace_id(trace_id: str | None) -> None:
    _trace_id.set(trace_id)


def get_log_context() -> dict[str, Any]:
    ctx: dict[str, Any] = {}
    if (request_id := _request_id.get()) is not None:
        ctx["request_id"] = request_id
    if (deal_id := _deal_id.get()) is not None:
        ctx["deal_id"] = deal_id
    if (document_id := _document_id.get()) is not None:
        ctx["document_id"] = document_id
    if (user_id := _user_id.get()) is not None:
        ctx["user_id"] = user_id
    if (trace_id := _trace_id.get()) is not None:
        ctx["trace_id"] = trace_id
    return ctx


def build_run_metadata(
    *,
    deal_id: int | None = None,
    document_id: int | None = None,
    user_id: str | None = None,
) -> dict[str, str]:
    metadata: dict[str, str] = {}
    effective_deal = deal_id if deal_id is not None else _deal_id.get()
    effective_doc = document_id if document_id is not None else _document_id.get()
    effective_user = user_id if user_id is not None else _user_id.get()
    effective_request = _request_id.get()
    if effective_deal is not None:
        metadata["deal_id"] = str(effective_deal)
    if effective_doc is not None:
        metadata["document_id"] = str(effective_doc)
    if effective_user is not None:
        metadata["user_id"] = str(effective_user)
    if effective_request is not None:
        metadata["request_id"] = effective_request
    return metadata


@contextmanager
def observability_context(
    *,
    deal_id: int | None = None,
    document_id: int | None = None,
    user_id: str | None = None,
) -> Iterator[None]:
    deal_token = _deal_id.set(deal_id) if deal_id is not None else None
    doc_token = _document_id.set(document_id) if document_id is not None else None
    user_token = _user_id.set(user_id) if user_id is not None else None
    try:
        yield
    finally:
        if deal_token is not None:
            _deal_id.reset(deal_token)
        if doc_token is not None:
            _document_id.reset(doc_token)
        if user_token is not None:
            _user_id.reset(user_token)
