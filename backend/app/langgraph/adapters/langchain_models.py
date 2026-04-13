from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI


_PROMPTS_DIR = Path(__file__).resolve().parents[2] / "prompts" / "runtime"


def _read_prompt(name: str) -> str:
    return (_PROMPTS_DIR / name).read_text(encoding="utf-8")


def _require_openai_api_key() -> None:
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is required for real interviewer runtime.")


def build_chat_model(*, temperature: float = 0.2) -> ChatOpenAI:
    _require_openai_api_key()
    model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    return ChatOpenAI(model=model_name, temperature=temperature)


def _json_response(llm: ChatOpenAI, system_prompt: str, payload: dict[str, Any], schema: dict[str, Any]) -> dict[str, Any]:
    response = llm.invoke(
        [
            SystemMessage(content=system_prompt),
            HumanMessage(
                content=(
                    "Return ONLY valid JSON.\n"
                    f"Schema:\n{json.dumps(schema)}\n\n"
                    f"Input payload:\n{json.dumps(payload, default=str)}"
                )
            ),
        ]
    )
    text = response.content if isinstance(response.content, str) else json.dumps(response.content)
    return json.loads(text)


class OpenAIInterviewerAgent:
    def __init__(self) -> None:
        self._llm = build_chat_model(temperature=0.3)
        self._system_prompt = _read_prompt("interviewer_system.md")

    def invoke(self, payload: dict[str, Any]) -> dict[str, Any]:
        schema = {
            "should_speak": "boolean",
            "spoken_response": "string|null",
            "response_goal": "ask_question|acknowledge|clarify|probe|challenge|redirect|hint|summarize|wrap_up|transition",
            "interruptible": "boolean",
            "wait_before_speaking_ms": "integer",
            "detected_user_state": "answering|thinking|stuck|off_track|finished|needs_clarification|debugging",
            "state_transition": "not_started|asking_question|listening|user_thinking|probing|hinting|evaluating|wrapping_up|ended|null",
        }
        return _json_response(self._llm, self._system_prompt, payload, schema)


class OpenAIEvaluatorAgent:
    def __init__(self) -> None:
        self._llm = build_chat_model(temperature=0.1)
        self._system_prompt = _read_prompt("evaluator_system.md")

    def invoke(self, payload: dict[str, Any]) -> dict[str, Any]:
        schema = {
            "round_status": "on_track|at_risk|stalled|completed|uncertain",
            "overall_estimate": {"score_normalized": "number|null", "confidence": "number|null"},
            "off_track_score": "number|null",
            "technical_correctness": "number|null",
            "answer_completeness": "number|null",
            "communication_effectiveness": "number|null",
            "dimension_scores": "array",
            "missing_requirements": "array",
            "strengths": "array",
            "weaknesses": "array",
            "uncertainty_notes": "array",
            "intervention_recommendation": {
                "action": "none|wait|probe|clarify|offer_hint|redirect|advance|wrap_up",
                "reason": "string",
                "urgency": "low|medium|high",
            },
        }
        return _json_response(self._llm, self._system_prompt, payload, schema)


class OpenAICoachAgent:
    def __init__(self) -> None:
        self._llm = build_chat_model(temperature=0.2)
        self._system_prompt = _read_prompt("coach_system.md")

    def invoke(self, payload: dict[str, Any]) -> dict[str, Any]:
        schema = {
            "helpfulness_level": "light|moderate|strong",
            "reveal_level": "integer",
            "coach_response": "string",
        }
        return _json_response(self._llm, self._system_prompt, payload, schema)
21