from __future__ import annotations

from typing import Any, Iterator
from contextlib import contextmanager

from app.core.config import settings
from app.observability import aws_backend, langsmith_backend
from app.observability.context import (
    bind_request_id,
    build_run_metadata,
    get_log_context,
    observability_context,
)
from app.observability.provider import get_observability_provider, validate_observability_config

_none_backend_configured = False


def configure_observability(app: Any | None = None) -> None:
    validate_observability_config()
    provider = get_observability_provider()
    if provider == "langsmith":
        langsmith_backend.configure()
    elif provider == "aws":
        aws_backend.configure()
        if app is not None:
            aws_backend.instrument_app(app)
    if app is not None and provider != "aws":
        global _none_backend_configured
        _none_backend_configured = True


def get_callbacks() -> list:
    provider = get_observability_provider()
    if provider == "langsmith":
        return langsmith_backend.get_callbacks()
    return []


def build_runnable_config(
    *,
    tags: list[str] | None = None,
    metadata: dict[str, str] | None = None,
) -> dict[str, Any]:
    config: dict[str, Any] = {}
    if tags:
        config["tags"] = tags
    merged = build_run_metadata()
    if metadata:
        merged.update(metadata)
    if merged:
        config["metadata"] = merged
    callbacks = get_callbacks()
    if callbacks:
        config["callbacks"] = callbacks
    return config


def emit_llm_metric(*, agent: str, latency_ms: int, success: bool) -> None:
    provider = get_observability_provider()
    if provider == "langsmith":
        langsmith_backend.emit_llm_metric(agent=agent, latency_ms=latency_ms, success=success)
    elif provider == "aws":
        aws_backend.emit_llm_metric(agent=agent, latency_ms=latency_ms, success=success)


def record_eval_metric(*, agent: str, case_id: str, score: float, suite: str) -> None:
    provider = get_observability_provider()
    if provider == "langsmith":
        langsmith_backend.record_eval_metric(agent=agent, case_id=case_id, score=score, suite=suite)
    elif provider == "aws":
        aws_backend.record_eval_metric(agent=agent, case_id=case_id, score=score, suite=suite)


@contextmanager
def agent_span(name: str, **attributes: Any) -> Iterator[None]:
    provider = get_observability_provider()
    if provider == "aws":
        with aws_backend.span(name, **attributes):
            yield
    else:
        yield


# Backward compatibility
def configure_langsmith() -> None:
    if get_observability_provider() == "langsmith":
        langsmith_backend.configure()


def with_deal_metadata(deal_id: int) -> dict:
    return build_run_metadata(deal_id=deal_id)


__all__ = [
    "configure_observability",
    "configure_langsmith",
    "get_callbacks",
    "build_runnable_config",
    "build_run_metadata",
    "bind_request_id",
    "get_log_context",
    "observability_context",
    "agent_span",
    "emit_llm_metric",
    "record_eval_metric",
    "with_deal_metadata",
    "get_observability_provider",
]
