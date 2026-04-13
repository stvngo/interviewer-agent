from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException

from app.api.v1.schemas import CreateSessionRequest, SessionListResponse, SessionOut

router = APIRouter()

_sessions: dict[UUID, SessionOut] = {}


@router.post("/", response_model=SessionOut, status_code=201)
async def create_session(body: CreateSessionRequest) -> SessionOut:
    now = datetime.now(timezone.utc)
    session = SessionOut(
        session_id=uuid4(),
        round_type=body.round_type,
        difficulty=body.difficulty,
        title=body.title,
        status="created",
        created_at=now,
        updated_at=now,
    )
    _sessions[session.session_id] = session
    return session


@router.get("/", response_model=SessionListResponse)
async def list_sessions() -> SessionListResponse:
    sessions = sorted(_sessions.values(), key=lambda s: s.created_at, reverse=True)
    return SessionListResponse(sessions=sessions, total=len(sessions))


@router.get("/{session_id}", response_model=SessionOut)
async def get_session(session_id: UUID) -> SessionOut:
    session = _sessions.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.post("/{session_id}/start", response_model=SessionOut)
async def start_session(session_id: UUID) -> SessionOut:
    session = _sessions.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.status not in ("created", "paused"):
        raise HTTPException(status_code=400, detail=f"Cannot start session in '{session.status}' state")

    updated = session.model_copy(update={
        "status": "active",
        "updated_at": datetime.now(timezone.utc),
    })
    _sessions[session_id] = updated
    return updated


@router.post("/{session_id}/end", response_model=SessionOut)
async def end_session(session_id: UUID) -> SessionOut:
    session = _sessions.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    now = datetime.now(timezone.utc)
    duration = None
    if session.created_at:
        duration = int((now - session.created_at).total_seconds() / 60)

    updated = session.model_copy(update={
        "status": "completed",
        "updated_at": now,
        "duration_minutes": duration,
    })
    _sessions[session_id] = updated
    return updated
