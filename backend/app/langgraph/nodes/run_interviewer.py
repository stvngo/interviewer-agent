"""
Purpose: Generate the next interviewer move.

Reads
- round state
- transcript window
- code window
- latest intervention decision
- retrieval refs

Calls
- interviewer_agent

Writes
- InterviewerExecutionState
- latest_interviewer_goal
- round_status target

Emits
- interviewer.turn_decision
- interviewer.utterance.created if speaking

DB writes
- optional session_events only
"""

from __future__ import annotations

from typing import Any

from app.langgraph.runtime.node_contracts import NodeExecutionContext, NodeResult, PersistenceIntent
from app.langgraph.state import RuntimeState
from app.realtime.event_contracts import (
    InterviewerTurnDecisionEvent,
    InterviewerTurnDecisionPayload,
    InterviewerUtteranceCreatedEvent,
    InterviewerUtteranceCreatedPayload,
)


def run_interviewer(
    state: RuntimeState,
    *,
    interviewer_agent: Any,
    ctx: NodeExecutionContext | None = None,
) -> NodeResult:
    """
    Generate the next interviewer move.

    Expected agent method:
    - interviewer_agent.invoke(payload: dict) -> dict
    """

    ctx = ctx or NodeExecutionContext()
    new_state = state.model_copy(deep=True)
    emitted_events = []
    persistence_intents = []
    warnings = []

    agent_input = {
        "session": new_state.session.model_dump(),
        "round": new_state.round.model_dump(),
        "interviewer": new_state.interviewer.model_dump(),
        "evaluation": new_state.evaluation.model_dump(),
    }

    result = interviewer_agent.invoke(agent_input)

    user_state = new_state.round.transcript_window.user_current_state
    # If the user is actively speaking, avoid talking over them.
    if user_state == "speaking":
        result["should_speak"] = False
        result["spoken_response"] = None
        result["response_goal"] = "acknowledge"
        result["state_transition"] = "listening"
        result["interruptible"] = True
        result["wait_before_speaking_ms"] = 0

    # Strong off-track signals should trigger concise redirect interruptions.
    if (new_state.evaluation.off_track_score or 0) > 0.85:
        result["should_speak"] = True
        result["spoken_response"] = (
            "Let's pause for a moment. You're drifting off the core problem; "
            "please restate your approach in one sentence and continue from there."
        )
        result["response_goal"] = "redirect"
        result["state_transition"] = "probing"
        result["interruptible"] = True
        result["wait_before_speaking_ms"] = 0

    new_state.interviewer.should_speak = result.get("should_speak", False)
    new_state.interviewer.pending_spoken_response = result.get("spoken_response")
    new_state.interviewer.response_goal = result.get("response_goal")
    new_state.interviewer.interruptible = result.get("interruptible", False)
    new_state.interviewer.wait_before_speaking_ms = result.get("wait_before_speaking_ms", 0)
    new_state.interviewer.detected_user_state = result.get("detected_user_state", "needs_clarification")
    new_state.interviewer.state_transition_target = result.get("state_transition")

    new_state.round.latest_interviewer_goal = result.get("response_goal")

    if result.get("state_transition"):
        new_state.round.round_status = result["state_transition"]

    emitted_events.append(
        InterviewerTurnDecisionEvent(
            session_id=new_state.session.session_id,
            session_round_id=new_state.round.round_id,
            session_question_id=new_state.round.session_question_id,
            channel="interviewer",
            event_type="interviewer.turn_decision",
            source="interviewer_agent",
            persist_level="important",
            payload=InterviewerTurnDecisionPayload(
                should_speak=new_state.interviewer.should_speak,
                response_goal=new_state.interviewer.response_goal,
                detected_user_state=new_state.interviewer.detected_user_state,
                interruptible=new_state.interviewer.interruptible,
                wait_before_speaking_ms=new_state.interviewer.wait_before_speaking_ms,
                next_round_state=new_state.interviewer.state_transition_target,
            ),
        )
    )

    if new_state.interviewer.should_speak and new_state.interviewer.pending_spoken_response:
        emitted_events.append(
            InterviewerUtteranceCreatedEvent(
                session_id=new_state.session.session_id,
                session_round_id=new_state.round.round_id,
                session_question_id=new_state.round.session_question_id,
                channel="interviewer",
                event_type="interviewer.utterance.created",
                source="interviewer_agent",
                persist_level="important",
                payload=InterviewerUtteranceCreatedPayload(
                    spoken_response=new_state.interviewer.pending_spoken_response,
                    response_goal=new_state.interviewer.response_goal or "acknowledge",
                    interruptible=new_state.interviewer.interruptible,
                    wait_before_speaking_ms=new_state.interviewer.wait_before_speaking_ms,
                    state_transition=new_state.interviewer.state_transition_target,
                    audio_url=None,
                ),
            )
        )

    persistence_intents.append(
        PersistenceIntent(
            target="session_events",
            operation="append",
            description="Recorded interviewer turn decision and optional utterance.",
            ref_id=new_state.session.session_id,
        )
    )

    if not result.get("spoken_response") and result.get("should_speak"):
        warnings.append("Interviewer requested speech but returned no spoken_response.")

    return NodeResult(
        state=new_state,
        emitted_events=emitted_events,
        persistence_intents=persistence_intents,
        warnings=warnings,
    )