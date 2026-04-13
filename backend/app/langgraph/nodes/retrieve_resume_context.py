"""
Purpose: Load only the relevant resume context for the active question/round.

Calls
- resume_service
- retrieval_service

Writes
- retrieval_bundle.resume_context_ref
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.langgraph.runtime.node_contracts import NodeExecutionContext, NodeResult
from app.langgraph.state import RuntimeState


def retrieve_resume_context(
    state: RuntimeState,
    *,
    retrieval_service: Any,
    resume_service: Any,
    ctx: NodeExecutionContext | None = None,
) -> NodeResult:
    """
    Load only the relevant resume context for the active question/round.

    Expected methods:
    - resume_service.get_resume_runtime_context(resume_id: str) -> dict
    - retrieval_service.package_resume_context(...) -> dict
    """
    ctx = ctx or NodeExecutionContext(actor="system")
    new_state = state.model_copy(deep=True)
    warnings: list[str] = []

    if not new_state.session.resume_id:
        warnings.append("No resume_id present; skipping resume retrieval.")
        return NodeResult(state=new_state, warnings=warnings)

    if not new_state.round.question_id:
        warnings.append("No question_id present; resume retrieval may be less relevant.")

    resume_ctx = resume_service.get_resume_runtime_context(new_state.session.resume_id)
    packaged = retrieval_service.package_resume_context(
        resume_context=resume_ctx,
        target_role=new_state.session.target_role,
        round_type=new_state.round.round_type,
        question_id=new_state.round.question_id,
    )

    new_state.round.retrieval_bundle.resume_context_ref = packaged["context_ref"]
    new_state.round.retrieval_bundle.loaded_at = datetime.now(timezone.utc)

    return NodeResult(state=new_state, warnings=warnings)