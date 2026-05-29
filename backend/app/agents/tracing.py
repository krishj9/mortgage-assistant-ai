from __future__ import annotations

import os


def configure_langsmith() -> None:
    """
    Keeps tracing optional for local development.
    """
    if os.environ.get("LANGSMITH_API_KEY"):
        os.environ.setdefault("LANGSMITH_TRACING", "true")


def with_deal_metadata(deal_id: int) -> dict:
    return {"deal_id": str(deal_id)}

