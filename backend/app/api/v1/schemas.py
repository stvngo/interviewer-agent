from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


# --- Health ---

class HealthResponse(BaseModel):
    status: str = "ok"


# --- Questions ---

class QuestionExample(BaseModel):
    input: str
    output: str
    explanation: str | None = None


class QuestionOut(BaseModel):
    id: int
    title: str
    description: str
    difficulty: str
    acceptance_rate: float | None = None
    related_topics: list[str] = Field(default_factory=list)
    url: str | None = None
    examples: list[QuestionExample] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)


class QuestionListResponse(BaseModel):
    questions: list[QuestionOut]
    total: int
    skip: int
    limit: int


# --- Sessions ---

class CreateSessionRequest(BaseModel):
    round_type: str = "coding"
    difficulty: str | None = None
    title: str | None = None


class SessionOut(BaseModel):
    session_id: UUID
    round_type: str
    difficulty: str | None = None
    title: str | None = None
    status: str
    question_id: int | None = None
    created_at: datetime
    updated_at: datetime
    duration_minutes: int | None = None


class SessionListResponse(BaseModel):
    sessions: list[SessionOut]
    total: int


# --- Code Events ---

class CodeEventRequest(BaseModel):
    session_id: UUID
    language: str = "javascript"
    content: str
    file_path: str = "main"


class CodeEventOut(BaseModel):
    event_id: UUID
    session_id: UUID
    language: str
    content: str
    file_path: str
    created_at: datetime


class CodeEventListResponse(BaseModel):
    events: list[CodeEventOut]
    total: int


# --- WebSocket messages ---

class WsUserMessage(BaseModel):
    type: str = "transcript.user"
    content: str


class WsInterviewerMessage(BaseModel):
    type: str = "transcript.interviewer"
    content: str
    timestamp: str
