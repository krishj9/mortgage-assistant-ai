from __future__ import annotations

from typing import TypeVar

from langchain_aws import ChatBedrockConverse
from langchain_core.runnables import Runnable
from pydantic import BaseModel

from app.core.config import settings

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

