"""
SessionGraphState
- session_id: str
- user_id: str
- template_id: str | None
- resume_id: str | None

- session_status: "created" | "ready" | "active" | "paused" | "completed" | "cancelled"
- current_graph: "session" | "round" | "report"
- current_round_id: str | None
- current_round_order: int | None
- total_round_count: int

- target_role: str | None
- interview_track: str | None
- strictness_mode: "strict" | "neutral" | "coaching" | "beginner"
- difficulty_mode: "manual" | "auto"
- voice_enabled: bool
- video_enabled: bool
- integrity_enabled: bool

- session_time_budget: TimeBudget
- current_round_summary_ref: str | None
- current_report_status: "not_started" | "queued" | "generating" | "ready" | "failed"

- latest_error: str | None
- pending_control_action: "none" | "pause" | "resume" | "cancel" | "complete"
"""

from __future__ import annotations

from uuid import UUID

from pydantic import Field

from .shared_types import (
    CurrentGraph,
    DifficultyMode,
    PendingControlAction,
    ReportStatus,
    SessionStatus,
    StateModel,
    StrictnessMode,
    TimeBudget,
)


class SessionGraphState(StateModel):
    session_id: UUID
    user_id: UUID
    template_id: UUID | None = None
    resume_id: UUID | None = None

    session_status: SessionStatus = "created"
    current_graph: CurrentGraph = "session"
    current_round_id: UUID | None = None
    current_round_order: int | None = None
    total_round_count: int = 0

    target_role: str | None = None
    interview_track: str | None = None
    strictness_mode: StrictnessMode = "neutral"
    difficulty_mode: DifficultyMode = "manual"

    voice_enabled: bool = True
    video_enabled: bool = False
    integrity_enabled: bool = False

    session_time_budget: TimeBudget = Field(default_factory=TimeBudget)
    current_round_summary_ref: str | None = None
    current_report_status: ReportStatus = "not_started"

    latest_error: str | None = None
    pending_control_action: PendingControlAction = "none"