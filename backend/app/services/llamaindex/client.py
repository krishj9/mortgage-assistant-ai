from __future__ import annotations

import logging
import time
from typing import Any, Protocol

from llama_cloud import LlamaCloud

from app.core.config import settings

logger = logging.getLogger(__name__)

_client: LlamaCloud | None = None

_TERMINAL_STATUSES = frozenset({"COMPLETED", "FAILED", "CANCELLED"})


class LlamaIndexError(Exception):
    """Raised when a LlamaCloud parse or extract job fails."""


class PollableJob(Protocol):
    status: str
    id: str


def get_client() -> LlamaCloud:
    global _client
    api_key = settings.LLAMA_CLOUD_API_KEY.strip()
    if not api_key:
        raise LlamaIndexError("LLAMA_CLOUD_API_KEY is not configured")
    if _client is None:
        _client = LlamaCloud(api_key=api_key)
    return _client


def reset_client() -> None:
    """Clear cached client (for tests)."""
    global _client
    _client = None


def wait_for_job(
    job: PollableJob,
    *,
    get_job: Any,
    job_kind: str,
    document_id: int | None = None,
) -> PollableJob:
    timeout = float(settings.LLAMA_JOB_TIMEOUT_SEC)
    interval = float(settings.LLAMA_POLL_INTERVAL_SEC)
    started = time.monotonic()
    current = job

    while current.status not in _TERMINAL_STATUSES:
        if time.monotonic() - started > timeout:
            raise LlamaIndexError(
                f"LlamaCloud {job_kind} job {current.id} timed out after {timeout}s"
            )
        time.sleep(interval)
        current = get_job(current.id)

    if current.status != "COMPLETED":
        error = getattr(current, "error_message", None) or current.status
        logger.warning(
            "llamaindex_job_failed",
            extra={
                "job_kind": job_kind,
                "job_id": current.id,
                "status": current.status,
                "document_id": document_id,
                "error": error,
            },
        )
        raise LlamaIndexError(f"LlamaCloud {job_kind} job {current.id} failed: {error}")

    elapsed_ms = int((time.monotonic() - started) * 1000)
    logger.info(
        "llamaindex_job_completed",
        extra={
            "job_kind": job_kind,
            "job_id": current.id,
            "document_id": document_id,
            "elapsed_ms": elapsed_ms,
        },
    )
    return current
