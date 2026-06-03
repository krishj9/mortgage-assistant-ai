from __future__ import annotations

from langgraph.graph import END, START, StateGraph
from sqlalchemy.orm import Session

from app.agents.nodes.intake_agent import intake_node_factory
from app.agents.state import LoanCopilotState
from app.models.deal import DealStatus
from app.models.event_log import EventKind
from app.services.deals_service import transition_status
from app.services.eligibility_service import run_eligibility_flow
from app.services.event_log_service import record_event


def build_graph(db: Session):
    graph = StateGraph(LoanCopilotState)
    graph.add_node("intake", intake_node_factory(db))
    graph.add_edge(START, "intake")
    graph.add_edge("intake", END)
    return graph.compile()


def run_intake_turn(db: Session, deal_id: int, borrower_message: str) -> LoanCopilotState:
    app = build_graph(db)
    result: LoanCopilotState = app.invoke(
        {
            "deal_id": deal_id,
            "latest_borrower_message": borrower_message,
        }
    )
    if not result.get("missing_fields"):
        transition_status(db, deal_id=deal_id, next_status=DealStatus.docs_pending)
        record_event(
            db,
            deal_id=deal_id,
            kind=EventKind.intake_complete,
            payload={"missing_fields": []},
        )
    return result


def run_eligibility_then_messaging(db: Session, deal_id: int) -> dict:
    """Run eligibility + messaging agents and persist outputs (Phase 4)."""
    return run_eligibility_flow(db, deal_id=deal_id)

