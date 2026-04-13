"""
Purpose: Generate hint/help when allowed.

Calls
- coach_agent

Writes
- increment hint_level_used
- maybe update round_status = hinting

Emits
- coach.hint_ready

DB writes
update session_questions.max_hint_level_used
"""

from __future__ import annotations

from typing import Any

from app.langgraph.runtime.node_contracts import NodeExecutionContext, NodeResult, PersistenceIntent
from app.langgraph.state import RuntimeState
from app.realtime.event_contracts import CoachHintReadyEvent, CoachHintReadyPayload


def run_coach(
    state: RuntimeState,
    *,
    coach_agent: Any,
    ctx: NodeExecutionContext | None = None,
) -> NodeResult:
    """
    Generate a hint/coaching response when policy allows.
    """
    ctx = ctx or NodeExecutionContext(actor="agent")
    new_state = state.model_copy(deep=True)
    warnings: list[str] = []

    agent_input = {
        "session": new_state.session.model_dump(),
        "round": new_state.round.model_dump(),
        "interviewer": new_state.interviewer.model_dump(),
        "evaluation": new_state.evaluation.model_dump(),
    }

    result = coach_agent.invoke(agent_input)

    reveal_level = int(result.get("reveal_level", 1))
    if reveal_level > new_state.round.max_hint_level_allowed:
        reveal_level = new_state.round.max_hint_level_allowed
        warnings.append("Coach requested reveal level above policy; clamped to max_hint_level_allowed.")

    new_state.round.hint_level_used = max(new_state.round.hint_level_used, reveal_level)
    new_state.round.hint_budget_remaining = max(0, new_state.round.hint_budget_remaining - 1)
    new_state.round.user_requested_hint = False
    new_state.round.round_status = "hinting"

    emitted = [
        CoachHintReadyEvent(
            session_id=new_state.session.session_id,
            session_round_id=new_state.round.round_id,
            session_question_id=new_state.round.session_question_id,
            channel="coach",
            event_type="coach.hint_ready",
            source="coach_agent",
            persist_level="important",
            payload=CoachHintReadyPayload(
                helpfulness_level=result.get("helpfulness_level", "light"),
                reveal_level=reveal_level,
                coach_response=result.get("coach_response", ""),
            ),
        )
    ]

    intents = [
        PersistenceIntent(
            target="session_questions",
            operation="update",
            description="Updated hint usage metadata for active session question.",
            ref_id=new_state.round.session_question_id,
        ),
        PersistenceIntent(
            target="session_events",
            operation="append",
            description="Recorded coach hint generation.",
            ref_id=new_state.session.session_id,
        ),
    ]

    return NodeResult(
        state=new_state,
        emitted_events=emitted,
        persistence_intents=intents,
        warnings=warnings,
    )