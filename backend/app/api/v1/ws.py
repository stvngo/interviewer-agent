from __future__ import annotations

import asyncio
import random
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.realtime.ws_manager import manager

router = APIRouter()

_CODING_RESPONSES = [
    "That sounds like a good approach. Can you walk me through the time complexity of your solution?",
    "I see what you're doing. Have you considered edge cases like an empty array or negative numbers?",
    "Nice progress. What data structure are you using and why did you choose it?",
    "Can you explain your thought process as you write the code?",
    "That's an interesting solution. How would you optimize it for very large inputs?",
    "Good. Before implementing, can you briefly describe your approach at a high level?",
    "I notice you're iterating through the array. Is there a way to do this in fewer passes?",
    "What happens when the input contains duplicates? Does your solution handle that?",
]

_BEHAVIORAL_RESPONSES = [
    "That's interesting. Can you tell me more about the specific challenges you faced?",
    "How did that experience shape your approach to similar situations?",
    "What would you do differently if you faced that situation again?",
    "Can you elaborate on the outcome and what you learned?",
    "How did you communicate your approach to the rest of the team?",
    "What was the most difficult part of that experience?",
    "How did you measure whether your approach was successful?",
    "Can you give me a specific example of how you handled the conflict?",
]


@router.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: UUID) -> None:
    await manager.connect(session_id, websocket)
    try:
        while True:
            data = await websocket.receive_json()

            msg_type = data.get("type", "")
            content = data.get("content", "")
            round_type = data.get("round_type", "coding")

            if msg_type == "transcript.user" and content:
                responses = _BEHAVIORAL_RESPONSES if round_type == "behavioral" else _CODING_RESPONSES
                reply = random.choice(responses)

                await asyncio.sleep(1.5)

                await manager.broadcast(session_id, {
                    "type": "transcript.interviewer",
                    "content": reply,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })

            elif msg_type == "ping":
                await manager.send_personal(websocket, {
                    "type": "pong",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })

    except WebSocketDisconnect:
        manager.disconnect(session_id, websocket)
