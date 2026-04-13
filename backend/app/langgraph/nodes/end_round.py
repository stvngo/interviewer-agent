"""
Purpose: Finalize round.

Calls
- scoring_service
- round_service if kept
- session_service

Writes
- round_status = ended
- should_end_round = false

Emits
- round.ended

DB writes
- final round scorecard if round-scoped
"""

from __future__ import annotations

from typing import Any

from app.langgraph.runtime.node_contracts import NodeExecutionContext, NodeResult, PersistenceIntent
from app.langgraph.state import RuntimeState
from app.realtime.event_contracts import RoundStateChangedEvent, RoundStateChangedPayload


def end_round(
    state: RuntimeState,
    *,
    scoring_service: Any,
    session_service: Any,
    ctx: NodeExecutionContext | None = None,
) -> NodeResult:
    """
    Finalize the current round and persist round-level scoring.
    """
    ctx = ctx or NodeExecutionContext(actor="system")
    new_state = state.model_copy(deep=True)

    previous_round_status = new_state.round.round_status
    new_state.round.round_status = "ended"
    new_state.round.should_end_round = False

    scorecard = scoring_service.finalize_round_scorecard(
        session_id=new_state.session.session_id,
        round_id=new_state.round.round_id,
        question_id=new_state.round.question_id,
        evaluation_state=new_state.evaluation.model_dump(),
        round_state=new_state.round.model_dump(),
    )

    session_service.finalize_round(
        session_id=new_state.session.session_id,
        round_id=new_state.round.round_id,
        final_status="ended",
    )

    emitted = [
        RoundStateChangedEvent(
            session_id=new_state.session.session_id,
            session_round_id=new_state.round.round_id,
            session_question_id=new_state.round.session_question_id,
            channel="round",
            event_type="round.state_changed",
            source="orchestrator",
            persist_level="important",
            payload=RoundStateChangedPayload(
                previous_state=previous_round_status,
                new_state="ended",
                reason="round_completed",
            ),
        )
    ]

    intents = [
        PersistenceIntent(
            target="final_scorecards",
            operation="append",
            description="Persisted finalized round scorecard.",
            ref_id=scorecard["scorecard_id"],
        ),
        PersistenceIntent(
            target="session_rounds",
            operation="update",
            description="Marked session round as ended.",
            ref_id=new_state.round.round_id,
        ),
        PersistenceIntent(
            target="session_events",
            operation="append",
            description="Recorded round completion.",
            ref_id=new_state.session.session_id,
        ),
    ]

    return NodeResult(
        state=new_state,
        emitted_events=emitted,
        persistence_intents=intents,
    )