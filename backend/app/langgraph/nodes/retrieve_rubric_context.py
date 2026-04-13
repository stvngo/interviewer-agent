"""
Purpose: Load rubric summary for interviewer or full rubric for evaluator.

Calls
- rubric_service
- retrieval_service

Writes
- retrieval_bundle.rubric_context_ref
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.langgraph.runtime.node_contracts import NodeExecutionContext, NodeResult
from app.langgraph.state import RuntimeState


def retrieve_rubric_context(
    state: RuntimeState,
    *,
    retrieval_service: Any,
    rubric_service: Any,
    ctx: NodeExecutionContext | None = None,
) -> NodeResult:
    """
    Load rubric context for interviewer and evaluator usage.

    Expected methods:
    - rubric_service.get_rubric_runtime_packet(round_type: str) -> dict
    - retrieval_service.package_rubric_context(rubric_packet: dict, target: str) -> dict
    """
    ctx = ctx or NodeExecutionContext(actor="system")
    new_state = state.model_copy(deep=True)
    warnings: list[str] = []

    rubric_packet = rubric_service.get_rubric_runtime_packet(new_state.round.round_type)
    packaged = retrieval_service.package_rubric_context(
        rubric_packet=rubric_packet,
        target="interviewer",
    )

    new_state.round.retrieval_bundle.rubric_context_ref = packaged["context_ref"]
    new_state.round.retrieval_bundle.loaded_at = datetime.now(timezone.utc)

    return NodeResult(state=new_state, warnings=warnings)