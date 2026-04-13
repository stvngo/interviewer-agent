"""Placeholder for app/langgraph/graphs/behavioral_subgraph.py"""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from app.langgraph.routers.round_router import (
    route_after_advance_question,
    route_after_coach,
    route_after_evaluator,
    route_after_intervention,
    route_after_question_context,
    route_after_question_selection,
    route_after_resume_context,
    route_after_rubric_context,
    route_after_interviewer,
    route_after_live_input,
    route_after_end_round,
)
from app.langgraph.state import RuntimeState


def build_behavioral_subgraph(
    *,
    select_question_node,
    retrieve_question_context_node,
    retrieve_resume_context_node,
    retrieve_rubric_context_node,
    run_interviewer_node,
    wait_for_input_node,
    run_evaluator_node,
    decide_intervention_node,
    run_coach_node,
    advance_question_node,
    end_round_node,
    checkpointer=None,
):
    """
    Behavioral interview subgraph.

    This graph is intentionally generic enough that it can later share most of
    its structure with other round types while differing in prompts, rubric,
    and policy.
    """
    graph = StateGraph(RuntimeState)

    graph.add_node("select_question", select_question_node)
    graph.add_node("retrieve_question_context", retrieve_question_context_node)
    graph.add_node("retrieve_resume_context", retrieve_resume_context_node)
    graph.add_node("retrieve_rubric_context", retrieve_rubric_context_node)
    graph.add_node("run_interviewer", run_interviewer_node)
    graph.add_node("wait_for_input", wait_for_input_node)
    graph.add_node("run_evaluator", run_evaluator_node)
    graph.add_node("decide_intervention", decide_intervention_node)
    graph.add_node("run_coach", run_coach_node)
    graph.add_node("advance_question", advance_question_node)
    graph.add_node("end_round", end_round_node)

    graph.add_edge(START, "select_question")

    graph.add_conditional_edges(
        "select_question",
        route_after_question_selection,
        {
            "retrieve_question_context": "retrieve_question_context",
        },
    )

    graph.add_conditional_edges(
        "retrieve_question_context",
        route_after_question_context,
        {
            "retrieve_resume_context": "retrieve_resume_context",
            "retrieve_rubric_context": "retrieve_rubric_context",
        },
    )

    graph.add_conditional_edges(
        "retrieve_resume_context",
        route_after_resume_context,
        {
            "retrieve_rubric_context": "retrieve_rubric_context",
        },
    )

    graph.add_conditional_edges(
        "retrieve_rubric_context",
        route_after_rubric_context,
        {
            "run_interviewer": "run_interviewer",
        },
    )

    graph.add_conditional_edges(
        "run_interviewer",
        route_after_interviewer,
        {
            "wait_for_input": "wait_for_input",
        },
    )

    graph.add_conditional_edges(
        "wait_for_input",
        route_after_live_input,
        {
            "run_evaluator": "run_evaluator",
        },
    )

    graph.add_conditional_edges(
        "run_evaluator",
        route_after_evaluator,
        {
            "decide_intervention": "decide_intervention",
        },
    )

    graph.add_conditional_edges(
        "decide_intervention",
        route_after_intervention,
        {
            "run_interviewer": "run_interviewer",
            "run_coach": "run_coach",
            "advance_question": "advance_question",
            "end_round": "end_round",
            "wait_for_input": "wait_for_input",
        },
    )

    graph.add_conditional_edges(
        "run_coach",
        route_after_coach,
        {
            "run_interviewer": "run_interviewer",
        },
    )

    graph.add_conditional_edges(
        "advance_question",
        route_after_advance_question,
        {
            "retrieve_question_context": "retrieve_question_context",
            "end_round": "end_round",
        },
    )

    graph.add_conditional_edges(
        "end_round",
        route_after_end_round,
        {
            "__end__": END,
        },
    )

    return graph.compile(checkpointer=checkpointer)