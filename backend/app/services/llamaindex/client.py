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


def _read_job_field(job: Any, field: str) -> Any:
    """Read id/status/error_message from create or get response shapes.

    parsing.create returns ParsingCreateResponse (top-level fields).
    parsing.get returns ParsingGetResponse (fields nested under .job).
    extract.get returns ExtractV2Job (top-level fields).
    """
    model_fields = getattr(job, "model_fields", None)
    if model_fields is not None and field in model_fields:
        return getattr(job, field)
    nested = getattr(job, "job", None)
    if nested is not None:
        return getattr(nested, field)
    raise LlamaIndexError(
        f"Cannot read {field!r} from LlamaCloud job response ({type(job).__name__})"
    )


def get_job_id(job: Any) -> str:
    return str(_read_job_field(job, "id"))


def get_job_status(job: Any) -> str:
    return str(_read_job_field(job, "status"))


def get_job_error_message(job: Any) -> str | None:
    try:
        value = _read_job_field(job, "error_message")
    except LlamaIndexError:
        return None
    return str(value) if value else None


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

    job_id = get_job_id(current)

    while get_job_status(current) not in _TERMINAL_STATUSES:
        if time.monotonic() - started > timeout:
            raise LlamaIndexError(
                f"LlamaCloud {job_kind} job {job_id} timed out after {timeout}s"
            )
        time.sleep(interval)
        current = get_job(job_id)

    status = get_job_status(current)
    if status != "COMPLETED":
        error = get_job_error_message(current) or status
        logger.warning(
            "llamaindex_job_failed",
            extra={
                "job_kind": job_kind,
                "job_id": job_id,
                "status": status,
                "document_id": document_id,
                "error": error,
            },
        )
        raise LlamaIndexError(f"LlamaCloud {job_kind} job {job_id} failed: {error}")

    elapsed_ms = int((time.monotonic() - started) * 1000)
    logger.info(
        "llamaindex_job_completed",
        extra={
            "job_kind": job_kind,
            "job_id": job_id,
            "document_id": document_id,
            "elapsed_ms": elapsed_ms,
        },
    )
    return current
