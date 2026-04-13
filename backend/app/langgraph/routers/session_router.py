"""Session-level routing functions for the top-level session graph."""

from __future__ import annotations

from typing import Literal

from app.langgraph.state import RuntimeState

SessionRoute = Literal[
    "behavioral_subgraph",
    "coding_subgraph",
    "ds_sql_subgraph",
    "system_design_subgraph",
    "generate_report",
    "__end__",
]

_ROUND_TYPE_TO_SUBGRAPH: dict[str, SessionRoute] = {
    "behavioral": "behavioral_subgraph",
    "coding": "coding_subgraph",
    "ds_sql": "ds_sql_subgraph",
    "system_design": "system_design_subgraph",
}


def route_to_round_subgraph(state: RuntimeState) -> SessionRoute:
    """
    After loading session context, route to the correct round subgraph
    based on the current round type.
    """
    return _ROUND_TYPE_TO_SUBGRAPH.get(
        state.round.round_type,
        "generate_report",
    )


def route_after_round_completion(state: RuntimeState) -> SessionRoute:
    """
    After a round subgraph finishes, determine whether to start the next
    round or proceed to report generation.

    Uses current_round_order and total_round_count to decide.
    """
    current_order = state.session.current_round_order or 0
    total = state.session.total_round_count

    if current_order + 1 < total:
        next_round_type = state.round.round_type
        return _ROUND_TYPE_TO_SUBGRAPH.get(next_round_type, "generate_report")

    return "generate_report"


def route_after_report(state: RuntimeState) -> Literal["__end__", "generate_report"]:
    """
    After report generation, check if the report is ready.
    If ready or failed, end the session graph. Otherwise retry.
    """
    if state.session.current_report_status in ("ready", "failed"):
        return "__end__"
    return "generate_report"
