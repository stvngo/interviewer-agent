"""
Purpose: Update code-derived runtime state.

Reads
- code events

Calls
- code_event_service

Writes
- code_window
- checkpoint counters
- code progress state

Emits
- code.checkpoint_created optionally

DB writes
- code_events
- optional code_snapshots
"""

from __future__ import annotations

from typing import Any, cast

from app.langgraph.runtime.node_contracts import NodeExecutionContext, NodeResult, PersistenceIntent
from app.langgraph.state import RuntimeState
from app.realtime.event_contracts import CodeChangedEvent, CodeRunCompletedEvent


def process_code_signal(
    state: RuntimeState,
    *,
    event: CodeChangedEvent | CodeRunCompletedEvent,
    code_event_service: Any,
    ctx: NodeExecutionContext | None = None,
) -> NodeResult:
    """
    Update code-derived runtime state and persist meaningful code events.

    Expected service methods:
    - code_event_service.persist_code_change(...) -> dict
    - code_event_service.persist_code_run(...) -> dict
    - code_event_service.summarize_code_window(...) -> dict
    """

    ctx = ctx or NodeExecutionContext(
        trigger_event_type=event.event_type,
        trigger_source=event.source,
        actor="provider" if event.source == "code_runner" else "user",
    )
    new_state = state.model_copy(deep=True)
    emitted_events = []
    persistence_intents = []
    warnings = []

    if isinstance(event, CodeChangedEvent):
        payload = event.payload

        persisted = code_event_service.persist_code_change(
            session_id=new_state.session.session_id,
            round_id=new_state.round.round_id,
            session_question_id=new_state.round.session_question_id,
            language=payload.language,
            file_path=payload.file_path,
            content_snapshot=payload.content_snapshot,
            content_hash=payload.content_hash,
            diff_summary=payload.diff_summary,
        )

        summary = code_event_service.summarize_code_window(
            code_window=new_state.round.code_window.model_dump(),
            event_type="code.changed",
            persisted_event_id=persisted["code_event_id"],
            language=payload.language,
            content_hash=payload.content_hash,
        )

        new_state.round.code_window.recent_code_event_ids = summary.get(
            "recent_code_event_ids",
            new_state.round.code_window.recent_code_event_ids + [persisted["code_event_id"]],
        )
        new_state.round.code_window.latest_language = summary.get("latest_language", payload.language)
        new_state.round.code_window.latest_snapshot_hash = summary.get("latest_snapshot_hash", payload.content_hash)
        new_state.round.code_window.code_progress_state = summary.get(
            "code_progress_state",
            new_state.round.code_window.code_progress_state,
        )

        new_state.round.code_checkpoint_counter += 1

        persistence_intents.extend(
            [
                PersistenceIntent(
                    target="code_events",
                    operation="append",
                    description="Persisted code change event.",
                    ref_id=persisted["code_event_id"],
                ),
                PersistenceIntent(
                    target="session_events",
                    operation="append",
                    description="Recorded code.changed event.",
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

    payload = cast(CodeRunCompletedEvent, event).payload

    persisted = code_event_service.persist_code_run(
        session_id=new_state.session.session_id,
        round_id=new_state.round.round_id,
        session_question_id=new_state.round.session_question_id,
        stdout=payload.stdout,
        stderr=payload.stderr,
        exit_code=payload.exit_code,
        runtime_ms=payload.runtime_ms,
        tests_passed=payload.tests_passed,
        tests_failed=payload.tests_failed,
    )

    summary = code_event_service.summarize_code_window(
        code_window=new_state.round.code_window.model_dump(),
        event_type="code.run_completed",
        persisted_event_id=persisted["code_event_id"],
        stdout=payload.stdout,
        stderr=payload.stderr,
        tests_passed=payload.tests_passed,
        tests_failed=payload.tests_failed,
        exit_code=payload.exit_code,
    )

    new_state.round.code_window.recent_code_event_ids = summary.get(
        "recent_code_event_ids",
        new_state.round.code_window.recent_code_event_ids + [persisted["code_event_id"]],
    )
    new_state.round.code_window.last_run_status = summary.get(
        "last_run_status",
        new_state.round.code_window.last_run_status,
    )
    new_state.round.code_window.code_progress_state = summary.get(
        "code_progress_state",
        new_state.round.code_window.code_progress_state,
    )
    new_state.round.code_window.latest_stdout_excerpt = summary.get("latest_stdout_excerpt")
    new_state.round.code_window.latest_stderr_excerpt = summary.get("latest_stderr_excerpt")
    new_state.round.code_window.tests_passed = summary.get("tests_passed")
    new_state.round.code_window.tests_failed = summary.get("tests_failed")

    new_state.round.code_checkpoint_counter += 1

    persistence_intents.extend(
        [
            PersistenceIntent(
                target="code_events",
                operation="append",
                description="Persisted code run completion event.",
                ref_id=persisted["code_event_id"],
            ),
            PersistenceIntent(
                target="session_events",
                operation="append",
                description="Recorded code.run_completed event.",
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