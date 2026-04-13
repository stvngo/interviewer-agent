"""
Purpose: Load question prompt, hints, followups, and allowed hidden metadata.

Calls
- retrieval_service
- question_service

Writes
- retrieval_bundle.question_context_ref

Emits
- optional internal retrieval event

DB writes
- none
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.langgraph.runtime.node_contracts import NodeExecutionContext, NodeResult
from app.langgraph.state import RuntimeState


def retrieve_question_context(
    state: RuntimeState,
    *,
    retrieval_service: Any,
    question_service: Any,
    ctx: NodeExecutionContext | None = None,
) -> NodeResult:
    """
    Load question prompt, hidden solution metadata, hint ladder, and followup references.

    Expected methods:
    - question_service.get_question_runtime_packet(question_id: str) -> dict
    - retrieval_service.package_question_context(question_packet: dict, target: str) -> dict
    """
    ctx = ctx or NodeExecutionContext(actor="system")
    new_state = state.model_copy(deep=True)
    warnings: list[str] = []

    if not new_state.round.question_id:
        warnings.append("No question_id set before retrieve_question_context.")
        return NodeResult(state=new_state, warnings=warnings)

    question_packet = question_service.get_question_runtime_packet(new_state.round.question_id)
    packaged_interviewer = retrieval_service.package_question_context(
        question_packet=question_packet,
        target="interviewer",
    )
    packaged_evaluator = retrieval_service.package_question_context(
        question_packet=question_packet,
        target="evaluator",
    )
    packaged_coach = retrieval_service.package_question_context(
        question_packet=question_packet,
        target="coach",
    )

    new_state.round.retrieval_bundle.question_context_ref = packaged_interviewer["context_ref"]
    new_state.round.retrieval_bundle.question_context_ref_interviewer = packaged_interviewer["context_ref"]
    new_state.round.retrieval_bundle.question_context_ref_evaluator = packaged_evaluator["context_ref"]
    new_state.round.retrieval_bundle.question_context_ref_coach = packaged_coach["context_ref"]
    new_state.round.retrieval_bundle.followup_context_ref = packaged_interviewer.get("followup_context_ref")
    new_state.round.retrieval_bundle.hidden_answer_ref = packaged_evaluator.get("hidden_answer_ref")
    new_state.round.retrieval_bundle.loaded_at = datetime.now(timezone.utc)

    return NodeResult(state=new_state, warnings=warnings)