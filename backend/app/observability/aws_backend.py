from __future__ import annotations

import json
import sys
import time
from contextlib import contextmanager
from typing import Any, Iterator

from app.core.config import settings
from app.observability.context import bind_trace_id

_initialized = False
_tracer = None


def _ensure_initialized() -> None:
    global _initialized, _tracer
    if _initialized:
        return

    try:
        from opentelemetry import trace
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
    except ImportError as exc:
        raise RuntimeError(
            "OBSERVABILITY_PROVIDER=aws requires optional deps. "
            "Install with: uv sync --extra observability-aws"
        ) from exc

    resource = Resource.create({"service.name": settings.OTEL_SERVICE_NAME})
    provider = TracerProvider(resource=resource)
    endpoint = settings.OTEL_EXPORTER_OTLP_ENDPOINT.strip()
    if endpoint:
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

        provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint)))
    else:
        provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter(out=sys.stderr)))

    trace.set_tracer_provider(provider)
    _tracer = trace.get_tracer(settings.OTEL_SERVICE_NAME)
    _initialized = True


def configure() -> None:
    _ensure_initialized()


def instrument_app(app: Any) -> None:
    _ensure_initialized()
    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
        from opentelemetry.instrumentation.botocore import BotocoreInstrumentor

        FastAPIInstrumentor.instrument_app(app)
        HTTPXClientInstrumentor().instrument()
        BotocoreInstrumentor().instrument()
    except ImportError:
        pass


def get_callbacks() -> list:
    return []


@contextmanager
def span(name: str, **attributes: Any) -> Iterator[None]:
    _ensure_initialized()
    from opentelemetry import trace

    tracer = trace.get_tracer(settings.OTEL_SERVICE_NAME)
    with tracer.start_as_current_span(name) as current:
        for key, value in attributes.items():
            if value is not None:
                current.set_attribute(key, value)
        span_context = current.get_span_context()
        if span_context.trace_id:
            bind_trace_id(format(span_context.trace_id, "032x"))
        yield


def emit_llm_metric(*, agent: str, latency_ms: int, success: bool) -> None:
    from app.core.logging import get_logger

    get_logger().info(
        "llm_invoke_complete",
        agent=agent,
        latency_ms=latency_ms,
        success=success,
        observability_provider="aws",
    )
    _emit_emf_metric(
        metric_name="LLMInvokeLatencyMs",
        value=float(latency_ms),
        dimensions={"Agent": agent, "Success": str(success).lower()},
    )


def record_eval_metric(*, agent: str, case_id: str, score: float, suite: str) -> None:
    from app.core.logging import get_logger

    get_logger().info(
        "eval_case_result",
        agent=agent,
        case_id=case_id,
        score=score,
        suite=suite,
        observability_provider="aws",
    )
    _emit_emf_metric(
        metric_name="EvalScore",
        value=score,
        dimensions={"Agent": agent, "CaseId": case_id, "Suite": suite},
    )


def _emit_emf_metric(*, metric_name: str, value: float, dimensions: dict[str, str]) -> None:
    """CloudWatch Embedded Metric Format to stdout (ADOT / agent can scrape)."""
    emf = {
        "_aws": {
            "Timestamp": int(time.time() * 1000),
            "CloudWatchMetrics": [
                {
                    "Namespace": "LoanOfficerCopilot",
                    "Dimensions": [list(dimensions.keys())],
                    "Metrics": [{"Name": metric_name, "Unit": "None"}],
                }
            ],
        },
        metric_name: value,
        **dimensions,
    }
    print(json.dumps(emf), file=sys.stdout, flush=True)
