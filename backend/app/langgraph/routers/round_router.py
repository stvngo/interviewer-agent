"""Placeholder for app/langgraph/routers/round_router.py"""

from __future__ import annotations

from typing import Literal

from app.langgraph.state import RuntimeState


RoundRoute = Literal[
    "retrieve_question_context",
    "retrieve_resume_context",
    "retrieve_rubric_context",
    "run_interviewer",
    "run_evaluator",
    "decide_intervention",
    "run_coach",
    "advance_question",
    "end_round",
    "wait_for_input",
    "__end__",
]


def route_after_question_selection(state: RuntimeState) -> RoundRoute:
    """
    After selecting a question, load its supporting context.
    """
    return "retrieve_question_context"


def route_after_question_context(state: RuntimeState) -> RoundRoute:
    """
    If there is a resume, load resume context next; otherwise rubric context.
    """
    if state.session.resume_id:
        return "retrieve_resume_context"
    return "retrieve_rubric_context"


def route_after_resume_context(state: RuntimeState) -> RoundRoute:
    return "retrieve_rubric_context"


def route_after_rubric_context(state: RuntimeState) -> RoundRoute:
    return "run_interviewer"


def route_after_interviewer(state: RuntimeState) -> RoundRoute:
    """
    After interviewer speaks, wait for user events in a real runtime.
    In a graph skeleton, we model that as a wait node / interrupt point.
    """
    return "wait_for_input"


def route_after_live_input(state: RuntimeState) -> RoundRoute:
    """
    Once transcript/code processing occurs, evaluate progress.
    """
    return "run_evaluator"


def route_after_evaluator(state: RuntimeState) -> RoundRoute:
    return "decide_intervention"


def route_after_intervention(state: RuntimeState) -> RoundRoute:
    """
    Decide next execution step after intervention policy resolution.
    """
    decision = state.round.latest_intervention_decision

    if decision is None:
        return "run_interviewer"

    if state.round.should_end_round:
        return "end_round"

    if state.round.should_advance_question:
        return "advance_question"

    if decision.action == "offer_hint":
        return "run_coach"

    if decision.action in {"wait"}:
        return "wait_for_input"

    # probe / clarify / redirect / wrap-up-like conversational moves
    return "run_interviewer"


def route_after_coach(state: RuntimeState) -> RoundRoute:
    return "run_interviewer"


def route_after_advance_question(state: RuntimeState) -> RoundRoute:
    """
    Either continue with the next question or end round, depending on state.
    """
    if state.round.should_end_round:
        return "end_round"
    return "retrieve_question_context"


def route_after_end_round(state: RuntimeState) -> RoundRoute:
    return "__end__"