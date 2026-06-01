from __future__ import annotations

import json

import pytest

from app.services import document_event_hub


def test_publish_and_subscribe_terminal_event():
    document_event_hub.reset_for_tests()
    events = []

    async def collect():
        async for event in document_event_hub.subscribe(42):
            events.append(event)

    import asyncio

    async def run():
        task = asyncio.create_task(collect())
        await asyncio.sleep(0.01)
        document_event_hub.publish(
            42,
            document_event_hub.build_event(42, status="running", stage="parsing"),
        )
        document_event_hub.publish(
            42,
            document_event_hub.build_event(
                42,
                status="succeeded",
                predicted_type="pay_stub",
                classification_confidence=0.9,
            ),
        )
        await asyncio.wait_for(task, timeout=1.0)

    asyncio.run(run())
    assert len(events) == 2
    assert events[-1]["status"] == "succeeded"
    assert events[-1]["predicted_type"] == "pay_stub"


def test_build_event_json_serializable():
    event = document_event_hub.build_event(
        1,
        status="failed",
        error="Only pay stubs, W-2s, and bank statements are accepted.",
    )
    json.dumps(event)
