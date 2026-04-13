"""
EvaluationState
- latest_live_score: float | None
- latest_confidence: float | None
- off_track_score: float | None
- technical_correctness: float | None
- answer_completeness: float | None
- communication_effectiveness: float | None

- dimension_scores_ref: str | None
- missing_requirements: list[str]
- strengths: list[str]
- weaknesses: list[str]
- uncertainty_notes: list[str]

- recommended_intervention: InterventionDecision | None
"""

from __future__ import annotations

from pydantic import Field

from .shared_types import DimensionScoreSnapshot, InterventionDecision, StateModel


class EvaluationState(StateModel):
    latest_live_score: float | None = None
    latest_confidence: float | None = None
    off_track_score: float | None = None

    technical_correctness: float | None = None
    answer_completeness: float | None = None
    communication_effectiveness: float | None = None

    dimension_scores: list[DimensionScoreSnapshot] = Field(default_factory=list)

    missing_requirements: list[str] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    uncertainty_notes: list[str] = Field(default_factory=list)

    recommended_intervention: InterventionDecision | None = None