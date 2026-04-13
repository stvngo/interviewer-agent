"use client"

import { useState, useCallback } from "react"
import { MainLayout } from "@/components/main-layout"
import { ProblemPanel, type Problem } from "@/components/problem-panel"
import { CodeEditor } from "@/components/code-editor"
import { VoiceAgent } from "@/components/voice-agent"
import { Transcript, type TranscriptMessage } from "@/components/transcript"
import { NotesPanel } from "@/components/notes-panel"
import { Button } from "@/components/ui/button"
import { Play, Square, RotateCcw } from "lucide-react"

const sampleProblem: Problem = {
  title: "Two Sum",
  difficulty: "Easy",
  description: `Given an array of integers nums and an integer target, return indices of the two numbers such that they add up to target.

You may assume that each input would have exactly one solution, and you may not use the same element twice.

You can return the answer in any order.`,
  examples: [
    {
      input: "nums = [2,7,11,15], target = 9",
      output: "[0,1]",
      explanation: "Because nums[0] + nums[1] == 9, we return [0, 1].",
    },
    {
      input: "nums = [3,2,4], target = 6",
      output: "[1,2]",
    },
    {
      input: "nums = [3,3], target = 6",
      output: "[0,1]",
    },
  ],
  constraints: [
    "2 <= nums.length <= 10^4",
    "-10^9 <= nums[i] <= 10^9",
    "-10^9 <= target <= 10^9",
    "Only one valid answer exists.",
  ],
}

const initialCode = `function twoSum(nums, target) {
  // Your solution here
  
}`

const initialMessages: TranscriptMessage[] = []

export default function TechnicalInterviewPage() {
  const [isInterviewActive, setIsInterviewActive] = useState(false)
  const [code, setCode] = useState(initialCode)
  const [notes, setNotes] = useState("")
  const [messages, setMessages] = useState<TranscriptMessage[]>(initialMessages)

  const startInterview = useCallback(() => {
    setIsInterviewActive(true)
    setMessages([
      {
        id: "1",
        role: "interviewer",
        content: "Hello! Welcome to your technical interview. Today we will be working on the Two Sum problem. Please take a moment to read the problem description and let me know when you are ready to discuss your approach.",
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
        content: "Thank you for completing this interview session. Great job working through the problem!",
        timestamp: new Date(),
      },
    ])
  }, [])

  const resetInterview = useCallback(() => {
    setIsInterviewActive(false)
    setCode(initialCode)
    setNotes("")
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

    // Simulate interviewer response
    if (message.role === "user") {
      setTimeout(() => {
        setMessages((prev) => [
          ...prev,
          {
            id: (Date.now() + 1).toString(),
            role: "interviewer",
            content: "That sounds like a good approach. Can you walk me through the time complexity of your solution?",
            timestamp: new Date(),
          },
        ])
      }, 2000)
    }
  }, [])

  return (
    <MainLayout>
      <div className="h-[calc(100vh-8rem)] flex flex-col gap-4">
        {/* Header Controls */}
        <div className="flex items-center justify-between">
          <h1 className="text-xl font-semibold text-foreground">Technical Interview</h1>
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

        {/* Main Content - 30:70 split */}
        <div className="flex-1 flex gap-4 overflow-hidden">
          {/* Left Panel - Problem + Voice + Transcript (30%) */}
          <div className="w-[30%] flex flex-col gap-4 overflow-hidden">
            <ProblemPanel problem={sampleProblem} className="flex-1 min-h-0" />
            <VoiceAgent isActive={isInterviewActive} onTranscript={handleTranscript} />
            <Transcript messages={messages} className="h-48" />
          </div>

          {/* Right Panel - Code Editor + Notes (70%) */}
          <div className="w-[70%] flex flex-col gap-4 overflow-hidden">
            <CodeEditor
              value={code}
              onChange={setCode}
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
