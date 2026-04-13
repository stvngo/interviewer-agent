from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from uuid import UUID, uuid4

from fastapi import APIRouter

from app.api.v1.schemas import CodeEventListResponse, CodeEventOut, CodeEventRequest

router = APIRouter()

_events_by_session: dict[UUID, list[CodeEventOut]] = defaultdict(list)


@router.post("/", response_model=CodeEventOut, status_code=201)
async def create_code_event(body: CodeEventRequest) -> CodeEventOut:
    event = CodeEventOut(
        event_id=uuid4(),
        session_id=body.session_id,
        language=body.language,
        content=body.content,
        file_path=body.file_path,
        created_at=datetime.now(timezone.utc),
    )
    _events_by_session[body.session_id].append(event)
    return event


@router.get("/{session_id}", response_model=CodeEventListResponse)
async def list_code_events(session_id: UUID) -> CodeEventListResponse:
    events = _events_by_session.get(session_id, [])
    return CodeEventListResponse(events=events, total=len(events))
