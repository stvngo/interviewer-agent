"""GraphExecutor: wires node functions to concrete services/agents and returns compiled graphs."""

from __future__ import annotations

import logging
from typing import Any

from langgraph.types import Command

from app.langgraph.checkpointing.thread_config import build_thread_config
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
from app.langgraph.runtime.persistence_sink import FilePersistenceSink
from app.langgraph.state import RuntimeState
from app.realtime.event_contracts import (
    CodeChangedEvent,
    CodeChangedPayload,
    CodeRunCompletedEvent,
    CodeRunCompletedPayload,
    TranscriptFinalEvent,
    TranscriptFinalPayload,
    TranscriptPartialEvent,
    TranscriptPartialPayload,
)

logger = logging.getLogger(__name__)


def _emit_node_result(result: NodeResult, *, persistence_sink: Any | None = None, node_name: str | None = None) -> None:
    """Emit events and persistence intents via LangGraph stream writer when available."""
    try:
        from langgraph.config import get_stream_writer

        writer = get_stream_writer()
        for event in result.emitted_events:
            writer({"type": "event", "payload": event.model_dump(mode="json")})
        for intent in result.persistence_intents:
            writer({"type": "persist", "payload": intent.model_dump(mode="json")})
            if persistence_sink is not None:
                persistence_sink.record(intent, node_name=node_name)
        for warning in result.warnings:
            writer({"type": "warning", "message": warning})
    except Exception:
        for intent in result.persistence_intents:
            if persistence_sink is not None:
                persistence_sink.record(intent, node_name=node_name)
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
        persistence_sink: Any | None = None,
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
        self.persistence_sink = persistence_sink or FilePersistenceSink()

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
        _emit_node_result(result, persistence_sink=self.persistence_sink, node_name="load_session_context")
        return result.state

    def select_question_node(self, state):
        result = select_question(
            state,
            question_service=self.question_service,
            session_service=self.session_service,
        )
        _emit_node_result(result, persistence_sink=self.persistence_sink, node_name="select_question")
        return result.state

    def retrieve_question_context_node(self, state):
        result = retrieve_question_context(
            state,
            retrieval_service=self.retrieval_service,
            question_service=self.question_service,
        )
        _emit_node_result(result, persistence_sink=self.persistence_sink, node_name="retrieve_question_context")
        return result.state

    def retrieve_resume_context_node(self, state):
        result = retrieve_resume_context(
            state,
            retrieval_service=self.retrieval_service,
            resume_service=self.resume_service,
        )
        _emit_node_result(result, persistence_sink=self.persistence_sink, node_name="retrieve_resume_context")
        return result.state

    def retrieve_rubric_context_node(self, state):
        result = retrieve_rubric_context(
            state,
            retrieval_service=self.retrieval_service,
            rubric_service=self.rubric_service,
        )
        _emit_node_result(result, persistence_sink=self.persistence_sink, node_name="retrieve_rubric_context")
        return result.state

    def run_interviewer_node(self, state):
        result = run_interviewer(
            state,
            interviewer_agent=self.interviewer_agent,
        )
        _emit_node_result(result, persistence_sink=self.persistence_sink, node_name="run_interviewer")
        return result.state

    def wait_for_input_node(self, state):
        result = wait_for_input(state)
        _emit_node_result(result, persistence_sink=self.persistence_sink, node_name="wait_for_input")
        return result.state

    def run_evaluator_node(self, state):
        result = run_evaluator(
            state,
            evaluator_agent=self.evaluator_agent,
            scoring_service=self.scoring_service,
        )
        _emit_node_result(result, persistence_sink=self.persistence_sink, node_name="run_evaluator")
        return result.state

    def decide_intervention_node(self, state):
        result = decide_intervention(
            state,
            template_service=self.template_service,
        )
        _emit_node_result(result, persistence_sink=self.persistence_sink, node_name="decide_intervention")
        return result.state

    def run_coach_node(self, state):
        result = run_coach(
            state,
            coach_agent=self.coach_agent,
        )
        _emit_node_result(result, persistence_sink=self.persistence_sink, node_name="run_coach")
        return result.state

    def advance_question_node(self, state):
        result = advance_question(
            state,
            session_service=self.session_service,
            question_service=self.question_service,
        )
        _emit_node_result(result, persistence_sink=self.persistence_sink, node_name="advance_question")
        return result.state

    def end_round_node(self, state):
        result = end_round(
            state,
            scoring_service=self.scoring_service,
            session_service=self.session_service,
        )
        _emit_node_result(result, persistence_sink=self.persistence_sink, node_name="end_round")
        return result.state

    def generate_report_node(self, state):
        result = generate_report(
            state,
            report_service=self.report_service,
            scoring_service=self.scoring_service,
        )
        _emit_node_result(result, persistence_sink=self.persistence_sink, node_name="generate_report")
        return result.state

    def process_transcript_node(self, state):
        payload = state.round.pending_input_event_payload or {}
        event_type = state.round.pending_input_event_type
        if event_type == "transcript.partial":
            event = TranscriptPartialEvent(
                session_id=state.session.session_id,
                session_round_id=state.round.round_id,
                session_question_id=state.round.session_question_id,
                channel="transcript",
                event_type="transcript.partial",
                source="frontend",
                persist_level="ephemeral",
                payload=TranscriptPartialPayload(
                    speaker=payload.get("speaker", "user"),
                    text_delta=payload.get("text_delta", payload.get("text", "")),
                    confidence=payload.get("confidence"),
                    start_ms=payload.get("start_ms"),
                    end_ms=payload.get("end_ms"),
                ),
            )
        else:
            event = TranscriptFinalEvent(
                session_id=state.session.session_id,
                session_round_id=state.round.round_id,
                session_question_id=state.round.session_question_id,
                channel="transcript",
                event_type="transcript.final",
                source="frontend",
                persist_level="durable",
                payload=TranscriptFinalPayload(
                    speaker=payload.get("speaker", "user"),
                    text=payload.get("text", ""),
                    confidence=payload.get("confidence"),
                    start_ms=payload.get("start_ms"),
                    end_ms=payload.get("end_ms"),
                    pause_before_ms=payload.get("pause_before_ms"),
                    pause_after_ms=payload.get("pause_after_ms"),
                ),
            )
        result = process_transcript(
            state,
            event=event,
            transcript_service=self.transcript_service,
        )
        _emit_node_result(result, persistence_sink=self.persistence_sink, node_name="process_transcript")
        return result.state

    def process_code_signal_node(self, state):
        payload = state.round.pending_input_event_payload or {}
        event_type = state.round.pending_input_event_type
        if event_type == "code.run_completed":
            event = CodeRunCompletedEvent(
                session_id=state.session.session_id,
                session_round_id=state.round.round_id,
                session_question_id=state.round.session_question_id,
                channel="code",
                event_type="code.run_completed",
                source="frontend",
                persist_level="durable",
                payload=CodeRunCompletedPayload(
                    stdout=payload.get("stdout"),
                    stderr=payload.get("stderr"),
                    exit_code=payload.get("exit_code", 0),
                    runtime_ms=payload.get("runtime_ms"),
                    tests_passed=payload.get("tests_passed"),
                    tests_failed=payload.get("tests_failed"),
                ),
            )
        else:
            event = CodeChangedEvent(
                session_id=state.session.session_id,
                session_round_id=state.round.round_id,
                session_question_id=state.round.session_question_id,
                channel="code",
                event_type="code.changed",
                source="frontend",
                persist_level="important",
                payload=CodeChangedPayload(
                    language=payload.get("language", "javascript"),
                    file_path=payload.get("file_path", "main"),
                    content_snapshot=payload.get("content_snapshot", payload.get("content", "")),
                    content_hash=payload.get("content_hash", ""),
                    diff_summary=payload.get("diff_summary"),
                ),
            )
        result = process_code_signal(
            state,
            event=event,
            code_event_service=self.code_event_service,
        )
        _emit_node_result(result, persistence_sink=self.persistence_sink, node_name="process_code_signal")
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
            process_transcript_node=self.process_transcript_node,
            process_code_signal_node=self.process_code_signal_node,
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
            process_transcript_node=self.process_transcript_node,
            process_code_signal_node=self.process_code_signal_node,
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

    def invoke_coding_graph(self, state):
        graph = self.build_coding_graph()
        config = build_thread_config(session_id=state.session.session_id, round_id=state.round.round_id)
        output = graph.invoke(state, config=config)
        return self._coerce_runtime_state(output)

    def resume_coding_graph(self, state, *, resume_payload: dict[str, Any]):
        state = self._coerce_runtime_state(state)
        graph = self.build_coding_graph()
        config = build_thread_config(session_id=state.session.session_id, round_id=state.round.round_id)
        output = graph.invoke(Command(resume=resume_payload), config=config)
        return self._coerce_runtime_state(output)

    @staticmethod
    def _coerce_runtime_state(value: Any) -> RuntimeState:
        if isinstance(value, RuntimeState):
            return value
        if isinstance(value, dict):
            if "__interrupt__" in value:
                value = {k: v for k, v in value.items() if k != "__interrupt__"}
            return RuntimeState.model_validate(value)
        raise TypeError(f"Unexpected runtime state type: {type(value)!r}")
