"""
RoundGraphState
- session_id: str
- round_id: str
- session_question_id: str | None
- question_id: str | None
- round_type: "behavioral" | "coding" | "ds_sql" | "system_design" | "stats" | "resume_deep_dive"
- round_status: "not_started" | "asking_question" | "listening" | "user_thinking" | "probing" | "hinting" | "evaluating" | "wrapping_up" | "ended"

- question_index: int
- question_status: "not_started" | "in_progress" | "answered" | "exhausted"
- followup_depth_used: int
- max_followup_depth: int

- hint_level_used: int
- max_hint_level_allowed: int
- hint_budget_remaining: int

- transcript_window: TranscriptWindow
- code_window: CodeWindow
- retrieval_bundle: RetrievalBundle

- latest_evaluator_status: "on_track" | "at_risk" | "stalled" | "completed" | "uncertain"
- latest_intervention_decision: InterventionDecision | None
- latest_interviewer_goal: "ask_question" | "acknowledge" | "clarify" | "probe" | "challenge" | "redirect" | "hint" | "summarize" | "wrap_up" | "transition" | None

- user_requested_hint: bool
- user_requested_repeat: bool
- should_advance_question: bool
- should_end_round: bool

- round_time_budget: TimeBudget
- evaluator_checkpoint_counter: int
- code_checkpoint_counter: int
- transcript_checkpoint_counter: int
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import Field

from .shared_types import (
    EvaluatorStatus,
    InterventionDecision,
    InterviewerGoal,
    InputEventType,
    QuestionStatus,
    RetrievalBundle,
    RoundStatus,
    RoundType,
    StateModel,
    TimeBudget,
    TranscriptWindow,
    CodeWindow,
)


class RoundGraphState(StateModel):
    session_id: UUID
    round_id: UUID

    session_question_id: UUID | None = None
    question_id: UUID | None = None

    round_type: RoundType
    round_status: RoundStatus = "not_started"

    question_index: int = 0
    question_status: QuestionStatus = "not_started"

    followup_depth_used: int = 0
    max_followup_depth: int = 2

    hint_level_used: int = 0
    max_hint_level_allowed: int = 2
    hint_budget_remaining: int = 1

    transcript_window: TranscriptWindow = Field(default_factory=TranscriptWindow)
    code_window: CodeWindow = Field(default_factory=CodeWindow)
    retrieval_bundle: RetrievalBundle = Field(default_factory=RetrievalBundle)

    latest_evaluator_status: EvaluatorStatus = "uncertain"
    latest_intervention_decision: InterventionDecision | None = None
    latest_interviewer_goal: InterviewerGoal | None = None

    user_requested_hint: bool = False
    user_requested_repeat: bool = False
    should_advance_question: bool = False
    should_end_round: bool = False

    round_time_budget: TimeBudget = Field(default_factory=TimeBudget)

    evaluator_checkpoint_counter: int = 0
    code_checkpoint_counter: int = 0
    transcript_checkpoint_counter: int = 0

    pending_input_event_type: InputEventType | None = None
    pending_input_event_payload: dict[str, Any] | None = None