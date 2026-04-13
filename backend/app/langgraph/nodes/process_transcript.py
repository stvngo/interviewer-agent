"""
Purpose: Update transcript-derived runtime state.

Reads
- transcript event payloads

Calls
- transcript_service

Writes
- transcript_window
- silence metrics
- user state estimate

Emits
- transcript.final or internal checkpoint events

DB writes
- transcript_segments for final segments only
"""

from __future__ import annotations

from typing import Any, cast

from app.langgraph.runtime.node_contracts import NodeExecutionContext, NodeResult, PersistenceIntent
from app.langgraph.state import RuntimeState
from app.realtime.event_contracts import (
    TranscriptFinalEvent,
    TranscriptPartialEvent,
)


def process_transcript(
    state: RuntimeState,
    *,
    event: TranscriptPartialEvent | TranscriptFinalEvent,
    transcript_service: Any,
    ctx: NodeExecutionContext | None = None,
) -> NodeResult:
    """
    Update transcript-derived runtime state.

    Expected service methods:
    - transcript_service.persist_final_segment(...) -> dict
    - transcript_service.update_transcript_window(...) -> dict
    """

    ctx = ctx or NodeExecutionContext(
        trigger_event_type=event.event_type,
        trigger_source=event.source,
        actor="provider",
    )
    new_state = state.model_copy(deep=True)
    emitted_events = []
    persistence_intents = []
    warnings = []

    payload = event.payload

    if isinstance(event, TranscriptPartialEvent):
        updated = transcript_service.update_transcript_window(
            transcript_window=new_state.round.transcript_window.model_dump(),
            speaker=payload.speaker,
            text_delta=payload.text_delta,
            is_final=False,
            confidence=payload.confidence,
            start_ms=payload.start_ms,
            end_ms=payload.end_ms,
        )

        new_state.round.transcript_window.rolling_text = updated.get(
            "rolling_text",
            new_state.round.transcript_window.rolling_text + payload.text_delta,
        )
        new_state.round.transcript_window.user_current_state = updated.get(
            "user_current_state",
            new_state.round.transcript_window.user_current_state,
        )

        return NodeResult(
            state=new_state,
            emitted_events=emitted_events,
            persistence_intents=persistence_intents,
            warnings=warnings,
        )

    final_payload = cast(TranscriptFinalEvent, event).payload

    segment = transcript_service.persist_final_segment(
        session_id=new_state.session.session_id,
        round_id=new_state.round.round_id,
        session_question_id=new_state.round.session_question_id,
        speaker=final_payload.speaker,
        text=final_payload.text,
        confidence=final_payload.confidence,
        start_ms=final_payload.start_ms,
        end_ms=final_payload.end_ms,
        pause_before_ms=final_payload.pause_before_ms,
        pause_after_ms=final_payload.pause_after_ms,
    )

    updated = transcript_service.update_transcript_window(
        transcript_window=new_state.round.transcript_window.model_dump(),
        speaker=final_payload.speaker,
        text_delta=final_payload.text,
        is_final=True,
        confidence=final_payload.confidence,
        start_ms=final_payload.start_ms,
        end_ms=final_payload.end_ms,
        persisted_segment_id=segment["segment_id"],
    )

    new_state.round.transcript_window.recent_segment_ids = updated.get(
        "recent_segment_ids",
        new_state.round.transcript_window.recent_segment_ids + [segment["segment_id"]],
    )
    new_state.round.transcript_window.rolling_text = updated.get("rolling_text", final_payload.text)
    new_state.round.transcript_window.last_user_final_at = updated.get(
        "last_user_final_at",
        new_state.round.transcript_window.last_user_final_at,
    )
    new_state.round.transcript_window.silence_ms = updated.get("silence_ms", 0)
    new_state.round.transcript_window.user_current_state = updated.get(
        "user_current_state",
        new_state.round.transcript_window.user_current_state,
    )

    new_state.round.transcript_checkpoint_counter += 1

    persistence_intents.extend(
        [
            PersistenceIntent(
                target="transcript_segments",
                operation="append",
                description="Persisted final transcript segment.",
                ref_id=segment["segment_id"],
            ),
            PersistenceIntent(
                target="session_events",
                operation="append",
                description="Recorded transcript.final event.",
                ref_id=new_state.session.session_id,
            ),
        ]
    )

    return NodeResult(
        state=new_state,
        emitted_events=emitted_events,
        persistence_intents=persistence_intents,
        warnings=warnings,
    )