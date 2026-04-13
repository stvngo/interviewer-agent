"""Placeholder module."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated, Literal, Union
from uuid import UUID, uuid4

from pydantic import Field

from app.langgraph.state import (
    DimensionScoreSnapshot,
    EvaluatorStatus,
    InterventionAction,
    InterviewerGoal,
    QuestionStatus,
    RoundStatus,
    SessionStatus,
    StateModel,
)


Channel = Literal[
    "control",
    "session",
    "round",
    "transcript",
    "code",
    "interviewer",
    "evaluator",
    "coach",
    "integrity",
    "report",
]

EventSource = Literal[
    "frontend",
    "backend",
    "orchestrator",
    "interviewer_agent",
    "evaluator_agent",
    "coach_agent",
    "integrity_monitor",
    "stt_provider",
    "tts_provider",
    "code_runner",
]

PersistLevel = Literal["ephemeral", "important", "durable"]


class BaseEventPayload(StateModel):
    pass


class BaseEventEnvelope(StateModel):
    version: Literal["1.0"] = "1.0"
    event_id: UUID = Field(default_factory=uuid4)

    session_id: UUID
    session_round_id: UUID | None = None
    session_question_id: UUID | None = None

    channel: Channel
    event_type: str
    source: EventSource

    seq: int | None = None
    client_event_id: str | None = None
    idempotency_key: str | None = None
    trace_id: str | None = None

    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    persist_level: PersistLevel

    payload: BaseEventPayload


# ----------------------------
# Control events
# ----------------------------

class ControlAckPayload(BaseEventPayload):
    ack_for_client_event_id: str
    accepted: bool = True
    message: str | None = None


class ControlAckEvent(BaseEventEnvelope):
    channel: Literal["control"] = "control"
    event_type: Literal["control.ack"] = "control.ack"
    source: EventSource = "backend"
    persist_level: PersistLevel = "important"
    payload: ControlAckPayload


class ControlErrorPayload(BaseEventPayload):
    code: str
    message: str


class ControlErrorEvent(BaseEventEnvelope):
    channel: Literal["control"] = "control"
    event_type: Literal["control.error"] = "control.error"
    source: EventSource = "backend"
    persist_level: PersistLevel = "important"
    payload: ControlErrorPayload


# ----------------------------
# Session / round lifecycle
# ----------------------------

class SessionStateChangedPayload(BaseEventPayload):
    previous_state: SessionStatus
    new_state: SessionStatus
    reason: str | None = None


class SessionStateChangedEvent(BaseEventEnvelope):
    channel: Literal["session"] = "session"
    event_type: Literal["session.state_changed"] = "session.state_changed"
    source: EventSource = "orchestrator"
    persist_level: PersistLevel = "important"
    payload: SessionStateChangedPayload


class RoundStateChangedPayload(BaseEventPayload):
    previous_state: RoundStatus
    new_state: RoundStatus
    reason: str | None = None


class RoundStateChangedEvent(BaseEventEnvelope):
    channel: Literal["round"] = "round"
    event_type: Literal["round.state_changed"] = "round.state_changed"
    source: EventSource = "orchestrator"
    persist_level: PersistLevel = "important"
    payload: RoundStateChangedPayload


class QuestionAssignedPayload(BaseEventPayload):
    question_id: UUID
    question_order: int
    question_status: QuestionStatus = "in_progress"
    round_type: str
    prompt_preview: str | None = None


class QuestionAssignedEvent(BaseEventEnvelope):
    channel: Literal["round"] = "round"
    event_type: Literal["question.assigned"] = "question.assigned"
    source: EventSource = "orchestrator"
    persist_level: PersistLevel = "important"
    payload: QuestionAssignedPayload


# ----------------------------
# Transcript events
# ----------------------------

class TranscriptPartialPayload(BaseEventPayload):
    speaker: Literal["user", "interviewer"]
    text_delta: str
    is_final: Literal[False] = False
    confidence: float | None = None
    start_ms: int | None = None
    end_ms: int | None = None


class TranscriptPartialEvent(BaseEventEnvelope):
    channel: Literal["transcript"] = "transcript"
    event_type: Literal["transcript.partial"] = "transcript.partial"
    source: EventSource = "stt_provider"
    persist_level: PersistLevel = "ephemeral"
    payload: TranscriptPartialPayload


class TranscriptFinalPayload(BaseEventPayload):
    speaker: Literal["user", "interviewer"]
    text: str
    is_final: Literal[True] = True
    confidence: float | None = None
    start_ms: int | None = None
    end_ms: int | None = None
    pause_before_ms: int | None = None
    pause_after_ms: int | None = None


class TranscriptFinalEvent(BaseEventEnvelope):
    channel: Literal["transcript"] = "transcript"
    event_type: Literal["transcript.final"] = "transcript.final"
    source: EventSource = "stt_provider"
    persist_level: PersistLevel = "durable"
    payload: TranscriptFinalPayload


# ----------------------------
# Code events
# ----------------------------

class CodeChangedPayload(BaseEventPayload):
    language: str
    file_path: str
    content_snapshot: str
    content_hash: str
    diff_summary: dict[str, int] | None = None


class CodeChangedEvent(BaseEventEnvelope):
    channel: Literal["code"] = "code"
    event_type: Literal["code.changed"] = "code.changed"
    source: EventSource = "frontend"
    persist_level: PersistLevel = "important"
    payload: CodeChangedPayload


class CodeRunCompletedPayload(BaseEventPayload):
    stdout: str | None = None
    stderr: str | None = None
    exit_code: int
    runtime_ms: int | None = None
    tests_passed: int | None = None
    tests_failed: int | None = None


class CodeRunCompletedEvent(BaseEventEnvelope):
    channel: Literal["code"] = "code"
    event_type: Literal["code.run_completed"] = "code.run_completed"
    source: EventSource = "code_runner"
    persist_level: PersistLevel = "durable"
    payload: CodeRunCompletedPayload


# ----------------------------
# Interviewer events
# ----------------------------

class InterviewerTurnDecisionPayload(BaseEventPayload):
    should_speak: bool
    response_goal: InterviewerGoal | None = None
    detected_user_state: str | None = None
    interruptible: bool = False
    wait_before_speaking_ms: int = 0
    next_round_state: RoundStatus | None = None


class InterviewerTurnDecisionEvent(BaseEventEnvelope):
    channel: Literal["interviewer"] = "interviewer"
    event_type: Literal["interviewer.turn_decision"] = "interviewer.turn_decision"
    source: EventSource = "interviewer_agent"
    persist_level: PersistLevel = "important"
    payload: InterviewerTurnDecisionPayload


class InterviewerUtteranceCreatedPayload(BaseEventPayload):
    spoken_response: str
    response_goal: InterviewerGoal
    interruptible: bool = False
    wait_before_speaking_ms: int = 0
    state_transition: RoundStatus | None = None
    audio_url: str | None = None


class InterviewerUtteranceCreatedEvent(BaseEventEnvelope):
    channel: Literal["interviewer"] = "interviewer"
    event_type: Literal["interviewer.utterance.created"] = "interviewer.utterance.created"
    source: EventSource = "interviewer_agent"
    persist_level: PersistLevel = "important"
    payload: InterviewerUtteranceCreatedPayload


# ----------------------------
# Evaluator events
# ----------------------------

class EvaluatorSignalUpdatedPayload(BaseEventPayload):
    round_status: EvaluatorStatus
    overall_score_estimate: float | None = None
    confidence: float | None = None
    off_track_score: float | None = None
    recommended_action: InterventionAction = "none"
    top_missing_requirements: list[str] = Field(default_factory=list)
    dimension_scores: list[DimensionScoreSnapshot] = Field(default_factory=list)


class EvaluatorSignalUpdatedEvent(BaseEventEnvelope):
    channel: Literal["evaluator"] = "evaluator"
    event_type: Literal["evaluator.signal.updated"] = "evaluator.signal.updated"
    source: EventSource = "evaluator_agent"
    persist_level: PersistLevel = "important"
    payload: EvaluatorSignalUpdatedPayload


# ----------------------------
# Coach events
# ----------------------------

class CoachHintReadyPayload(BaseEventPayload):
    helpfulness_level: Literal["light", "moderate", "strong"]
    reveal_level: int
    coach_response: str


class CoachHintReadyEvent(BaseEventEnvelope):
    channel: Literal["coach"] = "coach"
    event_type: Literal["coach.hint_ready"] = "coach.hint_ready"
    source: EventSource = "coach_agent"
    persist_level: PersistLevel = "important"
    payload: CoachHintReadyPayload


# ----------------------------
# Report events
# ----------------------------

class ReportReadyPayload(BaseEventPayload):
    report_id: UUID
    status: Literal["ready"] = "ready"


class ReportReadyEvent(BaseEventEnvelope):
    channel: Literal["report"] = "report"
    event_type: Literal["report.ready"] = "report.ready"
    source: EventSource = "backend"
    persist_level: PersistLevel = "durable"
    payload: ReportReadyPayload


AnyRealtimeEvent = Annotated[
    Union[
        ControlAckEvent,
        ControlErrorEvent,
        SessionStateChangedEvent,
        RoundStateChangedEvent,
        QuestionAssignedEvent,
        TranscriptPartialEvent,
        TranscriptFinalEvent,
        CodeChangedEvent,
        CodeRunCompletedEvent,
        InterviewerTurnDecisionEvent,
        InterviewerUtteranceCreatedEvent,
        EvaluatorSignalUpdatedEvent,
        CoachHintReadyEvent,
        ReportReadyEvent,
    ],
    Field(discriminator="event_type"),
]