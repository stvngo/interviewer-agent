from __future__ import annotations


class MockInterviewerAgent:
    def invoke(self, payload: dict) -> dict:
        round_state = payload["round"]

        if round_state["round_status"] == "asking_question":
            return {
                "should_speak": True,
                "spoken_response": "Tell me about a time you had to learn something quickly.",
                "response_goal": "ask_question",
                "state_transition": "listening",
                "interruptible": False,
                "wait_before_speaking_ms": 250,
                "detected_user_state": "needs_clarification",
            }

        decision = round_state.get("latest_intervention_decision")
        if decision and decision.get("action") == "probe":
            return {
                "should_speak": True,
                "spoken_response": "What made that situation challenging for you specifically?",
                "response_goal": "probe",
                "state_transition": "probing",
                "interruptible": False,
                "wait_before_speaking_ms": 250,
                "detected_user_state": "thinking",
            }

        return {
            "should_speak": True,
            "spoken_response": "Thanks. Keep going.",
            "response_goal": "acknowledge",
            "state_transition": "listening",
            "interruptible": False,
            "wait_before_speaking_ms": 250,
            "detected_user_state": "answering",
        }


class MockEvaluatorAgent:
    def invoke(self, payload: dict) -> dict:
        text = payload["round"]["transcript_window"]["rolling_text"].lower()

        if "result" in text or "outcome" in text:
            action = "advance"
            status = "completed"
            score = 0.82
        elif len(text) < 40:
            action = "probe"
            status = "at_risk"
            score = 0.45
        else:
            action = "wait"
            status = "on_track"
            score = 0.68

        return {
            "round_status": status,
            "intervention_recommendation": {
                "action": action,
                "reason": "Mock evaluator recommendation.",
                "urgency": "medium",
            },
            "dimension_scores": [
                {
                    "dimension_key": "structure",
                    "score_raw": 3,
                    "score_normalized": score,
                    "weight": 0.3,
                    "confidence": 0.8,
                    "evidence_refs": [],
                    "reason": "Mock structure assessment.",
                }
            ],
            "overall_estimate": {
                "score_normalized": score,
                "confidence": 0.8,
            },
            "technical_correctness": None,
            "answer_completeness": score,
            "communication_effectiveness": 0.75,
            "off_track_score": 1.0 - score,
            "strengths": ["clear framing"] if score > 0.6 else [],
            "weaknesses": ["needs more detail"] if score < 0.7 else [],
            "missing_requirements": ["missing outcome"] if "result" not in text and "outcome" not in text else [],
            "uncertainty_notes": [],
            "report_notes": ["Mock evaluator notes."],
        }


class MockCoachAgent:
    def invoke(self, payload: dict) -> dict:
        return {
            "coaching_mode": "live_hint",
            "helpfulness_level": "light",
            "reveal_level": 1,
            "coach_response": "Try making the example more concrete and include the outcome.",
            "misconception_tags": [],
            "recommended_next_step": "Add the result of your actions.",
            "suggested_drill": {
                "title": "STAR drill",
                "description": "Practice adding measurable outcomes to behavioral examples.",
            },
            "internal_notes": [],
        }