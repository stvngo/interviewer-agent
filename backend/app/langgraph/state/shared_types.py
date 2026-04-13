"""
EntityRef
- id: str
- type: str

TimeBudget
- started_at: datetime | None
- deadline_at: datetime | None
- elapsed_ms: int
- remaining_ms: int | None

InterventionDecision
- action: "none" | "wait" | "probe" | "clarify" | "offer_hint" | "redirect" | "advance" | "wrap_up"
- reason: str
- urgency: "low" | "medium" | "high"
- source: "policy_router" | "evaluator" | "timeout" | "user_request"

RetrievalBundle
- question_context_ref: str | None
- rubric_context_ref: str | None
- resume_context_ref: str | None
- followup_context_ref: str | None
- loaded_at: datetime | None

TranscriptWindow
- recent_segment_ids: list[str]
- rolling_text: str
- last_user_final_at: datetime | None
- silence_ms: int
- user_current_state: "speaking" | "thinking" | "silent" | "stuck" | "unknown"

CodeWindow
- recent_code_event_ids: list[str]
- latest_language: str | None
- latest_snapshot_hash: str | None
- last_run_status: "not_run" | "success" | "runtime_error" | "compile_error" | "test_fail" | "unknown"
- code_progress_state: "not_started" | "exploring" | "implementing" | "debugging" | "stalled" | "done"
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class StateModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        populate_by_name=True,
    )


SessionStatus = Literal["created", "ready", "active", "paused", "completed", "cancelled"]
CurrentGraph = Literal["session", "round", "report"]

StrictnessMode = Literal["strict", "neutral", "coaching", "beginner"]
DifficultyMode = Literal["manual", "auto"]

RoundType = Literal[
    "behavioral",
    "coding",
    "ds_sql",
    "system_design",
    "stats",
    "resume_deep_dive",
]

RoundStatus = Literal[
    "not_started",
    "asking_question",
    "listening",
    "user_thinking",
    "probing",
    "hinting",
    "evaluating",
    "wrapping_up",
    "ended",
]

QuestionStatus = Literal["not_started", "in_progress", "answered", "exhausted"]

ReportStatus = Literal["not_started", "queued", "generating", "ready", "failed"]

PendingControlAction = Literal["none", "pause", "resume", "cancel", "complete"]

InterviewerGoal = Literal[
    "ask_question",
    "acknowledge",
    "clarify",
    "probe",
    "challenge",
    "redirect",
    "hint",
    "summarize",
    "wrap_up",
    "transition",
]

DetectedUserState = Literal[
    "answering",
    "thinking",
    "stuck",
    "off_track",
    "finished",
    "needs_clarification",
    "debugging",
]

UserCurrentState = Literal["speaking", "thinking", "silent", "stuck", "unknown"]

LastRunStatus = Literal[
    "not_run",
    "success",
    "runtime_error",
    "compile_error",
    "test_fail",
    "unknown",
]

CodeProgressState = Literal[
    "not_started",
    "exploring",
    "implementing",
    "debugging",
    "stalled",
    "done",
]

EvaluatorStatus = Literal["on_track", "at_risk", "stalled", "completed", "uncertain"]

InterventionAction = Literal[
    "none",
    "wait",
    "probe",
    "clarify",
    "offer_hint",
    "redirect",
    "advance",
    "wrap_up",
]

InterventionUrgency = Literal["low", "medium", "high"]

InterventionSource = Literal["policy_router", "evaluator", "timeout", "user_request"]
InputEventType = Literal[
    "transcript.partial",
    "transcript.final",
    "code.changed",
    "code.run_completed",
]


class EntityRef(StateModel):
    id: UUID
    type: str


class TimeBudget(StateModel):
    started_at: datetime | None = None
    deadline_at: datetime | None = None
    elapsed_ms: int = 0
    remaining_ms: int | None = None


class InterventionDecision(StateModel):
    action: InterventionAction = "none"
    reason: str = ""
    urgency: InterventionUrgency = "low"
    source: InterventionSource = "policy_router"


class RetrievalBundle(StateModel):
    question_context_ref: str | None = None
    question_context_ref_interviewer: str | None = None
    question_context_ref_evaluator: str | None = None
    question_context_ref_coach: str | None = None
    rubric_context_ref: str | None = None
    rubric_context_ref_interviewer: str | None = None
    rubric_context_ref_evaluator: str | None = None
    rubric_context_ref_coach: str | None = None
    resume_context_ref: str | None = None
    resume_context_ref_interviewer: str | None = None
    resume_context_ref_evaluator: str | None = None
    resume_context_ref_coach: str | None = None
    followup_context_ref: str | None = None
    hidden_answer_ref: str | None = None
    loaded_at: datetime | None = None


class TranscriptWindow(StateModel):
    recent_segment_ids: list[str] = Field(default_factory=list)
    rolling_text: str = ""
    last_user_final_at: datetime | None = None
    silence_ms: int = 0
    user_current_state: UserCurrentState = "unknown"


class CodeWindow(StateModel):
    recent_code_event_ids: list[str] = Field(default_factory=list)
    latest_language: str | None = None
    latest_snapshot_hash: str | None = None
    last_run_status: LastRunStatus = "not_run"
    code_progress_state: CodeProgressState = "not_started"
    last_code_event_at: datetime | None = None
    latest_stdout_excerpt: str | None = None
    latest_stderr_excerpt: str | None = None
    tests_passed: int | None = None
    tests_failed: int | None = None


class DimensionScoreSnapshot(StateModel):
    dimension_key: str
    score_raw: float | None = None
    score_normalized: float | None = None
    weight: float | None = None
    confidence: float | None = None
    evidence_refs: list[str] = Field(default_factory=list)
    reason: str | None = None