from __future__ import annotations

import logging
import time
import uuid
from typing import Awaitable, Callable

import structlog
from starlette.requests import Request
from starlette.types import ASGIApp
from starlette.responses import Response


def configure_logging() -> None:
    logging.basicConfig(level=logging.INFO)

    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    )


async def request_id_middleware(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
    request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
    start = time.time()
    request.state.request_id = request_id

    response: Response = await call_next(request)
    response.headers["X-Request-Id"] = request_id

    structlog.get_logger().info(
        "request_complete",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        latency_ms=int((time.time() - start) * 1000),
        request_id=request_id,
    )
    return response


def get_logger():
    return structlog.get_logger()

