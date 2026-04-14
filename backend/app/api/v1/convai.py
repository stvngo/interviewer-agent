"""ConvAI agent management endpoints."""

from __future__ import annotations

import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.elevenlabs_service import ElevenLabsConvAIService

logger = logging.getLogger(__name__)
router = APIRouter()

_convai = ElevenLabsConvAIService()

_PROMPT_PATH = Path(__file__).resolve().parents[2] / "prompts" / "runtime" / "interviewer_system.md"


def _load_system_prompt() -> str:
    if _PROMPT_PATH.exists():
        return _PROMPT_PATH.read_text(encoding="utf-8")
    return "You are an interviewer for a technical and behavioral interview platform."


class CreateAgentResponse(BaseModel):
    agent_id: str
    name: str


@router.post("/agent", response_model=CreateAgentResponse)
async def create_convai_agent() -> CreateAgentResponse:
    """Create an ElevenLabs Conversational AI agent with the interviewer system prompt."""
    try:
        system_prompt = _load_system_prompt()
        agent_id = await _convai.create_interview_agent(system_prompt=system_prompt)
        return CreateAgentResponse(agent_id=agent_id, name="Interview Agent")
    except Exception as exc:
        logger.exception("Failed to create ConvAI agent")
        raise HTTPException(status_code=502, detail=f"ElevenLabs API error: {exc}") from exc


class AgentInfoResponse(BaseModel):
    agent_id: str | None
    available: bool


@router.get("/agent", response_model=AgentInfoResponse)
async def get_convai_agent_info() -> AgentInfoResponse:
    """Return the cached agent ID if one exists."""
    return AgentInfoResponse(
        agent_id=_convai._cached_agent_id,
        available=_convai._cached_agent_id is not None,
    )
