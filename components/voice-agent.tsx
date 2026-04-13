"use client"

import { useState, useEffect } from "react"
import { Mic, MicOff, Volume2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

interface VoiceAgentProps {
  isActive: boolean
  onTranscript?: (message: { role: "interviewer" | "user"; content: string }) => void
}

export function VoiceAgent({ isActive, onTranscript }: VoiceAgentProps) {
  const [isMuted, setIsMuted] = useState(false)
  const [isListening, setIsListening] = useState(false)
  const [audioLevel, setAudioLevel] = useState(0)

  useEffect(() => {
    if (!isActive) {
      setIsListening(false)
      setAudioLevel(0)
      return
    }

    // Simulate audio activity when active
    const interval = setInterval(() => {
      if (isActive && !isMuted) {
        setAudioLevel(Math.random() * 100)
      } else {
        setAudioLevel(0)
      }
    }, 100)

    return () => clearInterval(interval)
  }, [isActive, isMuted])

  const toggleMute = () => {
    setIsMuted(!isMuted)
  }

  const toggleListening = () => {
    setIsListening(!isListening)
    if (!isListening && onTranscript) {
      // Simulate user speaking
      setTimeout(() => {
        onTranscript({
          role: "user",
          content: "I think I would approach this problem by first..."
        })
      }, 2000)
    }
  }

  return (
    <div className="bg-card rounded-lg border border-border p-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-medium text-foreground">Voice Agent</h3>
        <div className={cn(
          "w-2 h-2 rounded-full",
          isActive ? "bg-emerald-500 animate-pulse" : "bg-muted-foreground"
        )} />
      </div>

      {/* Audio Visualization */}
      <div className="flex items-center justify-center gap-1 h-16 mb-4">
        {Array.from({ length: 12 }, (_, i) => (
          <div
            key={i}
            className="w-1.5 bg-foreground/30 rounded-full transition-all duration-75"
            style={{
              height: isActive && !isMuted 
                ? `${Math.max(8, Math.random() * audioLevel * 0.6)}px`
                : "8px"
            }}
          />
        ))}
      </div>

      {/* Controls */}
      <div className="flex items-center justify-center gap-3">
        <Button
          variant="outline"
          size="icon"
          onClick={toggleMute}
          disabled={!isActive}
          className={cn(
            "h-10 w-10",
            isMuted && "bg-destructive/20 border-destructive text-destructive"
          )}
        >
          {isMuted ? <Volume2 className="h-4 w-4" /> : <Volume2 className="h-4 w-4" />}
        </Button>
        
        <Button
          variant={isListening ? "default" : "outline"}
          size="icon"
          onClick={toggleListening}
          disabled={!isActive}
          className={cn(
            "h-12 w-12 rounded-full",
            isListening && "bg-primary animate-pulse"
          )}
        >
          {isListening ? (
            <Mic className="h-5 w-5" />
          ) : (
            <MicOff className="h-5 w-5" />
          )}
        </Button>
      </div>

      {isActive && (
        <p className="text-xs text-muted-foreground text-center mt-3">
          {isListening ? "Listening..." : "Click microphone to speak"}
        </p>
      )}
    </div>
  )
}
