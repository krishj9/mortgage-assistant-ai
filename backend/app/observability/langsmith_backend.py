from __future__ import annotations

import os
from typing import Any

from langchain_core.callbacks.base import BaseCallbackHandler

from app.core.config import settings

_tracer: BaseCallbackHandler | None = None


def configure() -> None:
    global _tracer
    if settings.LANGSMITH_API_KEY.strip():
        os.environ["LANGSMITH_API_KEY"] = settings.LANGSMITH_API_KEY.strip()
    if settings.LANGSMITH_PROJECT.strip():
        os.environ["LANGSMITH_PROJECT"] = settings.LANGSMITH_PROJECT.strip()
    os.environ["LANGSMITH_TRACING"] = "true"

    try:
        from langchain_core.tracers.langchain import LangChainTracer

        _tracer = LangChainTracer(project_name=settings.LANGSMITH_PROJECT)
    except Exception:
        _tracer = None


def get_callbacks() -> list[BaseCallbackHandler]:
    if _tracer is None:
        return []
    return [_tracer]


def emit_llm_metric(*, agent: str, latency_ms: int, success: bool) -> None:
    # LangSmith captures LLM latency via traces; structured log for correlation.
    from app.core.logging import get_logger

    get_logger().info(
        "llm_invoke_complete",
        agent=agent,
        latency_ms=latency_ms,
        success=success,
        observability_provider="langsmith",
    )


def record_eval_metric(*, agent: str, case_id: str, score: float, suite: str) -> None:
    from app.core.logging import get_logger

    get_logger().info(
        "eval_case_result",
        agent=agent,
        case_id=case_id,
        score=score,
        suite=suite,
        observability_provider="langsmith",
    )
