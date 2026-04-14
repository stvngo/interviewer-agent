"""Audio WebSocket endpoint: bridges browser mic/speaker with ElevenLabs STT/TTS or ConvAI."""

from __future__ import annotations

import asyncio
import base64
import logging
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.api.v1.sessions import _sessions
from app.api.v1.ws import _build_initial_state, _get_executor, _session_runtime
from app.realtime.ws_manager import manager
from app.services.elevenlabs_service import (
    ConvAISession,
    ElevenLabsConvAIService,
    ElevenLabsSTTService,
    ElevenLabsTTSService,
)

logger = logging.getLogger(__name__)
router = APIRouter()

_convai_service = ElevenLabsConvAIService()
_active_stt: dict[UUID, ElevenLabsSTTService] = {}
_active_convai: dict[UUID, ConvAISession] = {}


async def _handle_langgraph_mode(
    websocket: WebSocket,
    session_id: UUID,
) -> None:
    """LangGraph mode: STT -> LangGraph resume -> TTS -> playback."""
    tts = ElevenLabsTTSService()

    async def on_partial(text: str) -> None:
        await websocket.send_json({
            "type": "transcript.partial",
            "text": text,
            "speaker": "user",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    async def on_committed(text: str) -> None:
        if not text.strip():
            return
        await websocket.send_json({
            "type": "transcript.committed",
            "text": text,
            "speaker": "user",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        executor = _get_executor()
        current = _session_runtime.get(session_id)
        if current is None:
            current = _build_initial_state(session_id)
            loaded = executor.load_session_context_node(current)
            running_state = executor.invoke_coding_graph(loaded)
            _session_runtime[session_id] = running_state
            current = running_state

        resume_payload = {
            "type": "transcript.final",
            "speaker": "user",
            "text": text,
        }
        try:
            next_state = executor.resume_coding_graph(current, resume_payload=resume_payload)
            _session_runtime[session_id] = next_state

            if next_state.interviewer.should_speak and next_state.interviewer.pending_spoken_response:
                spoken = next_state.interviewer.pending_spoken_response
                await websocket.send_json({
                    "type": "transcript.interviewer",
                    "content": spoken,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "response_goal": next_state.interviewer.response_goal,
                    "interruptible": next_state.interviewer.interruptible,
                })
                asyncio.create_task(_stream_tts(websocket, tts, spoken))
        except Exception:
            logger.exception("LangGraph resume failed for session %s", session_id)

    stt = ElevenLabsSTTService(on_partial=on_partial, on_committed=on_committed)
    _active_stt[session_id] = stt
    try:
        await stt.connect()

        executor = _get_executor()
        if session_id not in _session_runtime:
            initial_state = _build_initial_state(session_id)
            loaded = executor.load_session_context_node(initial_state)
            running_state = executor.invoke_coding_graph(loaded)
            _session_runtime[session_id] = running_state
            if running_state.interviewer.should_speak and running_state.interviewer.pending_spoken_response:
                spoken = running_state.interviewer.pending_spoken_response
                await websocket.send_json({
                    "type": "transcript.interviewer",
                    "content": spoken,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "response_goal": running_state.interviewer.response_goal,
                    "interruptible": running_state.interviewer.interruptible,
                })
                asyncio.create_task(_stream_tts(websocket, tts, spoken))

        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type", "")

            if msg_type == "audio.chunk":
                audio_b64 = data.get("audio_base64", "")
                if audio_b64:
                    await stt.send_audio(audio_b64)

            elif msg_type == "audio.control":
                action = data.get("action", "")
                if action == "stop":
                    await stt.commit()
                    break
                elif action == "commit":
                    await stt.commit()

            elif msg_type == "ping":
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })

    finally:
        await stt.close()
        _active_stt.pop(session_id, None)


async def _stream_tts(websocket: WebSocket, tts: ElevenLabsTTSService, text: str) -> None:
    """Stream TTS audio chunks back to the client. Fails silently -- text transcript is the fallback."""
    try:
        async for chunk in tts.stream(text):
            b64 = base64.b64encode(chunk).decode("ascii")
            await websocket.send_json({
                "type": "audio.playback",
                "audio_base64": b64,
                "format": "pcm_16000",
            })
        await websocket.send_json({"type": "audio.playback.end"})
    except Exception as exc:
        logger.warning("TTS unavailable (text transcript still sent): %s", exc)
        try:
            await websocket.send_json({"type": "audio.playback.end", "error": "tts_unavailable"})
        except Exception:
            pass


async def _handle_convai_mode(
    websocket: WebSocket,
    session_id: UUID,
) -> None:
    """ConvAI mode: proxy audio bidirectionally with ElevenLabs ConvAI agent."""
    from pathlib import Path
    prompt_path = Path(__file__).resolve().parents[2] / "prompts" / "runtime" / "interviewer_system.md"
    system_prompt = prompt_path.read_text(encoding="utf-8") if prompt_path.exists() else "You are an interviewer."

    agent_id = await _convai_service.get_or_create_agent(system_prompt)

    async def on_agent_audio(audio_bytes: bytes) -> None:
        b64 = base64.b64encode(audio_bytes).decode("ascii")
        try:
            await websocket.send_json({
                "type": "audio.playback",
                "audio_base64": b64,
                "format": "pcm_16000",
            })
        except Exception:
            pass

    async def on_agent_transcript(text: str) -> None:
        try:
            await websocket.send_json({
                "type": "transcript.interviewer",
                "content": text,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
        except Exception:
            pass

    async def on_user_transcript(text: str) -> None:
        try:
            await websocket.send_json({
                "type": "transcript.committed",
                "text": text,
                "speaker": "user",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
        except Exception:
            pass

    session = await _convai_service.start_conversation_proxy(
        agent_id,
        on_agent_audio=on_agent_audio,
        on_agent_transcript=on_agent_transcript,
        on_user_transcript=on_user_transcript,
    )
    _active_convai[session_id] = session
    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type", "")

            if msg_type == "audio.chunk":
                audio_b64 = data.get("audio_base64", "")
                if audio_b64:
                    await session.send_audio(audio_b64)

            elif msg_type == "audio.control":
                action = data.get("action", "")
                if action == "stop":
                    break

            elif msg_type == "ping":
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })
    finally:
        await session.close()
        _active_convai.pop(session_id, None)


@router.websocket("/ws/audio/{session_id}")
async def audio_websocket_endpoint(websocket: WebSocket, session_id: UUID) -> None:
    await manager.connect(session_id, websocket)
    try:
        init = await websocket.receive_json()
        mode = init.get("mode", "langgraph")

        await websocket.send_json({
            "type": "audio.ready",
            "mode": mode,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        if mode == "convai":
            await _handle_convai_mode(websocket, session_id)
        else:
            await _handle_langgraph_mode(websocket, session_id)

    except WebSocketDisconnect:
        pass
    except Exception as exc:
        logger.exception("Audio WS error for session %s", session_id)
        try:
            await websocket.send_json({
                "type": "audio.error",
                "message": str(exc),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
        except Exception:
            pass
    finally:
        for stt in [_active_stt.pop(session_id, None)]:
            if stt:
                await stt.close()
        for conv in [_active_convai.pop(session_id, None)]:
            if conv:
                await conv.close()
        manager.disconnect(session_id, websocket)
