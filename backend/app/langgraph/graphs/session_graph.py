"""Placeholder for app/langgraph/graphs/session_graph.py"""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from app.langgraph.routers.session_router import (
    route_after_report,
    route_after_round_completion,
    route_to_round_subgraph,
)
from app.langgraph.state import RuntimeState


def build_session_graph(
    *,
    load_session_context_node,
    behavioral_subgraph_runner,
    coding_subgraph_runner,
    ds_sql_subgraph_runner=None,
    system_design_subgraph_runner=None,
    generate_report_node=None,
    checkpointer=None,
):
    """
    Top-level session graph.

    This graph:
    1. loads runtime session context
    2. enters the correct round subgraph
    3. determines whether more rounds remain
    4. generates the report
    5. ends
    """
    graph = StateGraph(RuntimeState)

    graph.add_node("load_session_context", load_session_context_node)
    graph.add_node("behavioral_subgraph", behavioral_subgraph_runner)
    graph.add_node("coding_subgraph", coding_subgraph_runner)
    graph.add_node("generate_report", generate_report_node)

    if ds_sql_subgraph_runner is not None:
        graph.add_node("ds_sql_subgraph", ds_sql_subgraph_runner)

    if system_design_subgraph_runner is not None:
        graph.add_node("system_design_subgraph", system_design_subgraph_runner)

    graph.add_edge(START, "load_session_context")

    graph.add_conditional_edges(
        "load_session_context",
        route_to_round_subgraph,
        {
            "behavioral_subgraph": "behavioral_subgraph",
            "coding_subgraph": "coding_subgraph",
            "ds_sql_subgraph": "ds_sql_subgraph" if ds_sql_subgraph_runner else "generate_report",
            "system_design_subgraph": "system_design_subgraph" if system_design_subgraph_runner else "generate_report",
            "generate_report": "generate_report",
        },
    )

    for node_name in ["behavioral_subgraph", "coding_subgraph"]:
        graph.add_conditional_edges(
            node_name,
            route_after_round_completion,
            {
                "behavioral_subgraph": "behavioral_subgraph",
                "coding_subgraph": "coding_subgraph",
                "ds_sql_subgraph": "ds_sql_subgraph" if ds_sql_subgraph_runner else "generate_report",
                "system_design_subgraph": "system_design_subgraph" if system_design_subgraph_runner else "generate_report",
                "generate_report": "generate_report",
            },
        )

    if ds_sql_subgraph_runner is not None:
        graph.add_conditional_edges(
            "ds_sql_subgraph",
            route_after_round_completion,
            {
                "behavioral_subgraph": "behavioral_subgraph",
                "coding_subgraph": "coding_subgraph",
                "ds_sql_subgraph": "ds_sql_subgraph",
                "system_design_subgraph": "system_design_subgraph" if system_design_subgraph_runner else "generate_report",
                "generate_report": "generate_report",
            },
        )

    if system_design_subgraph_runner is not None:
        graph.add_conditional_edges(
            "system_design_subgraph",
            route_after_round_completion,
            {
                "behavioral_subgraph": "behavioral_subgraph",
                "coding_subgraph": "coding_subgraph",
                "ds_sql_subgraph": "ds_sql_subgraph" if ds_sql_subgraph_runner else "generate_report",
                "system_design_subgraph": "system_design_subgraph",
                "generate_report": "generate_report",
            },
        )

    graph.add_conditional_edges(
        "generate_report",
        route_after_report,
        {
            "__end__": END,
            "generate_report": "generate_report",
        },
    )

    return graph.compile(checkpointer=checkpointer)