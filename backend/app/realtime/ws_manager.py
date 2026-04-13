from __future__ import annotations

from collections import defaultdict
from uuid import UUID

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self) -> None:
        self._connections: dict[UUID, list[WebSocket]] = defaultdict(list)

    async def connect(self, session_id: UUID, ws: WebSocket) -> None:
        await ws.accept()
        self._connections[session_id].append(ws)

    def disconnect(self, session_id: UUID, ws: WebSocket) -> None:
        conns = self._connections.get(session_id, [])
        if ws in conns:
            conns.remove(ws)
        if not conns:
            self._connections.pop(session_id, None)

    async def broadcast(self, session_id: UUID, message: dict) -> None:
        dead: list[WebSocket] = []
        for ws in self._connections.get(session_id, []):
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(session_id, ws)

    async def send_personal(self, ws: WebSocket, message: dict) -> None:
        await ws.send_json(message)


manager = ConnectionManager()
