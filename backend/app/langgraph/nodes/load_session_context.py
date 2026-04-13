"""
Load durable session/round/question context into runtime state.

Reads
- session_id
- current_round_id

Calls
- session_service
- template_service
- resume_service

Writes to graph state
- session metadata
- current round metadata
- role/config/strictness
- time budget

Emits
- none or session.context_loaded

DB writes
- none
"""

from __future__ import annotations

from typing import Any

from app.langgraph.runtime.node_contracts import NodeExecutionContext, NodeResult, PersistenceIntent
from app.langgraph.state import RuntimeState
from app.realtime.event_contracts import SessionStateChangedEvent, SessionStateChangedPayload


def load_session_context(
    state: RuntimeState,
    *,
    session_service: Any,
    template_service: Any,
    resume_service: Any,
    ctx: NodeExecutionContext | None = None,
) -> NodeResult:
    """
    Load durable session/template/resume context into the runtime state.

    Expected service methods:
    - session_service.get_session_runtime_context(session_id: str) -> dict
    - template_service.get_template_runtime_config(template_id: str) -> dict | None
    - resume_service.get_resume_runtime_context(resume_id: str) -> dict | None
    """

    ctx = ctx or NodeExecutionContext()
    new_state = state.model_copy(deep=True)
    emitted_events = []
    persistence_intents = []
    warnings = []

    previous_status = new_state.session.session_status

    session_ctx = session_service.get_session_runtime_context(new_state.session.session_id)

    template_ctx = None
    if new_state.session.template_id:
        template_ctx = template_service.get_template_runtime_config(new_state.session.template_id)

    resume_ctx = None
    if new_state.session.resume_id:
        resume_ctx = resume_service.get_resume_runtime_context(new_state.session.resume_id)

    # Session-level runtime hydration
    new_state.session.target_role = session_ctx.get("target_role", new_state.session.target_role)
    new_state.session.interview_track = session_ctx.get("interview_track", new_state.session.interview_track)
    new_state.session.total_round_count = session_ctx.get("total_round_count", new_state.session.total_round_count)
    new_state.session.current_round_id = session_ctx.get("current_round_id", new_state.session.current_round_id)
    new_state.session.current_round_order = session_ctx.get("current_round_order", new_state.session.current_round_order)

    # Template config overlay
    if template_ctx:
        new_state.session.strictness_mode = template_ctx.get("strictness_mode", new_state.session.strictness_mode)
        new_state.session.difficulty_mode = template_ctx.get("difficulty_mode", new_state.session.difficulty_mode)
        new_state.session.voice_enabled = template_ctx.get("voice_enabled", new_state.session.voice_enabled)
        new_state.session.video_enabled = template_ctx.get("video_enabled", new_state.session.video_enabled)
        new_state.session.integrity_enabled = template_ctx.get("integrity_enabled", new_state.session.integrity_enabled)

    # Resume is not written deeply here; this node only establishes top-level runtime context.
    if new_state.session.session_status == "created":
        new_state.session.session_status = "ready"

    if previous_status != new_state.session.session_status:
        emitted_events.append(
            SessionStateChangedEvent(
                session_id=new_state.session.session_id,
                session_round_id=new_state.session.current_round_id,
                channel="session",
                event_type="session.state_changed",
                source="orchestrator",
                persist_level="important",
                payload=SessionStateChangedPayload(
                    previous_state=previous_status,
                    new_state=new_state.session.session_status,
                    reason="runtime_context_loaded",
                ),
            )
        )

    persistence_intents.append(
        PersistenceIntent(
            target="session_events",
            operation="append",
            description="Recorded session runtime context load and any status change.",
            ref_id=new_state.session.session_id,
        )
    )

    if resume_ctx is None and new_state.session.resume_id:
        warnings.append("Resume context could not be loaded; proceeding without resume-grounded behavior.")

    return NodeResult(
        state=new_state,
        emitted_events=emitted_events,
        persistence_intents=persistence_intents,
        warnings=warnings,
    )