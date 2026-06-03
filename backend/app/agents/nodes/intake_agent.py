from __future__ import annotations

import json
import logging
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from sqlalchemy import select

from app.agents.intake_clarifications import field_aware_reply
from app.agents.intake_progress import is_meta_intent, needs_guidance
from app.agents.intake_slots import extract_patch_from_message, try_l0_slot_parse
from app.agents.prompts.intake import (
    INTAKE_FIELD_GUIDE,
    INTAKE_GUIDANCE_SYSTEM_PROMPT,
    INTAKE_SYSTEM_PROMPT,
)
from app.agents.state import LoanCopilotState
from app.agents.tools.application_writer import (
    get_application_snapshot,
    try_apply_application_patch,
)
from app.models.chat import ChatRole, ChatTurn
from app.schemas.agent_io import IntakeGuidance, IntakeTurn, patch_to_dict
from app.services.bedrock.client import get_structured_model, invoke_structured
from app.observability import agent_span, observability_context

logger = logging.getLogger(__name__)

COMPLETE_REPLY = (
    "Thanks! Your intake details look complete for now. "
    "Next step: please upload your initial documents."
)

_HISTORY_LIMIT = 10


def _load_recent_turns(db, deal_id: int, limit: int = _HISTORY_LIMIT) -> list[ChatTurn]:
    turns = (
        db.execute(
            select(ChatTurn)
            .where(ChatTurn.deal_id == deal_id)
            .order_by(ChatTurn.id.desc())
            .limit(limit)
        )
        .scalars()
        .all()
    )
    return list(reversed(turns))


def _history_to_messages(turns: list[ChatTurn]) -> list[Any]:
    messages: list[Any] = []
    for turn in turns:
        if turn.role == ChatRole.borrower.value:
            messages.append(HumanMessage(content=turn.content))
        else:
            messages.append(AIMessage(content=turn.content))
    return messages


def _last_assistant_message(turns: list[ChatTurn]) -> str | None:
    for turn in reversed(turns):
        if turn.role == ChatRole.assistant.value:
            return turn.content
    return None


def _extract_patch(borrower_message: str, next_label: str | None) -> dict[str, Any]:
    if next_label and len(borrower_message.split()) <= 8:
        patch = try_l0_slot_parse(borrower_message, next_label)
        if patch:
            return patch
    return extract_patch_from_message(borrower_message)


def _run_llm_turn(
    history_messages: list[Any],
    snapshot: dict[str, Any],
    missing_fields: list[str],
    latest_message: str,
) -> IntakeTurn | None:
    model = get_structured_model(IntakeTurn, tags=["borrower_chat", "intake_turn"])
    current = missing_fields[0] if missing_fields else None
    field_hint = INTAKE_FIELD_GUIDE.get(current, "") if current else ""
    context = (
        f"Current field to collect: {current}\n"
        f"Guidance for that field: {field_hint}\n\n"
        "Saved application so far (JSON):\n"
        f"{json.dumps(snapshot)}\n\n"
        "All fields still missing:\n"
        f"{missing_fields}\n\n"
        "The borrower just said:\n"
        f'"""{latest_message}"""\n\n'
        "If their answer cannot be mapped to allowed values, leave patch null and guide them "
        "in assistant_message with examples. Never repeat your previous wording verbatim."
    )
    messages = [
        SystemMessage(content=INTAKE_SYSTEM_PROMPT),
        *history_messages,
        HumanMessage(content=context),
    ]
    result = invoke_structured(
        model,
        messages,
        tags=["borrower_chat", "intake_turn"],
    )
    return result if isinstance(result, IntakeTurn) else None


def _run_guidance_turn(
    history_messages: list[Any],
    snapshot: dict[str, Any],
    current_field: str,
    borrower_message: str,
    *,
    validation_error: str | None = None,
    previous_assistant_message: str | None = None,
) -> str | None:
    """Dedicated LLM call when the borrower's answer could not be saved for any field."""
    model = get_structured_model(IntakeGuidance, tags=["borrower_chat", "intake_guidance"])
    field_hint = INTAKE_FIELD_GUIDE.get(current_field, "")
    context = (
        f"Field we need: {current_field}\n"
        f"Requirements: {field_hint}\n\n"
        f'Borrower answered:\n"""{borrower_message}"""\n\n'
    )
    if validation_error:
        context += f"Validation error when saving: {validation_error}\n\n"
    if previous_assistant_message:
        context += (
            "Your previous message to the borrower (use different wording):\n"
            f'"""{previous_assistant_message}"""\n\n'
        )
    context += f"Saved application so far (JSON):\n{json.dumps(snapshot)}"

    messages = [
        SystemMessage(content=INTAKE_GUIDANCE_SYSTEM_PROMPT),
        *history_messages,
        HumanMessage(content=context),
    ]
    try:
        result = invoke_structured(
            model,
            messages,
            tags=["borrower_chat", "intake_guidance"],
        )
    except Exception:
        logger.exception("Intake guidance LLM failed for field=%s", current_field)
        return None
    if isinstance(result, IntakeGuidance) and result.assistant_message.strip():
        return result.assistant_message.strip()
    return None


def _select_reply(
    *,
    missing_before: list[str],
    missing_after: list[str],
    borrower_message: str,
    llm_result: IntakeTurn | None,
    applied: bool,
    history_messages: list[Any],
    snapshot: dict[str, Any],
    validation_error: str | None,
    previous_assistant_message: str | None,
) -> str:
    if not missing_after:
        return COMPLETE_REPLY

    if llm_result and is_meta_intent(llm_result) and llm_result.assistant_message.strip():
        return llm_result.assistant_message.strip()

    current_field = missing_before[0] if missing_before else None
    if current_field and needs_guidance(
        missing_before=missing_before,
        missing_after=missing_after,
        borrower_message=borrower_message,
        turn=llm_result,
    ):
        guided = _run_guidance_turn(
            history_messages,
            snapshot,
            current_field,
            borrower_message,
            validation_error=validation_error,
            previous_assistant_message=previous_assistant_message,
        )
        if guided:
            return guided

    if llm_result and llm_result.assistant_message.strip():
        return llm_result.assistant_message.strip()

    return field_aware_reply(missing_after, made_progress=applied)


def intake_node_factory(db):
    def _intake_node(state: LoanCopilotState) -> LoanCopilotState:
        deal_id = int(state["deal_id"])
        borrower_message = state.get("latest_borrower_message", "")

        with observability_context(deal_id=deal_id), agent_span(
            "intake_turn", deal_id=deal_id
        ):
            snapshot, missing_before = get_application_snapshot(db, deal_id=deal_id)
            next_label = missing_before[0] if missing_before else None

            recent = _load_recent_turns(db, deal_id)
            if recent and recent[-1].role == ChatRole.borrower.value:
                recent = recent[:-1]
            history_messages = _history_to_messages(recent)
            previous_assistant = _last_assistant_message(recent)

            patch: dict[str, Any] = _extract_patch(borrower_message, next_label)

            llm_result: IntakeTurn | None = None
            try:
                llm_result = _run_llm_turn(
                    history_messages, snapshot, missing_before, borrower_message
                )
            except Exception:
                logger.exception("Intake LLM turn failed for deal_id=%s", deal_id)
                llm_result = None

            if llm_result and llm_result.patch is not None:
                patch = {**patch, **patch_to_dict(llm_result.patch)}

            snapshot, missing_after, applied, validation_error = try_apply_application_patch(
                db, deal_id=deal_id, patch=patch
            )

            assistant_reply = _select_reply(
                missing_before=missing_before,
                missing_after=missing_after,
                borrower_message=borrower_message,
                llm_result=llm_result,
                applied=applied,
                history_messages=history_messages,
                snapshot=snapshot,
                validation_error=validation_error,
                previous_assistant_message=previous_assistant,
            )

            return {
                **state,
                "application_patch": patch if applied else {},
                "application_snapshot": snapshot,
                "missing_fields": missing_after,
                "assistant_reply": assistant_reply,
            }

    return _intake_node
