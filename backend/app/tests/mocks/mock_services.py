from __future__ import annotations

from uuid import uuid4


class MockSessionService:
    def get_session_runtime_context(self, session_id) -> dict:
        return {
            "target_role": "Software Engineer Intern",
            "interview_track": "behavioral",
            "total_round_count": 1,
            "current_round_id": uuid4(),
            "current_round_order": 0,
        }

    def assign_question_to_round(self, session_id, round_id, question_id, question_order: int) -> dict:
        return {
            "question_id": question_id,
            "session_question_id": uuid4(),
        }

    def finalize_session_question(self, session_id, round_id, session_question_id=None, final_status: str = "") -> None:
        return None

    def finalize_round(self, session_id, round_id, final_status: str = "") -> None:
        return None


class MockTemplateService:
    def get_template_runtime_config(self, template_id) -> dict:
        return {
            "strictness_mode": "neutral",
            "difficulty_mode": "manual",
            "voice_enabled": True,
            "video_enabled": False,
            "integrity_enabled": False,
        }

    def resolve_intervention_policy(self, **kwargs) -> dict:
        recommendation = kwargs.get("evaluator_recommendation", {})
        action = recommendation.get("action", "none")

        if kwargs.get("user_requested_hint"):
            return {"action": "offer_hint", "reason": "User requested hint.", "urgency": "medium"}

        if action == "offer_hint" and kwargs.get("hint_budget_remaining", 0) > 0:
            return {"action": "offer_hint", "reason": "Evaluator recommends hint.", "urgency": "medium"}

        if action == "advance":
            return {"action": "advance", "reason": "Answer sufficiently complete.", "urgency": "medium"}

        if action == "wrap_up":
            return {"action": "wrap_up", "reason": "Round should conclude.", "urgency": "high"}

        if action in {"probe", "clarify", "redirect"}:
            return {"action": action, "reason": recommendation.get("reason", ""), "urgency": recommendation.get("urgency", "low")}

        return {"action": "wait", "reason": "Continue listening.", "urgency": "low"}


class MockResumeService:
    def get_resume_runtime_context(self, resume_id) -> dict:
        return {
            "skills": ["Python", "FastAPI", "PostgreSQL"],
            "projects": ["AI Interviewer", "RAG News App"],
            "experience_summary": "Student builder with backend and ML experience.",
        }


class MockQuestionService:
    def select_next_question(self, **kwargs) -> dict:
        return {
            "question_id": uuid4(),
            "prompt_preview": "Tell me about a time you had to learn something quickly.",
        }

    def get_question_runtime_packet(self, question_id) -> dict:
        return {
            "question_id": question_id,
            "prompt": "Tell me about a time you had to learn something quickly.",
            "hint_ladder": [
                "Use a concrete example.",
                "Focus on the challenge, action, and outcome.",
            ],
            "followups": [
                "What would you do differently now?",
                "How did you measure success?",
            ],
        }


class MockRubricService:
    def get_rubric_runtime_packet(self, round_type) -> dict:
        return {
            "round_type": round_type,
            "dimensions": [
                {"dimension_key": "structure", "weight": 0.3},
                {"dimension_key": "specificity", "weight": 0.3},
                {"dimension_key": "reflection", "weight": 0.2},
                {"dimension_key": "communication", "weight": 0.2},
            ],
        }


class MockTranscriptService:
    def persist_final_segment(self, **kwargs) -> dict:
        return {"segment_id": uuid4()}

    def update_transcript_window(self, transcript_window: dict, **kwargs) -> dict:
        rolling_text = transcript_window.get("rolling_text", "")
        text_delta = kwargs.get("text_delta", "")
        return {
            "recent_segment_ids": transcript_window.get("recent_segment_ids", []),
            "rolling_text": (rolling_text + " " + text_delta).strip(),
            "user_current_state": "thinking" if kwargs.get("speaker") == "user" else "unknown",
            "silence_ms": 0,
            "last_user_final_at": None,
        }


class MockCodeEventService:
    def persist_code_change(self, **kwargs) -> dict:
        return {"code_event_id": uuid4()}

    def persist_code_run(self, **kwargs) -> dict:
        return {"code_event_id": uuid4()}

    def summarize_code_window(self, code_window: dict, **kwargs) -> dict:
        return {
            "recent_code_event_ids": code_window.get("recent_code_event_ids", []),
            "latest_language": kwargs.get("language", code_window.get("latest_language")),
            "latest_snapshot_hash": kwargs.get("content_hash", code_window.get("latest_snapshot_hash")),
            "last_run_status": "success" if kwargs.get("exit_code", 1) == 0 else "runtime_error",
            "code_progress_state": "implementing",
            "latest_stdout_excerpt": kwargs.get("stdout"),
            "latest_stderr_excerpt": kwargs.get("stderr"),
            "tests_passed": kwargs.get("tests_passed"),
            "tests_failed": kwargs.get("tests_failed"),
        }


class MockScoringService:
    def persist_live_snapshot(self, **kwargs) -> dict:
        return {"snapshot_id": uuid4()}

    def finalize_round_scorecard(self, **kwargs) -> dict:
        return {"scorecard_id": uuid4()}

    def finalize_session_summary(self, session_id) -> dict:
        return {
            "overall_score": 0.78,
            "top_strengths": ["clear communication", "good structure"],
            "top_weaknesses": ["could give more specific detail"],
        }


class MockReportService:
    def generate_session_report(self, session_id, session_summary: dict) -> dict:
        return {"report_id": uuid4()}


class MockRetrievalService:
    def package_question_context(self, question_packet: dict, target: str) -> dict:
        payload = {
            "context_ref": f"question_ctx::{question_packet['question_id']}::{target}",
            "followup_context_ref": f"question_followups::{question_packet['question_id']}",
        }
        if target == "evaluator":
            payload["hidden_answer_ref"] = f"hidden_answer::{question_packet['question_id']}"
        return payload

    def package_resume_context(self, resume_context: dict, **kwargs) -> dict:
        return {
            "context_ref": (
                f"resume_ctx::{kwargs.get('round_type', 'unknown')}::{kwargs.get('target', 'interviewer')}"
            )
        }

    def package_rubric_context(self, rubric_packet: dict, target: str) -> dict:
        return {"context_ref": f"rubric_ctx::{rubric_packet['round_type']}::{target}"}