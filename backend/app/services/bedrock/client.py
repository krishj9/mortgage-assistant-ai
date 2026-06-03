from __future__ import annotations

import time
from typing import Any, TypeVar

from langchain_aws import ChatBedrockConverse
from langchain_core.messages import BaseMessage
from langchain_core.runnables import Runnable
from pydantic import BaseModel

from app.core.config import settings
from app.observability import build_runnable_config, emit_llm_metric

T = TypeVar("T", bound=BaseModel)


def get_chat_model(temperature: float = 0.2, tags: list[str] | None = None) -> ChatBedrockConverse:
    return ChatBedrockConverse(
        model=settings.BEDROCK_MODEL_ID,
        region_name=settings.AWS_REGION,
        temperature=temperature,
        tags=tags or [],
    )


def get_structured_model(
    schema: type[T],
    *,
    tags: list[str] | None = None,
    temperature: float = 0.0,
) -> Runnable:
    """Bedrock model constrained to a Pydantic schema (structured output)."""
    base = get_chat_model(temperature=temperature, tags=tags)
    return base.with_structured_output(schema)


def invoke_structured(
    model: Runnable,
    messages: list[BaseMessage],
    *,
    tags: list[str] | None = None,
    metadata: dict[str, str] | None = None,
) -> Any:
    """Invoke a structured Bedrock model with observability callbacks and metrics."""
    config = build_runnable_config(tags=tags, metadata=metadata)
    agent = (tags or ["unknown"])[0]
    started = time.monotonic()
    success = True
    try:
        return model.invoke(messages, config=config)
    except Exception:
        success = False
        raise
    finally:
        latency_ms = int((time.monotonic() - started) * 1000)
        emit_llm_metric(agent=agent, latency_ms=latency_ms, success=success)
