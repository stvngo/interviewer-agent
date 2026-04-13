"""
Purpose: Close current question and move to next one.

Calls
- session_service
- question_service

Writes
- increment question_index
- reset per-question runtime state

Emits
- question.advanced

DB writes
- finalize current session_question
"""

from __future__ import annotations

from typing import Any

from app.langgraph.runtime.node_contracts import NodeExecutionContext, NodeResult, PersistenceIntent
from app.langgraph.state import EvaluationState, InterviewerExecutionState, RuntimeState
from app.realtime.event_contracts import RoundStateChangedEvent, RoundStateChangedPayload


def advance_question(
    state: RuntimeState,
    *,
    session_service: Any,
    question_service: Any,
    ctx: NodeExecutionContext | None = None,
) -> NodeResult:
    """
    Finalize current question and reset per-question runtime state for the next one.
    """
    ctx = ctx or NodeExecutionContext(actor="system")
    new_state = state.model_copy(deep=True)

    previous_round_status = new_state.round.round_status
    previous_session_question_id = new_state.round.session_question_id

    session_service.finalize_session_question(
        session_id=new_state.session.session_id,
        round_id=new_state.round.round_id,
        session_question_id=new_state.round.session_question_id,
        final_status=new_state.round.question_status,
    )

    new_state.round.question_index += 1
    new_state.round.question_id = None
    new_state.round.session_question_id = None
    new_state.round.question_status = "not_started"
    new_state.round.round_status = "asking_question"

    new_state.round.followup_depth_used = 0
    new_state.round.hint_level_used = 0
    new_state.round.hint_budget_remaining = 1
    new_state.round.user_requested_hint = False
    new_state.round.user_requested_repeat = False
    new_state.round.should_advance_question = False

    new_state.round.transcript_window.recent_segment_ids.clear()
    new_state.round.transcript_window.rolling_text = ""
    new_state.round.transcript_window.silence_ms = 0
    new_state.round.transcript_window.user_current_state = "unknown"

    new_state.round.code_window.recent_code_event_ids.clear()
    new_state.round.code_window.latest_snapshot_hash = None
    new_state.round.code_window.last_run_status = "not_run"
    new_state.round.code_window.code_progress_state = "not_started"
    new_state.round.code_window.latest_stdout_excerpt = None
    new_state.round.code_window.latest_stderr_excerpt = None
    new_state.round.code_window.tests_passed = None
    new_state.round.code_window.tests_failed = None

    new_state.round.retrieval_bundle.question_context_ref = None
    new_state.round.retrieval_bundle.resume_context_ref = None
    new_state.round.retrieval_bundle.rubric_context_ref = None
    new_state.round.retrieval_bundle.followup_context_ref = None
    new_state.round.retrieval_bundle.loaded_at = None

    new_state.interviewer = InterviewerExecutionState()
    new_state.evaluation = EvaluationState()

    emitted = [
        RoundStateChangedEvent(
            session_id=new_state.session.session_id,
            session_round_id=new_state.round.round_id,
            session_question_id=None,
            channel="round",
            event_type="round.state_changed",
            source="orchestrator",
            persist_level="important",
            payload=RoundStateChangedPayload(
                previous_state=previous_round_status,
                new_state=new_state.round.round_status,
                reason="advance_question",
            ),
        )
    ]

    intents = [
        PersistenceIntent(
            target="session_questions",
            operation="update",
            description="Finalized previous session question before advancing.",
            ref_id=previous_session_question_id,
        ),
        PersistenceIntent(
            target="session_events",
            operation="append",
            description="Recorded question advancement and per-question state reset.",
            ref_id=new_state.session.session_id,
        ),
    ]

    return NodeResult(
        state=new_state,
        emitted_events=emitted,
        persistence_intents=intents,
    )