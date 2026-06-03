from __future__ import annotations

from typing import Literal

from app.core.config import settings

ObservabilityProvider = Literal["langsmith", "aws", "none"]


def get_observability_provider() -> ObservabilityProvider:
    value = settings.OBSERVABILITY_PROVIDER.lower().strip()
    if value in ("langsmith", "aws", "none"):
        return value  # type: ignore[return-value]
    return "none"


def validate_observability_config() -> None:
    provider = get_observability_provider()
    if provider == "langsmith" and not settings.LANGSMITH_API_KEY.strip():
        raise ValueError(
            "OBSERVABILITY_PROVIDER=langsmith requires LANGSMITH_API_KEY to be set."
        )
