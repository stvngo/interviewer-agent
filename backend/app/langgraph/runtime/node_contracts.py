from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import Field

from app.langgraph.state import RuntimeState, StateModel
from app.realtime.event_contracts import AnyRealtimeEvent


NodeName = Literal[
    "load_session_context",
    "select_question",
    "retrieve_question_context",
    "retrieve_resume_context",
    "retrieve_rubric_context",
    "run_interviewer",
    "process_transcript",
    "process_code_signal",
    "run_evaluator",
    "decide_intervention",
    "run_coach",
    "advance_question",
    "end_round",
    "generate_report",
]


MutationPath = Literal[
    "session",
    "round",
    "interviewer",
    "evaluation",
    "session.session_status",
    "session.current_round_id",
    "session.current_round_order",
    "session.current_report_status",
    "round.question_id",
    "round.session_question_id",
    "round.round_status",
    "round.question_status",
    "round.transcript_window",
    "round.code_window",
    "round.retrieval_bundle",
    "round.latest_evaluator_status",
    "round.latest_intervention_decision",
    "round.latest_interviewer_goal",
    "round.hint_level_used",
    "round.hint_budget_remaining",
    "round.should_advance_question",
    "round.should_end_round",
    "interviewer",
    "evaluation",
]


class NodeExecutionContext(StateModel):
    """
    Metadata about why a node is running.
    """

    trace_id: str | None = None
    trigger_event_type: str | None = None
    trigger_source: str | None = None
    actor: Literal["system", "user", "agent", "provider"] = "system"


class PersistenceIntent(StateModel):
    """
    A declarative record of what durable write should happen
    because of this node execution.
    The node may either perform the write directly via a service
    or return this intent to a higher-level runtime.
    """

    target: str
    operation: Literal["create", "update", "upsert", "append"]
    description: str
    ref_id: UUID | None = None


class NodeResult(StateModel):
    """
    Standard node output contract.
    Every node returns updated runtime state plus emitted events
    and any persistence intents/warnings.
    """

    state: RuntimeState
    emitted_events: list[AnyRealtimeEvent] = Field(default_factory=list)
    persistence_intents: list[PersistenceIntent] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class NodeContract(StateModel):
    """
    Static contract for what a node is allowed to do.
    Useful for docs, tests, and keeping boundaries clean.
    """

    name: NodeName
    purpose: str

    required_state_sections: list[Literal["session", "round", "interviewer", "evaluation"]]
    consumes_event_types: list[str] = Field(default_factory=list)
    emits_event_types: list[str] = Field(default_factory=list)

    may_call_services: list[str] = Field(default_factory=list)
    may_mutate_paths: list[MutationPath] = Field(default_factory=list)
    may_persist_targets: list[str] = Field(default_factory=list)


NODE_CONTRACTS: dict[NodeName, NodeContract] = {
    "load_session_context": NodeContract(
        name="load_session_context",
        purpose="Load durable session, round, template, and resume context into runtime state.",
        required_state_sections=["session"],
        consumes_event_types=[],
        emits_event_types=["session.state_changed"],
        may_call_services=["session_service", "template_service", "resume_service"],
        may_mutate_paths=[
            "session",
            "session.session_status",
            "session.current_round_id",
            "session.current_round_order",
        ],
        may_persist_targets=[],
    ),
    "select_question": NodeContract(
        name="select_question",
        purpose="Choose and assign the next question for the active round.",
        required_state_sections=["session", "round"],
        consumes_event_types=[],
        emits_event_types=["question.assigned"],
        may_call_services=["question_service", "session_service"],
        may_mutate_paths=[
            "round.question_id",
            "round.session_question_id",
            "round.question_status",
            "round.round_status",
        ],
        may_persist_targets=["session_questions", "session_events"],
    ),
    "retrieve_question_context": NodeContract(
        name="retrieve_question_context",
        purpose="Load question prompt, hints, and followup context needed for the round.",
        required_state_sections=["round"],
        consumes_event_types=[],
        emits_event_types=[],
        may_call_services=["retrieval_service", "question_service"],
        may_mutate_paths=["round.retrieval_bundle"],
        may_persist_targets=[],
    ),
    "retrieve_resume_context": NodeContract(
        name="retrieve_resume_context",
        purpose="Load only the relevant resume context for the active question and role.",
        required_state_sections=["session", "round"],
        consumes_event_types=[],
        emits_event_types=[],
        may_call_services=["retrieval_service", "resume_service"],
        may_mutate_paths=["round.retrieval_bundle"],
        may_persist_targets=[],
    ),
    "retrieve_rubric_context": NodeContract(
        name="retrieve_rubric_context",
        purpose="Load rubric context appropriate to interviewer or evaluator needs.",
        required_state_sections=["round"],
        consumes_event_types=[],
        emits_event_types=[],
        may_call_services=["retrieval_service", "rubric_service"],
        may_mutate_paths=["round.retrieval_bundle"],
        may_persist_targets=[],
    ),
    "run_interviewer": NodeContract(
        name="run_interviewer",
        purpose="Generate the next interviewer move and optional utterance.",
        required_state_sections=["session", "round", "interviewer", "evaluation"],
        consumes_event_types=[],
        emits_event_types=["interviewer.turn_decision", "interviewer.utterance.created"],
        may_call_services=[],
        may_mutate_paths=[
            "interviewer",
            "round.latest_interviewer_goal",
            "round.round_status",
        ],
        may_persist_targets=["session_events"],
    ),
    "process_transcript": NodeContract(
        name="process_transcript",
        purpose="Update transcript-derived runtime state and persist final transcript segments.",
        required_state_sections=["round"],
        consumes_event_types=["transcript.partial", "transcript.final"],
        emits_event_types=["transcript.final"],
        may_call_services=["transcript_service"],
        may_mutate_paths=["round.transcript_window"],
        may_persist_targets=["transcript_segments", "session_events"],
    ),
    "process_code_signal": NodeContract(
        name="process_code_signal",
        purpose="Update code-derived runtime state and persist meaningful code events.",
        required_state_sections=["round"],
        consumes_event_types=["code.changed", "code.run_completed"],
        emits_event_types=[],
        may_call_services=["code_event_service"],
        may_mutate_paths=["round.code_window"],
        may_persist_targets=["code_events", "code_snapshots", "session_events"],
    ),
    "run_evaluator": NodeContract(
        name="run_evaluator",
        purpose="Compute live evaluation state and intervention recommendations.",
        required_state_sections=["round", "evaluation"],
        consumes_event_types=["transcript.final", "code.run_completed"],
        emits_event_types=["evaluator.signal.updated"],
        may_call_services=["scoring_service"],
        may_mutate_paths=[
            "evaluation",
            "round.latest_evaluator_status",
        ],
        may_persist_targets=["live_score_snapshots", "session_events"],
    ),
    "decide_intervention": NodeContract(
        name="decide_intervention",
        purpose="Turn evaluator recommendations and policy into a final next action.",
        required_state_sections=["session", "round", "evaluation"],
        consumes_event_types=["evaluator.signal.updated", "coach.hint_ready"],
        emits_event_types=[],
        may_call_services=["template_service"],
        may_mutate_paths=[
            "round.latest_intervention_decision",
            "round.should_advance_question",
            "round.should_end_round",
        ],
        may_persist_targets=["session_events"],
    ),
    "run_coach": NodeContract(
        name="run_coach",
        purpose="Generate coaching or hint content when policy allows.",
        required_state_sections=["session", "round", "evaluation"],
        consumes_event_types=["control.request_hint"],
        emits_event_types=["coach.hint_ready"],
        may_call_services=[],
        may_mutate_paths=[
            "round.hint_level_used",
            "round.hint_budget_remaining",
            "round.round_status",
        ],
        may_persist_targets=["session_questions", "session_events"],
    ),
    "advance_question": NodeContract(
        name="advance_question",
        purpose="Finalize the current question and move to the next one.",
        required_state_sections=["round", "interviewer", "evaluation"],
        consumes_event_types=[],
        emits_event_types=["question.assigned", "round.state_changed"],
        may_call_services=["session_service", "question_service"],
        may_mutate_paths=[
            "round",
            "interviewer",
            "evaluation",
        ],
        may_persist_targets=["session_questions", "session_events"],
    ),
    "end_round": NodeContract(
        name="end_round",
        purpose="Finalize round-level state and persist final scores.",
        required_state_sections=["session", "round", "evaluation"],
        consumes_event_types=[],
        emits_event_types=["round.state_changed"],
        may_call_services=["scoring_service", "session_service"],
        may_mutate_paths=["round.round_status", "round.should_end_round"],
        may_persist_targets=["final_scorecards", "session_events", "session_rounds"],
    ),
    "generate_report": NodeContract(
        name="generate_report",
        purpose="Create and persist the final feedback report for the session.",
        required_state_sections=["session", "round", "evaluation"],
        consumes_event_types=[],
        emits_event_types=["report.ready"],
        may_call_services=["report_service", "scoring_service"],
        may_mutate_paths=["session.current_report_status"],
        may_persist_targets=["feedback_reports", "session_events"],
    ),
}