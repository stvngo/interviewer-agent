"use client"

import { useState, useCallback, useRef, useEffect } from "react"
import { MainLayout } from "@/components/main-layout"
import { ProblemPanel, type Problem } from "@/components/problem-panel"
import { CodeEditor } from "@/components/code-editor"
import { VoiceAgent } from "@/components/voice-agent"
import { Transcript, type TranscriptMessage } from "@/components/transcript"
import { NotesPanel } from "@/components/notes-panel"
import { Button } from "@/components/ui/button"
import { Play, Square, RotateCcw, Loader2 } from "lucide-react"
import {
  createSession,
  startSession,
  endSession,
  getRandomQuestion,
  submitCodeEvent,
  connectWebSocket,
  sendCodeChanged,
  type Question,
} from "@/lib/api"

const fallbackProblem: Problem = {
  title: "Loading...",
  difficulty: "Medium",
  description: "Fetching a problem from the server...",
  examples: [],
  constraints: [],
}

const initialCode = `// Your solution here\n`

function questionToProblem(q: Question): Problem {
  return {
    title: q.title,
    difficulty: q.difficulty,
    description: q.description,
    examples: q.examples.map((e) => ({
      input: e.input,
      output: e.output,
      explanation: e.explanation ?? undefined,
    })),
    constraints: q.constraints,
  }
}

export default function TechnicalInterviewPage() {
  const [isInterviewActive, setIsInterviewActive] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [problem, setProblem] = useState<Problem>(fallbackProblem)
  const [code, setCode] = useState(initialCode)
  const [notes, setNotes] = useState("")
  const [messages, setMessages] = useState<TranscriptMessage[]>([])

  const sessionIdRef = useRef<string | null>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const codeTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    return () => {
      wsRef.current?.close()
      if (codeTimerRef.current) clearTimeout(codeTimerRef.current)
    }
  }, [])

  const handleStartInterview = useCallback(async () => {
    setIsLoading(true)
    try {
      const session = await createSession({ round_type: "coding" })
      sessionIdRef.current = session.session_id
      await startSession(session.session_id)

      const q = await getRandomQuestion()
      setProblem(questionToProblem(q))

      const ws = connectWebSocket(session.session_id, {
        onMessage: (data) => {
          if (data.type === "transcript.interviewer") {
            setMessages((prev) => [
              ...prev,
              {
                id: Date.now().toString(),
                role: "interviewer",
                content: data.content as string,
                timestamp: new Date(),
              },
            ])
          }
        },
      })
      wsRef.current = ws

      setIsInterviewActive(true)
      setMessages([
        {
          id: "1",
          role: "interviewer",
          content: `Hello! Welcome to your technical interview. Today we'll be working on "${q.title}". Please take a moment to read the problem description and let me know when you're ready to discuss your approach.`,
          timestamp: new Date(),
        },
      ])
    } catch (err) {
      console.error("Failed to start interview:", err)
      setMessages([
        {
          id: "err",
          role: "interviewer",
          content: "Failed to connect to the server. Make sure the backend is running on port 8000.",
          timestamp: new Date(),
        },
      ])
    } finally {
      setIsLoading(false)
    }
  }, [])

  const handleEndInterview = useCallback(async () => {
    setIsInterviewActive(false)
    wsRef.current?.close()
    wsRef.current = null

    if (sessionIdRef.current) {
      try {
        await endSession(sessionIdRef.current)
      } catch {
        // best-effort
      }
    }

    setMessages((prev) => [
      ...prev,
      {
        id: Date.now().toString(),
        role: "interviewer",
        content: "Thank you for completing this interview session. Great job working through the problem!",
        timestamp: new Date(),
      },
    ])
  }, [])

  const resetInterview = useCallback(() => {
    setIsInterviewActive(false)
    wsRef.current?.close()
    wsRef.current = null
    sessionIdRef.current = null
    setProblem(fallbackProblem)
    setCode(initialCode)
    setNotes("")
    setMessages([])
  }, [])

  const handleTranscript = useCallback(
    (message: { role: "interviewer" | "user"; content: string }) => {
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now().toString(),
          role: message.role,
          content: message.content,
          timestamp: new Date(),
        },
      ])
    },
    []
  )

  const handleCodeChange = useCallback(
    (value: string) => {
      setCode(value)

      if (codeTimerRef.current) clearTimeout(codeTimerRef.current)
      if (!sessionIdRef.current || !isInterviewActive) return

      const sid = sessionIdRef.current
      codeTimerRef.current = setTimeout(() => {
        if (wsRef.current?.readyState === WebSocket.OPEN) {
          sendCodeChanged(wsRef.current, {
            language: "javascript",
            content_snapshot: value,
            file_path: "main",
          })
        }
        submitCodeEvent({
          session_id: sid,
          language: "javascript",
          content: value,
        }).catch(() => {})
      }, 2000)
    },
    [isInterviewActive]
  )

  return (
    <MainLayout>
      <div className="h-[calc(100vh-8rem)] flex flex-col gap-4">
        {/* Header Controls */}
        <div className="flex items-center justify-between">
          <h1 className="text-xl font-semibold text-foreground">Technical Interview</h1>
          <div className="flex items-center gap-2">
            {!isInterviewActive ? (
              <Button onClick={handleStartInterview} className="gap-2" disabled={isLoading}>
                {isLoading ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Play className="h-4 w-4" />
                )}
                {isLoading ? "Starting..." : "Start Interview"}
              </Button>
            ) : (
              <Button onClick={handleEndInterview} variant="destructive" className="gap-2">
                <Square className="h-4 w-4" />
                End Interview
              </Button>
            )}
            <Button onClick={resetInterview} variant="outline" size="icon">
              <RotateCcw className="h-4 w-4" />
            </Button>
          </div>
        </div>

        {/* Main Content - 30:70 split */}
        <div className="flex-1 flex gap-4 overflow-hidden">
          {/* Left Panel - Problem + Voice + Transcript (30%) */}
          <div className="w-[30%] flex flex-col gap-4 overflow-hidden">
            <ProblemPanel problem={problem} className="flex-1 min-h-0" />
            <VoiceAgent isActive={isInterviewActive} sessionId={sessionIdRef.current} onTranscript={handleTranscript} />
            <Transcript messages={messages} className="h-48" />
          </div>

          {/* Right Panel - Code Editor + Notes (70%) */}
          <div className="w-[70%] flex flex-col gap-4 overflow-hidden">
            <CodeEditor
              value={code}
              onChange={handleCodeChange}
              language="javascript"
              className="flex-1 min-h-0"
            />
            <NotesPanel value={notes} onChange={setNotes} />
          </div>
        </div>
      </div>
    </MainLayout>
  )
}
