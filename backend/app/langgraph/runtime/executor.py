"""GraphExecutor: wires node functions to concrete services/agents and returns compiled graphs."""

from __future__ import annotations

import logging
from typing import Any

from app.langgraph.graphs.round_graph import build_round_graph
from app.langgraph.graphs.session_graph import build_session_graph
from app.langgraph.nodes.advance_question import advance_question
from app.langgraph.nodes.decide_intervention import decide_intervention
from app.langgraph.nodes.end_round import end_round
from app.langgraph.nodes.generate_report import generate_report
from app.langgraph.nodes.load_session_context import load_session_context
from app.langgraph.nodes.process_code_signal import process_code_signal
from app.langgraph.nodes.process_transcript import process_transcript
from app.langgraph.nodes.retrieve_question_context import retrieve_question_context
from app.langgraph.nodes.retrieve_resume_context import retrieve_resume_context
from app.langgraph.nodes.retrieve_rubric_context import retrieve_rubric_context
from app.langgraph.nodes.run_coach import run_coach
from app.langgraph.nodes.run_evaluator import run_evaluator
from app.langgraph.nodes.run_interviewer import run_interviewer
from app.langgraph.nodes.select_question import select_question
from app.langgraph.nodes.wait_for_input import wait_for_input
from app.langgraph.runtime.node_contracts import NodeResult

logger = logging.getLogger(__name__)


def _emit_node_result(result: NodeResult) -> None:
    """Emit events and persistence intents via LangGraph stream writer when available."""
    try:
        from langgraph.config import get_stream_writer

        writer = get_stream_writer()
        for event in result.emitted_events:
            writer({"type": "event", "payload": event.model_dump(mode="json")})
        for intent in result.persistence_intents:
            writer({"type": "persist", "payload": intent.model_dump(mode="json")})
        for warning in result.warnings:
            writer({"type": "warning", "message": warning})
    except Exception:
        for warning in result.warnings:
            logger.warning("Node warning: %s", warning)


class GraphExecutor:
    """
    Wires node functions to concrete services/agents and returns compiled graphs.

    This class keeps dependency injection in one place.
    """

    def __init__(
        self,
        *,
        session_service: Any,
        template_service: Any,
        resume_service: Any,
        question_service: Any,
        rubric_service: Any,
        transcript_service: Any,
        code_event_service: Any,
        scoring_service: Any,
        report_service: Any,
        retrieval_service: Any,
        interviewer_agent: Any,
        evaluator_agent: Any,
        coach_agent: Any,
        checkpointer: Any = None,
    ) -> None:
        self.session_service = session_service
        self.template_service = template_service
        self.resume_service = resume_service
        self.question_service = question_service
        self.rubric_service = rubric_service
        self.transcript_service = transcript_service
        self.code_event_service = code_event_service
        self.scoring_service = scoring_service
        self.report_service = report_service
        self.retrieval_service = retrieval_service
        self.interviewer_agent = interviewer_agent
        self.evaluator_agent = evaluator_agent
        self.coach_agent = coach_agent
        self.checkpointer = checkpointer

    # -------------------------
    # Node wrappers
    # -------------------------

    def load_session_context_node(self, state):
        result = load_session_context(
            state,
            session_service=self.session_service,
            template_service=self.template_service,
            resume_service=self.resume_service,
        )
        _emit_node_result(result)
        return result.state

    def select_question_node(self, state):
        result = select_question(
            state,
            question_service=self.question_service,
            session_service=self.session_service,
        )
        _emit_node_result(result)
        return result.state

    def retrieve_question_context_node(self, state):
        result = retrieve_question_context(
            state,
            retrieval_service=self.retrieval_service,
            question_service=self.question_service,
        )
        _emit_node_result(result)
        return result.state

    def retrieve_resume_context_node(self, state):
        result = retrieve_resume_context(
            state,
            retrieval_service=self.retrieval_service,
            resume_service=self.resume_service,
        )
        _emit_node_result(result)
        return result.state

    def retrieve_rubric_context_node(self, state):
        result = retrieve_rubric_context(
            state,
            retrieval_service=self.retrieval_service,
            rubric_service=self.rubric_service,
        )
        _emit_node_result(result)
        return result.state

    def run_interviewer_node(self, state):
        result = run_interviewer(
            state,
            interviewer_agent=self.interviewer_agent,
        )
        _emit_node_result(result)
        return result.state

    def wait_for_input_node(self, state):
        result = wait_for_input(state)
        _emit_node_result(result)
        return result.state

    def run_evaluator_node(self, state):
        result = run_evaluator(
            state,
            evaluator_agent=self.evaluator_agent,
            scoring_service=self.scoring_service,
        )
        _emit_node_result(result)
        return result.state

    def decide_intervention_node(self, state):
        result = decide_intervention(
            state,
            template_service=self.template_service,
        )
        _emit_node_result(result)
        return result.state

    def run_coach_node(self, state):
        result = run_coach(
            state,
            coach_agent=self.coach_agent,
        )
        _emit_node_result(result)
        return result.state

    def advance_question_node(self, state):
        result = advance_question(
            state,
            session_service=self.session_service,
            question_service=self.question_service,
        )
        _emit_node_result(result)
        return result.state

    def end_round_node(self, state):
        result = end_round(
            state,
            scoring_service=self.scoring_service,
            session_service=self.session_service,
        )
        _emit_node_result(result)
        return result.state

    def generate_report_node(self, state):
        result = generate_report(
            state,
            report_service=self.report_service,
            scoring_service=self.scoring_service,
        )
        _emit_node_result(result)
        return result.state

    # -------------------------
    # Graph builders
    # -------------------------

    def build_behavioral_graph(self):
        return build_round_graph(
            round_type="behavioral",
            checkpointer=self.checkpointer,
            select_question_node=self.select_question_node,
            retrieve_question_context_node=self.retrieve_question_context_node,
            retrieve_resume_context_node=self.retrieve_resume_context_node,
            retrieve_rubric_context_node=self.retrieve_rubric_context_node,
            run_interviewer_node=self.run_interviewer_node,
            wait_for_input_node=self.wait_for_input_node,
            run_evaluator_node=self.run_evaluator_node,
            decide_intervention_node=self.decide_intervention_node,
            run_coach_node=self.run_coach_node,
            advance_question_node=self.advance_question_node,
            end_round_node=self.end_round_node,
        )

    def build_coding_graph(self):
        return build_round_graph(
            round_type="coding",
            checkpointer=self.checkpointer,
            select_question_node=self.select_question_node,
            retrieve_question_context_node=self.retrieve_question_context_node,
            retrieve_resume_context_node=self.retrieve_resume_context_node,
            retrieve_rubric_context_node=self.retrieve_rubric_context_node,
            run_interviewer_node=self.run_interviewer_node,
            wait_for_input_node=self.wait_for_input_node,
            run_evaluator_node=self.run_evaluator_node,
            decide_intervention_node=self.decide_intervention_node,
            run_coach_node=self.run_coach_node,
            advance_question_node=self.advance_question_node,
            end_round_node=self.end_round_node,
        )

    def build_session_graph(self):
        behavioral_graph = self.build_behavioral_graph()
        coding_graph = self.build_coding_graph()

        def behavioral_runner(state):
            return behavioral_graph.invoke(state)

        def coding_runner(state):
            return coding_graph.invoke(state)

        return build_session_graph(
            load_session_context_node=self.load_session_context_node,
            behavioral_subgraph_runner=behavioral_runner,
            coding_subgraph_runner=coding_runner,
            generate_report_node=self.generate_report_node,
            checkpointer=self.checkpointer,
        )
