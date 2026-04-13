from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class FilePersistenceSink:
    """
    Lightweight persistence sink for node persistence intents.

    Writes JSONL records so localhost runs preserve state mutations even when
    backing DB services are still being implemented.
    """

    def __init__(self, path: str = "backend/.runtime/persistence_intents.jsonl") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def record(self, intent: Any, *, node_name: str | None = None) -> None:
        payload = intent.model_dump(mode="json") if hasattr(intent, "model_dump") else dict(intent)
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "node_name": node_name,
            "intent": payload,
        }
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
