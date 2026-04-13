from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID
from uuid import uuid4

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.api.v1.sessions import _sessions
from app.langgraph.adapters.langchain_models import (
    OpenAICoachAgent,
    OpenAIEvaluatorAgent,
    OpenAIInterviewerAgent,
)
from app.langgraph.checkpointing.checkpointer import get_checkpointer
from app.langgraph.runtime.executor import GraphExecutor
from app.langgraph.state import (
    EvaluationState,
    InterviewerExecutionState,
    RoundGraphState,
    RuntimeState,
    SessionGraphState,
)
from app.realtime.ws_manager import manager
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

router = APIRouter()

_session_runtime: dict[UUID, RuntimeState] = {}
_last_sent_response: dict[UUID, str] = {}
_executor: GraphExecutor | None = None


def _get_executor() -> GraphExecutor:
    global _executor
    if _executor is None:
        _executor = GraphExecutor(
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
            interviewer_agent=OpenAIInterviewerAgent(),
            evaluator_agent=OpenAIEvaluatorAgent(),
            coach_agent=OpenAICoachAgent(),
            checkpointer=get_checkpointer(),
        )
    return _executor


def _build_initial_state(session_id: UUID) -> RuntimeState:
    stored = _sessions.get(session_id)
    round_id = uuid4()
    if stored is None:
        return RuntimeState(
            session=SessionGraphState(
                session_id=session_id,
                user_id=uuid4(),
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

    return RuntimeState(
        session=SessionGraphState(
            session_id=stored.session_id,
            user_id=stored.user_id,
            template_id=stored.template_id,
            resume_id=stored.resume_id,
            session_status="active" if stored.status in {"active", "created"} else "paused",
            current_graph="round",
            current_round_id=round_id,
            current_round_order=0,
            total_round_count=1,
            target_role=stored.target_role,
            interview_track=stored.round_type,
            strictness_mode=stored.strictness_mode,
            difficulty_mode=stored.difficulty_mode,
            voice_enabled=stored.voice_enabled,
            video_enabled=stored.video_enabled,
            integrity_enabled=stored.integrity_enabled,
        ),
        round=RoundGraphState(
            session_id=stored.session_id,
            round_id=round_id,
            round_type="coding",
            round_status="not_started",
        ),
        interviewer=InterviewerExecutionState(),
        evaluation=EvaluationState(),
    )


async def _send_interviewer_message(session_id: UUID, state: RuntimeState) -> None:
    if not state.interviewer.should_speak or not state.interviewer.pending_spoken_response:
        return
    current = state.interviewer.pending_spoken_response
    if _last_sent_response.get(session_id) == current:
        return
    _last_sent_response[session_id] = current
    await manager.broadcast(
        session_id,
        {
            "type": "transcript.interviewer",
            "content": current,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "response_goal": state.interviewer.response_goal,
            "interruptible": state.interviewer.interruptible,
        },
    )


def _resume_payload_from_ws(data: dict) -> dict:
    msg_type = data.get("type", "")
    if msg_type == "transcript.user":
        return {"type": "transcript.final", "speaker": "user", "text": data.get("content", "")}
    if msg_type == "transcript.partial":
        return {
            "type": "transcript.partial",
            "speaker": data.get("speaker", "user"),
            "text_delta": data.get("text_delta", data.get("content", "")),
            "confidence": data.get("confidence"),
            "start_ms": data.get("start_ms"),
            "end_ms": data.get("end_ms"),
        }
    if msg_type == "transcript.final":
        return {
            "type": "transcript.final",
            "speaker": data.get("speaker", "user"),
            "text": data.get("text", data.get("content", "")),
            "confidence": data.get("confidence"),
            "start_ms": data.get("start_ms"),
            "end_ms": data.get("end_ms"),
            "pause_before_ms": data.get("pause_before_ms"),
            "pause_after_ms": data.get("pause_after_ms"),
        }
    if msg_type == "code.changed":
        return {
            "type": "code.changed",
            "language": data.get("language", "javascript"),
            "file_path": data.get("file_path", "main"),
            "content_snapshot": data.get("content_snapshot", data.get("content", "")),
            "content_hash": data.get("content_hash", ""),
            "diff_summary": data.get("diff_summary"),
        }
    if msg_type == "code.run_completed":
        return {
            "type": "code.run_completed",
            "stdout": data.get("stdout"),
            "stderr": data.get("stderr"),
            "exit_code": data.get("exit_code", 0),
            "runtime_ms": data.get("runtime_ms"),
            "tests_passed": data.get("tests_passed"),
            "tests_failed": data.get("tests_failed"),
        }
    return {"type": "transcript.final", "speaker": "user", "text": data.get("content", "")}


@router.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: UUID) -> None:
    executor = _get_executor()
    await manager.connect(session_id, websocket)
    try:
        if session_id not in _session_runtime:
            initial_state = _build_initial_state(session_id)
            loaded = executor.load_session_context_node(initial_state)
            running_state = executor.invoke_coding_graph(loaded)
            _session_runtime[session_id] = running_state
            await _send_interviewer_message(session_id, running_state)

        while True:
            data = await websocket.receive_json()
            if data.get("type") == "ping":
                await manager.send_personal(
                    websocket,
                    {"type": "pong", "timestamp": datetime.now(timezone.utc).isoformat()},
                )
                continue

            current = _session_runtime.get(session_id)
            if current is None:
                current = _build_initial_state(session_id)

            resume_payload = _resume_payload_from_ws(data)
            next_state = executor.resume_coding_graph(current, resume_payload=resume_payload)
            _session_runtime[session_id] = next_state
            await _send_interviewer_message(session_id, next_state)

    except WebSocketDisconnect:
        manager.disconnect(session_id, websocket)
    except Exception as exc:
        await manager.send_personal(
            websocket,
            {
                "type": "control.error",
                "message": str(exc),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )
        manager.disconnect(session_id, websocket)
