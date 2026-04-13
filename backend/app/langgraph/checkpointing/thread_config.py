from __future__ import annotations

from uuid import UUID


def build_thread_config(*, session_id: UUID, round_id: UUID | None = None) -> dict:
    thread_id = f"session:{session_id}"
    if round_id is not None:
        thread_id = f"{thread_id}:round:{round_id}"
    return {"configurable": {"thread_id": thread_id}}
