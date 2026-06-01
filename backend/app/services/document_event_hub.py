from __future__ import annotations

import asyncio
import threading
from collections import defaultdict
from typing import Any, AsyncIterator

_TERMINAL_STATUSES = frozenset({"succeeded", "failed"})

_lock = threading.Lock()
_subscribers: dict[int, list[asyncio.Queue[dict[str, Any] | None]]] = defaultdict(list)
_loops: dict[int, asyncio.AbstractEventLoop] = {}


def publish(document_id: int, event: dict[str, Any]) -> None:
    """Publish a document processing event (safe from sync background tasks)."""
    with _lock:
        queues = list(_subscribers.get(document_id, []))
        loop = _loops.get(document_id)

    for queue in queues:
        if loop is not None and loop.is_running():
            loop.call_soon_threadsafe(queue.put_nowait, event)
        else:
            try:
                queue.put_nowait(event)
            except Exception:
                pass


async def subscribe(document_id: int) -> AsyncIterator[dict[str, Any]]:
    """Yield events until a terminal status or unsubscribe sentinel."""
    queue: asyncio.Queue[dict[str, Any] | None] = asyncio.Queue()
    loop = asyncio.get_running_loop()

    with _lock:
        _subscribers[document_id].append(queue)
        _loops[document_id] = loop

    try:
        while True:
            event = await queue.get()
            if event is None:
                break
            yield event
            if event.get("status") in _TERMINAL_STATUSES:
                break
    finally:
        with _lock:
            subs = _subscribers.get(document_id, [])
            if queue in subs:
                subs.remove(queue)
            if not subs:
                _subscribers.pop(document_id, None)
                _loops.pop(document_id, None)


def build_event(
    document_id: int,
    *,
    status: str,
    stage: str | None = None,
    predicted_type: str | None = None,
    classification_confidence: float | None = None,
    error: str | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "document_id": document_id,
        "status": status,
    }
    if stage is not None:
        payload["stage"] = stage
    if predicted_type is not None:
        payload["predicted_type"] = predicted_type
    if classification_confidence is not None:
        payload["classification_confidence"] = classification_confidence
    if error is not None:
        payload["error"] = error
    return payload


def reset_for_tests() -> None:
    with _lock:
        _subscribers.clear()
        _loops.clear()
