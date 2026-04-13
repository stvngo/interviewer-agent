from __future__ import annotations

from uuid import uuid4

from app.langgraph.runtime.executor import GraphExecutor
from app.langgraph.state import (
    EvaluationState,
    InterviewerExecutionState,
    RoundGraphState,
    RuntimeState,
    SessionGraphState,
)
from app.realtime.event_contracts import TranscriptFinalEvent, TranscriptFinalPayload
from app.tests.mocks.mock_agents import (
    MockCoachAgent,
    MockEvaluatorAgent,
    MockInterviewerAgent,
)
from app.tests.mocks.mock_services import (
    MockCodeEventService,
    MockQuestionService,
    MockReportService,
    MockResumeService,
    MockRetrievalService,
    MockRubricService,
    MockScoringService,
    MockSessionService,
    MockTemplateService,
    MockTranscriptService,
)


def main() -> None:
    session_id = uuid4()
    round_id = uuid4()

    initial_state = RuntimeState(
        session=SessionGraphState(
            session_id=session_id,
            user_id=uuid4(),
            template_id=uuid4(),
            resume_id=uuid4(),
            session_status="created",
            current_graph="session",
            current_round_id=round_id,
            current_round_order=0,
            total_round_count=1,
            target_role="Software Engineer Intern",
            interview_track="behavioral",
        ),
        round=RoundGraphState(
            session_id=session_id,
            round_id=round_id,
            round_type="behavioral",
            round_status="not_started",
        ),
        interviewer=InterviewerExecutionState(),
        evaluation=EvaluationState(),
    )

    executor = GraphExecutor(
        session_service=MockSessionService(),
        template_service=MockTemplateService(),
        resume_service=MockResumeService(),
        question_service=MockQuestionService(),
        rubric_service=MockRubricService(),
        transcript_service=MockTranscriptService(),
        code_event_service=MockCodeEventService(),
        scoring_service=MockScoringService(),
        report_service=MockReportService(),
        retrieval_service=MockRetrievalService(),
        interviewer_agent=MockInterviewerAgent(),
        evaluator_agent=MockEvaluatorAgent(),
        coach_agent=MockCoachAgent(),
    )

    state = executor.load_session_context_node(initial_state)
    state = executor.select_question_node(state)
    state = executor.retrieve_question_context_node(state)
    state = executor.retrieve_resume_context_node(state)
    state = executor.retrieve_rubric_context_node(state)
    state = executor.run_interviewer_node(state)

    print("\n=== INTERVIEWER ASK ===")
    print(state.interviewer.pending_spoken_response)
    print("round_status:", state.round.round_status)

    transcript_event = TranscriptFinalEvent(
        session_id=state.session.session_id,
        session_round_id=state.round.round_id,
        session_question_id=None,
        channel="transcript",
        event_type="transcript.final",
        source="stt_provider",
        persist_level="durable",
        payload=TranscriptFinalPayload(
            speaker="user",
            text="During a hackathon I had to learn a new API quickly, and I ended up getting the feature working with my team by the end of the night. The result was that we finished our demo on time.",
            is_final=True,
            confidence=0.96,
            start_ms=0,
            end_ms=9000,
            pause_before_ms=500,
            pause_after_ms=300,
        ),
    )

    from app.langgraph.nodes.process_transcript import process_transcript

    result = process_transcript(
        state,
        event=transcript_event,
        transcript_service=MockTranscriptService(),
    )
    state = result.state

    state = executor.run_evaluator_node(state)
    state = executor.decide_intervention_node(state)

    print("\n=== EVALUATOR / POLICY ===")
    print("latest_evaluator_status:", state.round.latest_evaluator_status)
    print("decision:", state.round.latest_intervention_decision)

    if state.round.should_advance_question:
        state = executor.advance_question_node(state)
        print("\n=== ADVANCED QUESTION ===")
        print("new question_index:", state.round.question_index)

    state.round.should_end_round = True
    state = executor.end_round_node(state)
    state = executor.generate_report_node(state)

    print("\n=== FINAL ===")
    print("round_status:", state.round.round_status)
    print("report_status:", state.session.current_report_status)


if __name__ == "__main__":
    main()
