"use client"

import { useState, useEffect, useRef, useCallback } from "react"
import { Mic, MicOff, Volume2, VolumeX } from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

interface VoiceAgentProps {
  isActive: boolean
  sessionId?: string | null
  mode?: "langgraph" | "convai"
  onTranscript?: (message: { role: "interviewer" | "user"; content: string }) => void
  onPartialTranscript?: (text: string) => void
}

const CHUNK_INTERVAL_MS = 250
const TARGET_SAMPLE_RATE = 16000

function downsampleBuffer(buffer: Float32Array, inputRate: number, outputRate: number): Int16Array {
  if (inputRate === outputRate) {
    const result = new Int16Array(buffer.length)
    for (let i = 0; i < buffer.length; i++) {
      const s = Math.max(-1, Math.min(1, buffer[i]))
      result[i] = s < 0 ? s * 0x8000 : s * 0x7fff
    }
    return result
  }
  const ratio = inputRate / outputRate
  const newLength = Math.round(buffer.length / ratio)
  const result = new Int16Array(newLength)
  for (let i = 0; i < newLength; i++) {
    const index = Math.round(i * ratio)
    const s = Math.max(-1, Math.min(1, buffer[index] ?? 0))
    result[i] = s < 0 ? s * 0x8000 : s * 0x7fff
  }
  return result
}

function int16ToBase64(pcm: Int16Array): string {
  const bytes = new Uint8Array(pcm.buffer, pcm.byteOffset, pcm.byteLength)
  let binary = ""
  for (let i = 0; i < bytes.length; i++) {
    binary += String.fromCharCode(bytes[i])
  }
  return btoa(binary)
}

export function VoiceAgent({ isActive, sessionId, mode = "langgraph", onTranscript, onPartialTranscript }: VoiceAgentProps) {
  const [isMuted, setIsMuted] = useState(false)
  const [isSpeakerMuted, setIsSpeakerMuted] = useState(false)
  const [isConnected, setIsConnected] = useState(false)
  const [audioLevel, setAudioLevel] = useState(0)
  const [partialText, setPartialText] = useState("")

  const wsRef = useRef<WebSocket | null>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const audioCtxRef = useRef<AudioContext | null>(null)
  const analyserRef = useRef<AnalyserNode | null>(null)
  const processorRef = useRef<ScriptProcessorNode | null>(null)
  const sourceRef = useRef<MediaStreamAudioSourceNode | null>(null)
  const playbackCtxRef = useRef<AudioContext | null>(null)
  const animFrameRef = useRef<number>(0)
  const chunkBufferRef = useRef<Float32Array[]>([])
  const chunkTimerRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const cleanup = useCallback(() => {
    if (chunkTimerRef.current) {
      clearInterval(chunkTimerRef.current)
      chunkTimerRef.current = null
    }
    if (animFrameRef.current) {
      cancelAnimationFrame(animFrameRef.current)
      animFrameRef.current = 0
    }
    processorRef.current?.disconnect()
    sourceRef.current?.disconnect()
    analyserRef.current?.disconnect()
    processorRef.current = null
    sourceRef.current = null
    analyserRef.current = null

    if (audioCtxRef.current && audioCtxRef.current.state !== "closed") {
      audioCtxRef.current.close().catch(() => {})
    }
    audioCtxRef.current = null

    streamRef.current?.getTracks().forEach((t) => t.stop())
    streamRef.current = null

    if (wsRef.current && wsRef.current.readyState <= WebSocket.OPEN) {
      try {
        wsRef.current.send(JSON.stringify({ type: "audio.control", action: "stop" }))
      } catch {}
      wsRef.current.close()
    }
    wsRef.current = null
    setIsConnected(false)
    setAudioLevel(0)
    setPartialText("")
    chunkBufferRef.current = []
  }, [])

  useEffect(() => {
    if (!isActive || !sessionId) {
      cleanup()
      return
    }

    let cancelled = false

    async function start() {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          audio: { echoCancellation: true, noiseSuppression: true, sampleRate: TARGET_SAMPLE_RATE },
        })
        if (cancelled) { stream.getTracks().forEach((t) => t.stop()); return }
        streamRef.current = stream

        const audioCtx = new AudioContext({ sampleRate: stream.getAudioTracks()[0]?.getSettings().sampleRate || 44100 })
        audioCtxRef.current = audioCtx

        const source = audioCtx.createMediaStreamSource(stream)
        sourceRef.current = source

        const analyser = audioCtx.createAnalyser()
        analyser.fftSize = 256
        analyserRef.current = analyser
        source.connect(analyser)

        const processor = audioCtx.createScriptProcessor(4096, 1, 1)
        processorRef.current = processor
        processor.onaudioprocess = (e) => {
          if (isMuted) return
          const input = e.inputBuffer.getChannelData(0)
          chunkBufferRef.current.push(new Float32Array(input))
        }
        source.connect(processor)
        processor.connect(audioCtx.destination)

        playbackCtxRef.current = new AudioContext({ sampleRate: TARGET_SAMPLE_RATE })

        const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1"
        const wsUrl = apiUrl.replace(/^http/, "ws")
        const ws = new WebSocket(`${wsUrl}/ws/audio/${sessionId}`)
        wsRef.current = ws

        ws.onopen = () => {
          ws.send(JSON.stringify({ mode }))
          setIsConnected(true)
        }

        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data)
            handleServerMessage(data)
          } catch {}
        }

        ws.onclose = () => {
          setIsConnected(false)
        }

        ws.onerror = () => {
          setIsConnected(false)
        }

        chunkTimerRef.current = setInterval(() => {
          if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return
          if (chunkBufferRef.current.length === 0) return

          const totalLen = chunkBufferRef.current.reduce((acc, b) => acc + b.length, 0)
          const merged = new Float32Array(totalLen)
          let offset = 0
          for (const buf of chunkBufferRef.current) {
            merged.set(buf, offset)
            offset += buf.length
          }
          chunkBufferRef.current = []

          const pcm16 = downsampleBuffer(merged, audioCtx.sampleRate, TARGET_SAMPLE_RATE)
          const b64 = int16ToBase64(pcm16)
          wsRef.current.send(JSON.stringify({ type: "audio.chunk", audio_base64: b64 }))
        }, CHUNK_INTERVAL_MS)

        const freqData = new Uint8Array(analyser.frequencyBinCount)
        function updateLevel() {
          if (!analyserRef.current) return
          analyserRef.current.getByteFrequencyData(freqData)
          const avg = freqData.reduce((a, b) => a + b, 0) / freqData.length
          setAudioLevel(avg)
          animFrameRef.current = requestAnimationFrame(updateLevel)
        }
        updateLevel()

      } catch (err) {
        console.error("VoiceAgent: failed to start", err)
      }
    }

    start()
    return () => { cancelled = true; cleanup() }
  }, [isActive, sessionId, mode, cleanup])

  useEffect(() => {
    if (streamRef.current) {
      streamRef.current.getAudioTracks().forEach((t) => { t.enabled = !isMuted })
    }
  }, [isMuted])

  function handleServerMessage(data: Record<string, unknown>) {
    const type = data.type as string

    if (type === "transcript.partial") {
      const text = data.text as string
      setPartialText(text)
      onPartialTranscript?.(text)
    } else if (type === "transcript.committed") {
      const text = data.text as string
      setPartialText("")
      onTranscript?.({ role: "user", content: text })
    } else if (type === "transcript.interviewer") {
      const content = data.content as string
      onTranscript?.({ role: "interviewer", content })
    } else if (type === "audio.playback") {
      if (!isSpeakerMuted) {
        playAudioChunk(data.audio_base64 as string)
      }
    }
  }

  function playAudioChunk(b64: string) {
    if (!playbackCtxRef.current) return
    try {
      const binary = atob(b64)
      const bytes = new Uint8Array(binary.length)
      for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i)

      const int16 = new Int16Array(bytes.buffer)
      const float32 = new Float32Array(int16.length)
      for (let i = 0; i < int16.length; i++) {
        float32[i] = int16[i] / (int16[i] < 0 ? 0x8000 : 0x7fff)
      }

      const ctx = playbackCtxRef.current
      const audioBuffer = ctx.createBuffer(1, float32.length, TARGET_SAMPLE_RATE)
      audioBuffer.getChannelData(0).set(float32)
      const source = ctx.createBufferSource()
      source.buffer = audioBuffer
      source.connect(ctx.destination)
      source.start()
    } catch (err) {
      console.error("VoiceAgent: playback error", err)
    }
  }

  const barCount = 16
  const bars = Array.from({ length: barCount }, (_, i) => {
    if (!isActive || !isConnected || isMuted) return 4
    const variation = Math.sin(Date.now() / 100 + i * 0.5) * 0.3 + 0.7
    return Math.max(4, (audioLevel / 255) * 48 * variation)
  })

  return (
    <div className="bg-card rounded-lg border border-border p-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-medium text-foreground">Voice Agent</h3>
        <div className="flex items-center gap-2">
          {mode === "convai" && (
            <span className="text-[10px] font-medium text-muted-foreground bg-muted px-1.5 py-0.5 rounded">
              ConvAI
            </span>
          )}
          <div className={cn(
            "w-2 h-2 rounded-full",
            isConnected ? "bg-emerald-500 animate-pulse" : isActive ? "bg-amber-500" : "bg-muted-foreground"
          )} />
        </div>
      </div>

      {/* Audio Visualization */}
      <div className="flex items-center justify-center gap-[3px] h-16 mb-4">
        {bars.map((height, i) => (
          <div
            key={i}
            className="w-1.5 bg-foreground/30 rounded-full transition-all duration-75"
            style={{ height: `${height}px` }}
          />
        ))}
      </div>

      {/* Partial transcript */}
      {partialText && (
        <p className="text-xs text-muted-foreground text-center mb-3 truncate italic">
          {partialText}
        </p>
      )}

      {/* Controls */}
      <div className="flex items-center justify-center gap-3">
        <Button
          variant="outline"
          size="icon"
          onClick={() => setIsSpeakerMuted(!isSpeakerMuted)}
          disabled={!isActive}
          className={cn(
            "h-10 w-10",
            isSpeakerMuted && "bg-destructive/20 border-destructive text-destructive"
          )}
        >
          {isSpeakerMuted ? <VolumeX className="h-4 w-4" /> : <Volume2 className="h-4 w-4" />}
        </Button>

        <Button
          variant={isConnected && !isMuted ? "default" : "outline"}
          size="icon"
          onClick={() => setIsMuted(!isMuted)}
          disabled={!isActive}
          className={cn(
            "h-12 w-12 rounded-full",
            isConnected && !isMuted && "bg-primary animate-pulse"
          )}
        >
          {isMuted ? (
            <MicOff className="h-5 w-5" />
          ) : (
            <Mic className="h-5 w-5" />
          )}
        </Button>
      </div>

      {isActive && (
        <p className="text-xs text-muted-foreground text-center mt-3">
          {!isConnected
            ? "Connecting..."
            : isMuted
            ? "Microphone muted"
            : "Listening..."}
        </p>
      )}
    </div>
  )
}
