"""
Purpose: Create post-session report.

Calls
- report_service
- scoring_service

Writes
- report.generating
- report.ready

Emits
- feedback_reports
- final scorecards if session-scoped
"""

from __future__ import annotations

from typing import Any

from app.langgraph.runtime.node_contracts import NodeExecutionContext, NodeResult, PersistenceIntent
from app.langgraph.state import RuntimeState
from app.realtime.event_contracts import ReportReadyEvent, ReportReadyPayload


def generate_report(
    state: RuntimeState,
    *,
    report_service: Any,
    scoring_service: Any,
    ctx: NodeExecutionContext | None = None,
) -> NodeResult:
    """
    Generate and persist the final feedback report.
    """
    ctx = ctx or NodeExecutionContext(actor="system")
    new_state = state.model_copy(deep=True)

    new_state.session.current_report_status = "generating"

    final_summary = scoring_service.finalize_session_summary(
        session_id=new_state.session.session_id,
    )

    report = report_service.generate_session_report(
        session_id=new_state.session.session_id,
        session_summary=final_summary,
    )

    new_state.session.current_report_status = "ready"

    emitted = [
        ReportReadyEvent(
            session_id=new_state.session.session_id,
            session_round_id=new_state.round.round_id,
            session_question_id=new_state.round.session_question_id,
            channel="report",
            event_type="report.ready",
            source="backend",
            persist_level="durable",
            payload=ReportReadyPayload(
                report_id=report["report_id"],
                status="ready",
            ),
        )
    ]

    intents = [
        PersistenceIntent(
            target="feedback_reports",
            operation="append",
            description="Persisted session feedback report.",
            ref_id=report["report_id"],
        ),
        PersistenceIntent(
            target="session_events",
            operation="append",
            description="Recorded report generation completion.",
            ref_id=new_state.session.session_id,
        ),
    ]

    return NodeResult(
        state=new_state,
        emitted_events=emitted,
        persistence_intents=intents,
    )