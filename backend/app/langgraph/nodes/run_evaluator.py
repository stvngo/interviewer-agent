"""
Purpose: Produce live evaluation and intervention recommendation.

Reads
- transcript window
- code window
- question/rubric context
- hint history

Calls
- evaluator_agent

Writes
- EvaluationState
- latest_evaluator_status

Emits
- evaluator.signal.updated

DB writes
- live_score_snapshots
"""

from __future__ import annotations

from typing import Any

from app.langgraph.runtime.node_contracts import NodeExecutionContext, NodeResult, PersistenceIntent
from app.langgraph.state import DimensionScoreSnapshot, InterventionDecision, RuntimeState
from app.realtime.event_contracts import (
    EvaluatorSignalUpdatedEvent,
    EvaluatorSignalUpdatedPayload,
)


def run_evaluator(
    state: RuntimeState,
    *,
    evaluator_agent: Any,
    scoring_service: Any,
    ctx: NodeExecutionContext | None = None,
) -> NodeResult:
    """
    Compute live evaluation state and intervention recommendations.

    Expected methods:
    - evaluator_agent.invoke(payload: dict) -> dict
    - scoring_service.persist_live_snapshot(...) -> dict
    """

    ctx = ctx or NodeExecutionContext(actor="agent")
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

    result = evaluator_agent.invoke(agent_input)

    new_state.round.latest_evaluator_status = result.get("round_status", "uncertain")
    new_state.evaluation.latest_live_score = result.get("overall_estimate", {}).get("score_normalized")
    new_state.evaluation.latest_confidence = result.get("overall_estimate", {}).get("confidence")
    new_state.evaluation.off_track_score = result.get("off_track_score")
    new_state.evaluation.technical_correctness = result.get("technical_correctness")
    new_state.evaluation.answer_completeness = result.get("answer_completeness")
    new_state.evaluation.communication_effectiveness = result.get("communication_effectiveness")
    new_state.evaluation.missing_requirements = result.get("missing_requirements", [])
    new_state.evaluation.strengths = result.get("strengths", [])
    new_state.evaluation.weaknesses = result.get("weaknesses", [])
    new_state.evaluation.uncertainty_notes = result.get("uncertainty_notes", [])

    new_state.evaluation.dimension_scores = [
        DimensionScoreSnapshot(**item) for item in result.get("dimension_scores", [])
    ]

    if result.get("intervention_recommendation"):
        new_state.evaluation.recommended_intervention = InterventionDecision(
            action=result["intervention_recommendation"].get("action", "none"),
            reason=result["intervention_recommendation"].get("reason", ""),
            urgency=result["intervention_recommendation"].get("urgency", "low"),
            source="evaluator",
        )

    snapshot = scoring_service.persist_live_snapshot(
        session_id=new_state.session.session_id,
        round_id=new_state.round.round_id,
        session_question_id=new_state.round.session_question_id,
        status=new_state.round.latest_evaluator_status,
        overall_score=new_state.evaluation.latest_live_score,
        confidence=new_state.evaluation.latest_confidence,
        off_track_score=new_state.evaluation.off_track_score,
        dimension_scores=[d.model_dump() for d in new_state.evaluation.dimension_scores],
        intervention_recommendation=(
            new_state.evaluation.recommended_intervention.model_dump()
            if new_state.evaluation.recommended_intervention
            else None
        ),
        raw_output=result,
    )

    new_state.round.evaluator_checkpoint_counter += 1

    emitted_events.append(
        EvaluatorSignalUpdatedEvent(
            session_id=new_state.session.session_id,
            session_round_id=new_state.round.round_id,
            session_question_id=new_state.round.session_question_id,
            channel="evaluator",
            event_type="evaluator.signal.updated",
            source="evaluator_agent",
            persist_level="important",
            payload=EvaluatorSignalUpdatedPayload(
                round_status=new_state.round.latest_evaluator_status,
                overall_score_estimate=new_state.evaluation.latest_live_score,
                confidence=new_state.evaluation.latest_confidence,
                off_track_score=new_state.evaluation.off_track_score,
                recommended_action=(
                    new_state.evaluation.recommended_intervention.action
                    if new_state.evaluation.recommended_intervention
                    else "none"
                ),
                top_missing_requirements=new_state.evaluation.missing_requirements,
                dimension_scores=new_state.evaluation.dimension_scores,
            ),
        )
    )

    persistence_intents.extend(
        [
            PersistenceIntent(
                target="live_score_snapshots",
                operation="append",
                description="Persisted evaluator live score snapshot.",
                ref_id=snapshot["snapshot_id"],
            ),
            PersistenceIntent(
                target="session_events",
                operation="append",
                description="Recorded evaluator signal update.",
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