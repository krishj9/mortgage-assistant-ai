"""Backward-compatible re-exports. Prefer app.observability."""

from app.observability import (
    configure_langsmith,
    configure_observability,
    with_deal_metadata,
)

__all__ = ["configure_langsmith", "configure_observability", "with_deal_metadata"]
