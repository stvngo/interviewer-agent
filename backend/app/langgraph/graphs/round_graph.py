"""Placeholder for app/langgraph/graphs/round_graph.py"""

from __future__ import annotations

from app.langgraph.graphs.behavioral_subgraph import build_behavioral_subgraph
from app.langgraph.graphs.coding_subgraph import build_coding_subgraph


def build_round_graph(*, round_type: str, checkpointer=None, **nodes):
    """
    Dispatch to the appropriate round subgraph builder.

    Supported now:
    - behavioral
    - coding

    Future:
    - ds_sql
    - system_design
    - stats
    """
    if round_type == "behavioral":
        return build_behavioral_subgraph(checkpointer=checkpointer, **nodes)

    if round_type == "coding":
        return build_coding_subgraph(checkpointer=checkpointer, **nodes)

    raise ValueError(f"Unsupported round_type for build_round_graph: {round_type}")