"use client"

import { useRef, useEffect } from "react"
import { cn } from "@/lib/utils"
import { User, Bot } from "lucide-react"

export interface TranscriptMessage {
  id: string
  role: "interviewer" | "user"
  content: string
  timestamp: Date
}

interface TranscriptProps {
  messages: TranscriptMessage[]
  className?: string
}

export function Transcript({ messages, className }: TranscriptProps) {
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [messages])

  return (
    <div className={cn("flex flex-col bg-card rounded-lg border border-border overflow-hidden", className)}>
      <div className="px-4 py-3 border-b border-border">
        <h3 className="text-sm font-medium text-foreground">Transcript</h3>
      </div>
      
      <div ref={scrollRef} className="flex-1 overflow-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <p className="text-sm text-muted-foreground text-center py-8">
            Start the interview to see the transcript
          </p>
        ) : (
          messages.map((message) => (
            <div
              key={message.id}
              className={cn(
                "flex gap-3",
                message.role === "user" && "flex-row-reverse"
              )}
            >
              <div className={cn(
                "flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center",
                message.role === "interviewer" ? "bg-secondary" : "bg-primary"
              )}>
                {message.role === "interviewer" ? (
                  <Bot className="h-4 w-4 text-secondary-foreground" />
                ) : (
                  <User className="h-4 w-4 text-primary-foreground" />
                )}
              </div>
              
              <div className={cn(
                "flex-1 max-w-[80%]",
                message.role === "user" && "text-right"
              )}>
                <div className={cn(
                  "inline-block px-3 py-2 rounded-lg text-sm",
                  message.role === "interviewer"
                    ? "bg-secondary text-secondary-foreground"
                    : "bg-primary text-primary-foreground"
                )}>
                  {message.content}
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </p>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}
