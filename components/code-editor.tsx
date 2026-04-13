"use client"

import { useState, useCallback, useRef, useEffect } from "react"
import { cn } from "@/lib/utils"

interface CodeEditorProps {
  value: string
  onChange: (value: string) => void
  language?: string
  className?: string
}

const keywords = [
  "function", "const", "let", "var", "return", "if", "else", "for", "while",
  "class", "extends", "import", "export", "from", "default", "async", "await",
  "try", "catch", "throw", "new", "this", "typeof", "instanceof", "true", "false",
  "null", "undefined", "break", "continue", "switch", "case", "do", "in", "of",
  "def", "print", "self", "None", "True", "False", "and", "or", "not", "elif",
  "lambda", "with", "as", "pass", "raise", "except", "finally", "yield", "global",
  "public", "private", "protected", "static", "void", "int", "string", "boolean",
  "interface", "type", "enum", "implements", "abstract", "final"
]

const builtins = [
  "console", "Math", "Array", "Object", "String", "Number", "Boolean", "Date",
  "JSON", "Promise", "Map", "Set", "RegExp", "Error", "setTimeout", "setInterval",
  "parseInt", "parseFloat", "isNaN", "isFinite", "len", "range", "str", "list",
  "dict", "tuple", "set", "int", "float", "bool", "input", "open", "enumerate"
]

function highlightCode(code: string): string {
  const lines = code.split("\n")
  
  return lines.map(line => {
    let highlighted = line
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
    
    // Comments
    highlighted = highlighted.replace(
      /(\/\/.*$|#.*$)/gm,
      '<span class="text-muted-foreground/60">$1</span>'
    )
    
    // Strings
    highlighted = highlighted.replace(
      /("(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*'|`(?:[^`\\]|\\.)*`)/g,
      '<span class="text-emerald-400">$1</span>'
    )
    
    // Numbers
    highlighted = highlighted.replace(
      /\b(\d+\.?\d*)\b/g,
      '<span class="text-amber-400">$1</span>'
    )
    
    // Keywords
    keywords.forEach(keyword => {
      const regex = new RegExp(`\\b(${keyword})\\b`, "g")
      highlighted = highlighted.replace(
        regex,
        '<span class="text-rose-400 font-medium">$1</span>'
      )
    })
    
    // Built-ins
    builtins.forEach(builtin => {
      const regex = new RegExp(`\\b(${builtin})\\b`, "g")
      highlighted = highlighted.replace(
        regex,
        '<span class="text-cyan-400">$1</span>'
      )
    })
    
    // Function calls
    highlighted = highlighted.replace(
      /\b([a-zA-Z_][a-zA-Z0-9_]*)\s*\(/g,
      '<span class="text-violet-400">$1</span>('
    )
    
    return highlighted
  }).join("\n")
}

export function CodeEditor({ value, onChange, language = "javascript", className }: CodeEditorProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const preRef = useRef<HTMLPreElement>(null)
  const [lineCount, setLineCount] = useState(1)

  useEffect(() => {
    const lines = value.split("\n").length
    setLineCount(Math.max(lines, 20))
  }, [value])

  const handleScroll = useCallback(() => {
    if (textareaRef.current && preRef.current) {
      preRef.current.scrollTop = textareaRef.current.scrollTop
      preRef.current.scrollLeft = textareaRef.current.scrollLeft
    }
  }, [])

  const handleKeyDown = useCallback((e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Tab") {
      e.preventDefault()
      const start = e.currentTarget.selectionStart
      const end = e.currentTarget.selectionEnd
      const newValue = value.substring(0, start) + "  " + value.substring(end)
      onChange(newValue)
      requestAnimationFrame(() => {
        if (textareaRef.current) {
          textareaRef.current.selectionStart = textareaRef.current.selectionEnd = start + 2
        }
      })
    }
  }, [value, onChange])

  return (
    <div className={cn("relative flex h-full bg-card rounded-lg border border-border overflow-hidden", className)}>
      {/* Line numbers */}
      <div className="flex flex-col bg-secondary/50 text-muted-foreground text-right py-4 px-3 font-mono text-sm select-none border-r border-border">
        {Array.from({ length: lineCount }, (_, i) => (
          <div key={i + 1} className="leading-6 h-6">
            {i + 1}
          </div>
        ))}
      </div>
      
      {/* Editor area */}
      <div className="relative flex-1 overflow-hidden">
        {/* Syntax highlighted background */}
        <pre
          ref={preRef}
          className="absolute inset-0 p-4 font-mono text-sm leading-6 text-foreground whitespace-pre overflow-auto pointer-events-none"
          dangerouslySetInnerHTML={{ __html: highlightCode(value) + "\n" }}
          aria-hidden="true"
        />
        
        {/* Actual textarea */}
        <textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onScroll={handleScroll}
          onKeyDown={handleKeyDown}
          spellCheck={false}
          className="absolute inset-0 w-full h-full p-4 font-mono text-sm leading-6 bg-transparent text-transparent caret-foreground resize-none outline-none"
          placeholder="// Start coding here..."
        />
      </div>
      
      {/* Language indicator */}
      <div className="absolute bottom-3 right-3 px-2 py-1 bg-secondary rounded text-xs text-muted-foreground font-mono">
        {language}
      </div>
    </div>
  )
}
