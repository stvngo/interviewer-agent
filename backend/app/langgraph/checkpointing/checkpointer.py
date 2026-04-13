from __future__ import annotations

from pathlib import Path
from typing import Any

from langgraph.checkpoint.memory import InMemorySaver


_default_checkpointer: Any | None = None


def get_checkpointer() -> Any:
    """
    Return a reusable checkpointer instance for localhost runtime.

    Prefer in-process durability for now; callers should keep this singleton
    alive for session lifetime so interrupt/resume works reliably.
    """
    global _default_checkpointer
    if _default_checkpointer is None:
        _default_checkpointer = InMemorySaver()
    return _default_checkpointer


def ensure_checkpoint_dir() -> Path:
    checkpoint_dir = Path("backend/.checkpoints")
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    return checkpoint_dir
