"""ElevenLabs voice services: STT (Scribe), TTS (streaming), and Conversational AI agent proxy."""

from __future__ import annotations

import asyncio
import base64
import json
import logging
import os
from typing import Any, AsyncIterator, Callable, Awaitable

import httpx
import websockets
from websockets.asyncio.client import ClientConnection

logger = logging.getLogger(__name__)

ELEVENLABS_API_BASE = "https://api.elevenlabs.io"
ELEVENLABS_WS_BASE = "wss://api.elevenlabs.io"


def _api_key() -> str:
    key = os.getenv("ELEVENLABS_API_KEY", "")
    if not key:
        raise RuntimeError("ELEVENLABS_API_KEY is required for ElevenLabs services.")
    return key


def _voice_id() -> str:
    return os.getenv("ELEVENLABS_VOICE_ID", "cgSgspJ2msm6clMCkdW9")


def _tts_model() -> str:
    return os.getenv("ELEVENLABS_MODEL_ID", "eleven_flash_v2_5")


# ---------------------------------------------------------------------------
# STT -- Scribe Realtime WebSocket
# ---------------------------------------------------------------------------

class ElevenLabsSTTService:
    """
    Streams PCM 16kHz audio to ElevenLabs Scribe realtime WebSocket and
    delivers partial / committed transcripts via async callbacks.
    """

    def __init__(
        self,
        *,
        on_partial: Callable[[str], Awaitable[None]] | None = None,
        on_committed: Callable[[str], Awaitable[None]] | None = None,
        language_code: str = "en",
    ) -> None:
        self.on_partial = on_partial
        self.on_committed = on_committed
        self.language_code = language_code
        self._ws: ClientConnection | None = None
        self._listen_task: asyncio.Task[None] | None = None
        self._closed = False

    async def connect(self) -> None:
        url = (
            f"{ELEVENLABS_WS_BASE}/v1/speech-to-text/realtime"
            f"?model_id=scribe_v2_realtime"
            f"&audio_format=pcm_16000"
            f"&commit_strategy=vad"
            f"&language_code={self.language_code}"
            f"&vad_silence_threshold_secs=1.2"
        )
        extra_headers = {"xi-api-key": _api_key()}
        self._ws = await websockets.connect(url, additional_headers=extra_headers)
        self._closed = False
        self._listen_task = asyncio.create_task(self._listen_loop())

    async def send_audio(self, pcm_b64: str) -> None:
        if self._ws is None or self._closed:
            return
        msg = json.dumps({
            "message_type": "input_audio_chunk",
            "audio_base_64": pcm_b64,
            "commit": False,
            "sample_rate": 16000,
        })
        try:
            await self._ws.send(msg)
        except Exception:
            logger.warning("STT send_audio failed, marking connection closed")
            self._closed = True

    async def commit(self) -> None:
        """Force-commit current audio buffer."""
        if self._ws is None or self._closed:
            return
        msg = json.dumps({
            "message_type": "input_audio_chunk",
            "audio_base_64": "",
            "commit": True,
            "sample_rate": 16000,
        })
        try:
            await self._ws.send(msg)
        except Exception:
            logger.warning("STT commit failed, marking connection closed")
            self._closed = True

    async def close(self) -> None:
        self._closed = True
        if self._listen_task and not self._listen_task.done():
            self._listen_task.cancel()
        if self._ws:
            try:
                await self._ws.close()
            except Exception:
                pass
            self._ws = None

    async def _listen_loop(self) -> None:
        assert self._ws is not None
        try:
            async for raw in self._ws:
                if self._closed:
                    break
                data = json.loads(raw)
                mt = data.get("message_type", "")
                if mt == "partial_transcript" and self.on_partial:
                    await self.on_partial(data.get("text", ""))
                elif mt in ("committed_transcript", "committed_transcript_with_timestamps") and self.on_committed:
                    await self.on_committed(data.get("text", ""))
                elif mt in ("error", "auth_error", "quota_exceeded", "rate_limited"):
                    logger.error("STT error from ElevenLabs: %s", data)
                    self._closed = True
                    break
        except asyncio.CancelledError:
            pass
        except Exception:
            logger.exception("STT listen loop error")
        finally:
            self._closed = True


# ---------------------------------------------------------------------------
# TTS -- Streaming HTTP
# ---------------------------------------------------------------------------

class ElevenLabsTTSService:
    """
    Converts text to speech via ElevenLabs streaming HTTP endpoint.
    Returns an async iterator of raw audio bytes (PCM 16kHz or MP3).
    """

    def __init__(
        self,
        *,
        voice_id: str | None = None,
        model_id: str | None = None,
        output_format: str = "pcm_16000",
    ) -> None:
        self.voice_id = voice_id or _voice_id()
        self.model_id = model_id or _tts_model()
        self.output_format = output_format

    async def stream(self, text: str) -> AsyncIterator[bytes]:
        """Stream TTS audio chunks for the given text."""
        url = (
            f"{ELEVENLABS_API_BASE}/v1/text-to-speech/{self.voice_id}/stream"
            f"?output_format={self.output_format}"
            f"&optimize_streaming_latency=3"
        )
        headers = {
            "xi-api-key": _api_key(),
            "Content-Type": "application/json",
        }
        body = {
            "text": text,
            "model_id": self.model_id,
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.8,
                "style": 0.0,
                "use_speaker_boost": True,
            },
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            async with client.stream("POST", url, headers=headers, json=body) as resp:
                if resp.status_code != 200:
                    error_body = await resp.aread()
                    logger.error("TTS API error %s: %s", resp.status_code, error_body.decode(errors="replace"))
                    resp.raise_for_status()
                async for chunk in resp.aiter_bytes(chunk_size=4096):
                    yield chunk

    async def synthesize_full(self, text: str) -> bytes:
        """Synthesize full audio and return as a single bytes object."""
        chunks: list[bytes] = []
        async for chunk in self.stream(text):
            chunks.append(chunk)
        return b"".join(chunks)


# ---------------------------------------------------------------------------
# Conversational AI Agent
# ---------------------------------------------------------------------------

class ElevenLabsConvAIService:
    """
    Manages ElevenLabs Conversational AI agents and proxies audio between
    the browser WebSocket and ElevenLabs ConvAI WebSocket.
    """

    def __init__(self) -> None:
        self._cached_agent_id: str | None = os.getenv("ELEVENLABS_CONVAI_AGENT_ID")

    async def create_interview_agent(
        self,
        *,
        system_prompt: str,
        first_message: str = "Hi! I'm your interviewer today. Let's get started. Tell me a little about yourself and what role you're preparing for.",
        voice_id: str | None = None,
    ) -> str:
        """Create a ConvAI agent via the ElevenLabs API and return the agent_id."""
        url = f"{ELEVENLABS_API_BASE}/v1/convai/agents/create"
        headers = {"xi-api-key": _api_key(), "Content-Type": "application/json"}
        body: dict[str, Any] = {
            "name": "Interview Agent",
            "conversation_config": {
                "agent": {
                    "prompt": {
                        "prompt": system_prompt,
                    },
                    "first_message": first_message,
                    "language": "en",
                },
                "asr": {
                    "quality": "high",
                },
                "tts": {
                    "model_id": _tts_model(),
                    "voice_id": voice_id or _voice_id(),
                    "optimize_streaming_latency": 3,
                    "stability": 0.5,
                    "similarity_boost": 0.8,
                },
                "turn": {
                    "turn_timeout": 7,
                    "mode": {
                        "type": "conversational",
                    },
                },
                "conversation": {
                    "max_duration_seconds": 1800,
                },
            },
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, headers=headers, json=body)
            resp.raise_for_status()
            data = resp.json()
        agent_id = data.get("agent_id", "")
        self._cached_agent_id = agent_id
        logger.info("Created ElevenLabs ConvAI agent: %s", agent_id)
        return agent_id

    async def get_or_create_agent(self, system_prompt: str) -> str:
        if self._cached_agent_id:
            return self._cached_agent_id
        return await self.create_interview_agent(system_prompt=system_prompt)

    async def start_conversation_proxy(
        self,
        agent_id: str,
        *,
        on_agent_audio: Callable[[bytes], Awaitable[None]],
        on_agent_transcript: Callable[[str], Awaitable[None]],
        on_user_transcript: Callable[[str], Awaitable[None]],
    ) -> ConvAISession:
        """
        Opens a WebSocket to the ElevenLabs ConvAI endpoint and returns
        a ConvAISession that can send/receive audio.
        """
        url = f"{ELEVENLABS_WS_BASE}/v1/convai/conversation?agent_id={agent_id}"
        extra_headers = {"xi-api-key": _api_key()}
        ws = await websockets.connect(url, additional_headers=extra_headers)
        session = ConvAISession(
            ws=ws,
            on_agent_audio=on_agent_audio,
            on_agent_transcript=on_agent_transcript,
            on_user_transcript=on_user_transcript,
        )
        session.start()
        return session


class ConvAISession:
    """Async wrapper around a single ElevenLabs ConvAI conversation WebSocket."""

    def __init__(
        self,
        *,
        ws: ClientConnection,
        on_agent_audio: Callable[[bytes], Awaitable[None]],
        on_agent_transcript: Callable[[str], Awaitable[None]],
        on_user_transcript: Callable[[str], Awaitable[None]],
    ) -> None:
        self._ws = ws
        self._on_agent_audio = on_agent_audio
        self._on_agent_transcript = on_agent_transcript
        self._on_user_transcript = on_user_transcript
        self._listen_task: asyncio.Task[None] | None = None
        self._closed = False

    def start(self) -> None:
        self._listen_task = asyncio.create_task(self._listen_loop())

    async def send_audio(self, pcm_b64: str) -> None:
        if self._closed:
            return
        msg = json.dumps({"user_audio_chunk": pcm_b64})
        try:
            await self._ws.send(msg)
        except Exception:
            logger.exception("ConvAI send_audio failed")

    async def close(self) -> None:
        self._closed = True
        if self._listen_task and not self._listen_task.done():
            self._listen_task.cancel()
        try:
            await self._ws.close()
        except Exception:
            pass

    async def _listen_loop(self) -> None:
        try:
            async for raw in self._ws:
                if self._closed:
                    break
                if isinstance(raw, bytes):
                    await self._on_agent_audio(raw)
                    continue
                data = json.loads(raw)
                msg_type = data.get("type", "")
                if msg_type == "audio" and "audio" in data:
                    audio_bytes = base64.b64decode(data["audio"])
                    await self._on_agent_audio(audio_bytes)
                elif msg_type == "agent_response":
                    await self._on_agent_transcript(data.get("text", data.get("agent_response", "")))
                elif msg_type == "user_transcript":
                    await self._on_user_transcript(data.get("text", data.get("user_transcript", "")))
                elif msg_type == "interruption":
                    logger.debug("ConvAI: user interrupted agent")
                elif msg_type == "error":
                    logger.error("ConvAI error: %s", data)
        except asyncio.CancelledError:
            pass
        except Exception:
            logger.exception("ConvAI listen loop error")
