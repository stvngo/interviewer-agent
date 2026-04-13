"""
Purpose: Choose the next question for the round.

Reads
- round_type
- question_index
- target_role
- difficulty_mode
- resume_id
- current round config

Calls

- question_service
- retrieval_service optionally

Writes
- question_id
- session_question_id
- question_status = in_progress

Emits
- question.assigned

DB writes
- insert/update session_questions
"""

from __future__ import annotations

from typing import Any

from app.langgraph.runtime.node_contracts import NodeExecutionContext, NodeResult, PersistenceIntent
from app.langgraph.state import RuntimeState
from app.realtime.event_contracts import (
    QuestionAssignedEvent,
    QuestionAssignedPayload,
    RoundStateChangedEvent,
    RoundStateChangedPayload,
)


def select_question(
    state: RuntimeState,
    *,
    question_service: Any,
    session_service: Any,
    ctx: NodeExecutionContext | None = None,
) -> NodeResult:
    """
    Choose and assign the next question for the active round.

    Expected service methods:
    - question_service.select_next_question(...) -> dict
    - session_service.assign_question_to_round(...) -> dict
    """

    ctx = ctx or NodeExecutionContext()
    new_state = state.model_copy(deep=True)
    emitted_events = []
    persistence_intents = []
    warnings = []

    previous_round_status = new_state.round.round_status

    selected = question_service.select_next_question(
        round_type=new_state.round.round_type,
        question_index=new_state.round.question_index,
        target_role=new_state.session.target_role,
        difficulty_mode=new_state.session.difficulty_mode,
        resume_id=new_state.session.resume_id,
        strictness_mode=new_state.session.strictness_mode,
    )

    assignment = session_service.assign_question_to_round(
        session_id=new_state.session.session_id,
        round_id=new_state.round.round_id,
        question_id=selected["question_id"],
        question_order=new_state.round.question_index,
    )

    new_state.round.question_id = assignment["question_id"]
    new_state.round.session_question_id = assignment["session_question_id"]
    new_state.round.question_status = "in_progress"
    new_state.round.round_status = "asking_question"

    # Reset per-question execution state
    new_state.round.followup_depth_used = 0
    new_state.round.hint_level_used = 0
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
    new_state.round.retrieval_bundle.rubric_context_ref = None
    new_state.round.retrieval_bundle.resume_context_ref = None
    new_state.round.retrieval_bundle.followup_context_ref = None
    new_state.round.retrieval_bundle.loaded_at = None

    emitted_events.append(
        QuestionAssignedEvent(
            session_id=new_state.session.session_id,
            session_round_id=new_state.round.round_id,
            session_question_id=new_state.round.session_question_id,
            channel="round",
            event_type="question.assigned",
            source="orchestrator",
            persist_level="important",
            payload=QuestionAssignedPayload(
                question_id=new_state.round.question_id,
                question_order=new_state.round.question_index,
                question_status="in_progress",
                round_type=new_state.round.round_type,
                prompt_preview=selected.get("prompt_preview"),
            ),
        )
    )

    if previous_round_status != new_state.round.round_status:
        emitted_events.append(
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
                    new_state=new_state.round.round_status,
                    reason="question_selected",
                ),
            )
        )

    persistence_intents.extend(
        [
            PersistenceIntent(
                target="session_questions",
                operation="upsert",
                description="Assigned next question to session round.",
                ref_id=new_state.round.session_question_id,
            ),
            PersistenceIntent(
                target="session_events",
                operation="append",
                description="Recorded question assignment and round transition.",
                ref_id=new_state.session.session_id,
            ),
        ]
    )

    return NodeResult(
        state=new_state,
        emitted_events=emitted_events,
        persistence_intents=persistence_intents,
        warnings=warnings,
    )