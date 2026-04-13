"""
Purpose: Turn evaluator recommendation + policy into final action.

Calls
- pure policy/router logic
- maybe template_service for policy lookup

Writes
- latest_intervention_decision
- should_advance_question
- should_end_round

Emits
- policy.intervention_decided

DB writes
- optional session_events


INTERVENTION AUTHORITY SPECIFICATION
Evaluator can recommend:
- wait
- probe
- clarify
- offer_hint
- redirect
- advance
- wrap_up

Policy router decides based on:
- template strictness
- round type
- hint budget
- elapsed time
- follow-up depth
- user explicit requests
- evaluator confidence

Interviewer only executesthe chosen strategy:
evaluator output
-> policy/router
-> interviewer turn generation
-> event emission
"""

from __future__ import annotations

from typing import Any

from app.langgraph.runtime.node_contracts import NodeExecutionContext, NodeResult, PersistenceIntent
from app.langgraph.state import InterventionDecision, RuntimeState


def decide_intervention(
    state: RuntimeState,
    *,
    template_service: Any,
    ctx: NodeExecutionContext | None = None,
) -> NodeResult:
    """
    Convert evaluator recommendation + template policy into final next action.

    Expected service method:
    - template_service.resolve_intervention_policy(...) -> dict
    """

    ctx = ctx or NodeExecutionContext(actor="system")
    new_state = state.model_copy(deep=True)
    emitted_events = []
    persistence_intents = []
    warnings = []

    recommendation = (
        new_state.evaluation.recommended_intervention.model_dump()
        if new_state.evaluation.recommended_intervention
        else {"action": "none", "reason": "No evaluator recommendation.", "urgency": "low", "source": "evaluator"}
    )

    resolved = template_service.resolve_intervention_policy(
        strictness_mode=new_state.session.strictness_mode,
        round_type=new_state.round.round_type,
        hint_budget_remaining=new_state.round.hint_budget_remaining,
        hint_level_used=new_state.round.hint_level_used,
        max_hint_level_allowed=new_state.round.max_hint_level_allowed,
        followup_depth_used=new_state.round.followup_depth_used,
        max_followup_depth=new_state.round.max_followup_depth,
        question_status=new_state.round.question_status,
        round_status=new_state.round.round_status,
        evaluator_recommendation=recommendation,
        user_requested_hint=new_state.round.user_requested_hint,
        elapsed_ms=new_state.round.round_time_budget.elapsed_ms,
        remaining_ms=new_state.round.round_time_budget.remaining_ms,
    )

    decision = InterventionDecision(
        action=resolved.get("action", "none"),
        reason=resolved.get("reason", ""),
        urgency=resolved.get("urgency", "low"),
        source="policy_router",
    )

    new_state.round.latest_intervention_decision = decision
    new_state.round.should_advance_question = decision.action == "advance"
    new_state.round.should_end_round = decision.action == "wrap_up"

    if decision.action == "offer_hint":
        new_state.round.round_status = "hinting"
    elif decision.action in {"probe", "clarify", "redirect"}:
        new_state.round.round_status = "probing"
    elif decision.action == "wait":
        new_state.round.round_status = "user_thinking"

    persistence_intents.append(
        PersistenceIntent(
            target="session_events",
            operation="append",
            description="Recorded final intervention decision from policy router.",
            ref_id=new_state.session.session_id,
        )
    )

    if decision.action == "offer_hint" and new_state.round.hint_budget_remaining <= 0:
        warnings.append("Policy chose offer_hint but hint budget is exhausted.")

    return NodeResult(
        state=new_state,
        emitted_events=emitted_events,
        persistence_intents=persistence_intents,
        warnings=warnings,
    )