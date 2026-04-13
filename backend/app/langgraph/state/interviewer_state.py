"""
InterviewerExecutionState
- should_speak: bool
- pending_spoken_response: str | None
- response_goal: str | None
- interruptible: bool
- wait_before_speaking_ms: int
- detected_user_state: "answering" | "thinking" | "stuck" | "off_track" | "finished" | "needs_clarification" | "debugging"
- state_transition_target: str | None
"""

from __future__ import annotations

from .shared_types import DetectedUserState, InterviewerGoal, RoundStatus, StateModel


class InterviewerExecutionState(StateModel):
    should_speak: bool = False
    pending_spoken_response: str | None = None
    response_goal: InterviewerGoal | None = None
    interruptible: bool = False
    wait_before_speaking_ms: int = 0

    detected_user_state: DetectedUserState = "needs_clarification"
    state_transition_target: RoundStatus | None = None