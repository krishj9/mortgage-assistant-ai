from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.models.event_log import EventLog, EventKind


def record_event(
    db: Session,
    *,
    deal_id: int,
    kind: EventKind,
    payload: dict[str, Any] | None = None,
) -> EventLog:
    row = EventLog(deal_id=deal_id, kind=kind.value, payload_snapshot=payload or {})
    db.add(row)
    db.commit()
    db.refresh(row)
    return row
