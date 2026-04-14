"use client"

import { useState, useCallback, useRef, useEffect } from "react"
import { MainLayout } from "@/components/main-layout"
import { VoiceAgent } from "@/components/voice-agent"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Play, Square, RotateCcw, ChevronDown, ChevronUp, MessageSquare, Loader2 } from "lucide-react"
import { cn } from "@/lib/utils"
import {
  createSession,
  startSession,
  endSession,
  connectWebSocket,
} from "@/lib/api"

interface TranscriptMessage {
  id: string
  role: "interviewer" | "user"
  content: string
  timestamp: Date
}

const behavioralQuestions = [
  "Tell me about a time when you had to lead a team through a difficult situation.",
  "Describe a situation where you had to deal with a difficult coworker.",
  "Tell me about a project you are most proud of.",
  "Describe a time when you failed and how you handled it.",
  "Tell me about a time when you had to make a difficult decision.",
  "Describe a time you had to learn something new quickly under pressure.",
  "Tell me about a conflict you had with a teammate and how you resolved it.",
  "Give an example of when you went above and beyond expectations.",
]

export default function BehavioralInterviewPage() {
  const [isInterviewActive, setIsInterviewActive] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [currentQuestion, setCurrentQuestion] = useState("")
  const [messages, setMessages] = useState<TranscriptMessage[]>([])
  const [isTranscriptOpen, setIsTranscriptOpen] = useState(false)

  const sessionIdRef = useRef<string | null>(null)
  const wsRef = useRef<WebSocket | null>(null)

  useEffect(() => {
    return () => {
      wsRef.current?.close()
    }
  }, [])

  const pickRandomQuestion = () =>
    behavioralQuestions[Math.floor(Math.random() * behavioralQuestions.length)]

  const handleStartInterview = useCallback(async () => {
    setIsLoading(true)
    try {
      const session = await createSession({ round_type: "behavioral" })
      sessionIdRef.current = session.session_id
      await startSession(session.session_id)

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

      const randomQuestion = pickRandomQuestion()
      setCurrentQuestion(randomQuestion)
      setIsInterviewActive(true)
      setMessages([
        {
          id: "1",
          role: "interviewer",
          content: `Hello! Welcome to your behavioral interview. Let me start with a question: ${randomQuestion}`,
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
        content: "Thank you for sharing your experiences. This concludes our behavioral interview. You did great!",
        timestamp: new Date(),
      },
    ])
  }, [])

  const resetInterview = useCallback(() => {
    setIsInterviewActive(false)
    wsRef.current?.close()
    wsRef.current = null
    sessionIdRef.current = null
    setCurrentQuestion("")
    setMessages([])
  }, [])

  const handleTranscript = useCallback((message: { role: "interviewer" | "user"; content: string }) => {
    setMessages((prev) => [
      ...prev,
      {
        id: Date.now().toString(),
        role: message.role,
        content: message.content,
        timestamp: new Date(),
      },
    ])
  }, [])

  const nextQuestion = useCallback(() => {
    const randomQuestion = pickRandomQuestion()
    setCurrentQuestion(randomQuestion)
    setMessages((prev) => [
      ...prev,
      {
        id: Date.now().toString(),
        role: "interviewer",
        content: `Great answer! Let me ask you another question: ${randomQuestion}`,
        timestamp: new Date(),
      },
    ])
  }, [])

  return (
    <MainLayout>
      <div className="h-[calc(100vh-8rem)] flex flex-col gap-6 max-w-4xl mx-auto">
        {/* Header Controls */}
        <div className="flex items-center justify-between">
          <h1 className="text-xl font-semibold text-foreground">Behavioral Interview</h1>
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

        {/* Main Interview Area */}
        <div className="flex-1 flex flex-col items-center justify-center gap-8">
          {/* Current Question */}
          <Card className="w-full max-w-2xl">
            <CardHeader>
              <CardTitle className="text-center text-lg font-medium">
                {isInterviewActive ? "Current Question" : "Ready to Start"}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-center text-foreground/90 text-lg leading-relaxed">
                {isInterviewActive
                  ? currentQuestion
                  : "Click \"Start Interview\" to begin your behavioral interview practice session."}
              </p>
            </CardContent>
          </Card>

          {/* Voice Agent - Centered */}
          <div className="w-full max-w-md">
            <VoiceAgent isActive={isInterviewActive} sessionId={sessionIdRef.current} onTranscript={handleTranscript} />
          </div>

          {/* Next Question Button */}
          {isInterviewActive && (
            <Button onClick={nextQuestion} variant="outline" className="gap-2">
              <MessageSquare className="h-4 w-4" />
              Next Question
            </Button>
          )}
        </div>

        {/* Transcript Dropdown */}
        <div className="border border-border rounded-lg overflow-hidden bg-card">
          <button
            onClick={() => setIsTranscriptOpen(!isTranscriptOpen)}
            className="w-full flex items-center justify-between px-4 py-3 hover:bg-secondary/50 transition-colors"
          >
            <span className="text-sm font-medium text-foreground">
              Transcript ({messages.length} messages)
            </span>
            {isTranscriptOpen ? (
              <ChevronUp className="h-4 w-4 text-muted-foreground" />
            ) : (
              <ChevronDown className="h-4 w-4 text-muted-foreground" />
            )}
          </button>

          {isTranscriptOpen && (
            <div className="border-t border-border max-h-64 overflow-auto p-4 space-y-3">
              {messages.length === 0 ? (
                <p className="text-sm text-muted-foreground text-center py-4">
                  No transcript yet. Start the interview to see messages.
                </p>
              ) : (
                messages.map((message) => (
                  <div
                    key={message.id}
                    className={cn(
                      "flex flex-col gap-1",
                      message.role === "user" && "items-end"
                    )}
                  >
                    <span className="text-xs text-muted-foreground">
                      {message.role === "interviewer" ? "Interviewer" : "You"} -{" "}
                      {message.timestamp.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                    </span>
                    <div
                      className={cn(
                        "max-w-[80%] px-3 py-2 rounded-lg text-sm",
                        message.role === "interviewer"
                          ? "bg-secondary text-secondary-foreground"
                          : "bg-primary text-primary-foreground"
                      )}
                    >
                      {message.content}
                    </div>
                  </div>
                ))
              )}
            </div>
          )}
        </div>
      </div>
    </MainLayout>
  )
}
