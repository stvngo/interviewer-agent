"use client"

import { useState } from "react"
import { ChevronDown, ChevronUp, StickyNote } from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

interface NotesPanelProps {
  value: string
  onChange: (value: string) => void
  className?: string
}

export function NotesPanel({ value, onChange, className }: NotesPanelProps) {
  const [isExpanded, setIsExpanded] = useState(true)

  return (
    <div className={cn("bg-card rounded-lg border border-border overflow-hidden", className)}>
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between px-4 py-3 border-b border-border hover:bg-secondary/50 transition-colors"
      >
        <div className="flex items-center gap-2">
          <StickyNote className="h-4 w-4 text-muted-foreground" />
          <span className="text-sm font-medium text-foreground">Notes</span>
        </div>
        {isExpanded ? (
          <ChevronUp className="h-4 w-4 text-muted-foreground" />
        ) : (
          <ChevronDown className="h-4 w-4 text-muted-foreground" />
        )}
      </button>
      
      {isExpanded && (
        <textarea
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder="Jot down your thoughts, pseudocode, or questions..."
          className="w-full h-32 p-4 bg-transparent text-sm text-foreground placeholder:text-muted-foreground resize-none outline-none"
        />
      )}
    </div>
  )
}
