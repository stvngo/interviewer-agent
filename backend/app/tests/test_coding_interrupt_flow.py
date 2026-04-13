from __future__ import annotations

import os
import unittest
from uuid import uuid4

from app.langgraph.adapters.langchain_models import OpenAIInterviewerAgent
from app.langgraph.checkpointing.checkpointer import get_checkpointer
from app.langgraph.runtime.executor import GraphExecutor
from app.langgraph.state import (
    EvaluationState,
    InterviewerExecutionState,
    RoundGraphState,
    RuntimeState,
    SessionGraphState,
)
from app.tests.mocks.mock_agents import MockCoachAgent, MockEvaluatorAgent, MockInterviewerAgent
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


def _base_state() -> RuntimeState:
    session_id = uuid4()
    round_id = uuid4()
    return RuntimeState(
        session=SessionGraphState(
            session_id=session_id,
            user_id=uuid4(),
            template_id=uuid4(),
            resume_id=uuid4(),
            session_status="active",
            current_graph="round",
            current_round_id=round_id,
            current_round_order=0,
            total_round_count=1,
            interview_track="coding",
        ),
        round=RoundGraphState(
            session_id=session_id,
            round_id=round_id,
            round_type="coding",
            round_status="not_started",
        ),
        interviewer=InterviewerExecutionState(),
        evaluation=EvaluationState(),
    )


def _mock_executor() -> GraphExecutor:
    return GraphExecutor(
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
        checkpointer=get_checkpointer(),
    )


class CodingInterruptFlowTests(unittest.TestCase):
    def test_resume_transcript_final_updates_state(self) -> None:
        executor = _mock_executor()
        state = executor.load_session_context_node(_base_state())
        running = executor.invoke_coding_graph(state)
        self.assertIsNotNone(running.round.question_id)

        resumed = executor.resume_coding_graph(
            running,
            resume_payload={"type": "transcript.final", "speaker": "user", "text": "I would use a hash map"},
        )
        self.assertGreaterEqual(len(resumed.round.transcript_window.rolling_text), 1)
        self.assertGreaterEqual(resumed.round.transcript_checkpoint_counter, 1)

    def test_resume_code_changed_updates_code_window(self) -> None:
        executor = _mock_executor()
        state = executor.load_session_context_node(_base_state())
        running = executor.invoke_coding_graph(state)
        resumed = executor.resume_coding_graph(
            running,
            resume_payload={
                "type": "code.changed",
                "language": "javascript",
                "file_path": "main",
                "content_snapshot": "function twoSum(){}",
                "content_hash": "abc",
            },
        )
        self.assertEqual(resumed.round.code_window.latest_language, "javascript")
        self.assertGreaterEqual(resumed.round.code_checkpoint_counter, 1)


@unittest.skipUnless(os.getenv("OPENAI_API_KEY"), "OPENAI_API_KEY not set")
class OpenAISmokeTests(unittest.TestCase):
    def test_openai_interviewer_agent_invoke(self) -> None:
        agent = OpenAIInterviewerAgent()
        payload = {
            "session": _base_state().session.model_dump(mode="json"),
            "round": _base_state().round.model_dump(mode="json"),
            "interviewer": _base_state().interviewer.model_dump(mode="json"),
            "evaluation": _base_state().evaluation.model_dump(mode="json"),
        }
        result = agent.invoke(payload)
        self.assertIn("should_speak", result)


if __name__ == "__main__":
    unittest.main()
