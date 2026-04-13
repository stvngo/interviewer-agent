"use client"

import { useState, useCallback } from "react"
import { MainLayout } from "@/components/main-layout"
import { VoiceAgent } from "@/components/voice-agent"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Play, Square, RotateCcw, ChevronDown, ChevronUp, MessageSquare } from "lucide-react"
import { cn } from "@/lib/utils"

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
]

export default function BehavioralInterviewPage() {
  const [isInterviewActive, setIsInterviewActive] = useState(false)
  const [currentQuestion, setCurrentQuestion] = useState("")
  const [messages, setMessages] = useState<TranscriptMessage[]>([])
  const [isTranscriptOpen, setIsTranscriptOpen] = useState(false)

  const startInterview = useCallback(() => {
    setIsInterviewActive(true)
    const randomQuestion = behavioralQuestions[Math.floor(Math.random() * behavioralQuestions.length)]
    setCurrentQuestion(randomQuestion)
    setMessages([
      {
        id: "1",
        role: "interviewer",
        content: `Hello! Welcome to your behavioral interview. Let me start with a question: ${randomQuestion}`,
        timestamp: new Date(),
      },
    ])
  }, [])

  const endInterview = useCallback(() => {
    setIsInterviewActive(false)
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

    // Simulate interviewer follow-up
    if (message.role === "user") {
      setTimeout(() => {
        const followUps = [
          "That is interesting. Can you tell me more about the specific challenges you faced?",
          "How did that experience shape your approach to similar situations?",
          "What would you do differently if you faced that situation again?",
          "Can you elaborate on the outcome and what you learned?",
        ]
        const randomFollowUp = followUps[Math.floor(Math.random() * followUps.length)]
        setMessages((prev) => [
          ...prev,
          {
            id: (Date.now() + 1).toString(),
            role: "interviewer",
            content: randomFollowUp,
            timestamp: new Date(),
          },
        ])
      }, 2000)
    }
  }, [])

  const nextQuestion = useCallback(() => {
    const randomQuestion = behavioralQuestions[Math.floor(Math.random() * behavioralQuestions.length)]
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
              <Button onClick={startInterview} className="gap-2">
                <Play className="h-4 w-4" />
                Start Interview
              </Button>
            ) : (
              <Button onClick={endInterview} variant="destructive" className="gap-2">
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
            <VoiceAgent isActive={isInterviewActive} onTranscript={handleTranscript} />
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
