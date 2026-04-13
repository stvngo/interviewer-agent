"use client"

import { useState, useCallback, useRef, useEffect, useMemo } from "react"
import { cn } from "@/lib/utils"

interface CodeEditorProps {
  value: string
  onChange: (value: string) => void
  language?: string
  className?: string
}

const keywords = new Set([
  "function", "const", "let", "var", "return", "if", "else", "for", "while",
  "class", "extends", "import", "export", "from", "default", "async", "await",
  "try", "catch", "throw", "new", "this", "typeof", "instanceof", "true", "false",
  "null", "undefined", "break", "continue", "switch", "case", "do", "in", "of",
  "def", "print", "self", "None", "True", "False", "and", "or", "not", "elif",
  "lambda", "with", "as", "pass", "raise", "except", "finally", "yield", "global",
  "public", "private", "protected", "static", "void", "int", "string", "boolean",
  "interface", "type", "enum", "implements", "abstract", "final"
])

const builtins = new Set([
  "console", "Math", "Array", "Object", "String", "Number", "Boolean", "Date",
  "JSON", "Promise", "Map", "Set", "RegExp", "Error", "setTimeout", "setInterval",
  "parseInt", "parseFloat", "isNaN", "isFinite", "len", "range", "str", "list",
  "dict", "tuple", "set", "int", "float", "bool", "input", "open", "enumerate"
])

interface Token {
  type: "keyword" | "builtin" | "function" | "string" | "number" | "comment" | "punctuation" | "text"
  value: string
}

function tokenizeLine(line: string): Token[] {
  const tokens: Token[] = []
  let i = 0
  
  while (i < line.length) {
    // Check for comments
    if (line.slice(i, i + 2) === "//" || line[i] === "#") {
      tokens.push({ type: "comment", value: line.slice(i) })
      break
    }
    
    // Check for strings
    if (line[i] === '"' || line[i] === "'" || line[i] === "`") {
      const quote = line[i]
      let j = i + 1
      while (j < line.length && (line[j] !== quote || line[j - 1] === "\\")) {
        j++
      }
      tokens.push({ type: "string", value: line.slice(i, j + 1) })
      i = j + 1
      continue
    }
    
    // Check for numbers
    if (/\d/.test(line[i])) {
      let j = i
      while (j < line.length && /[\d.]/.test(line[j])) {
        j++
      }
      tokens.push({ type: "number", value: line.slice(i, j) })
      i = j
      continue
    }
    
    // Check for identifiers (words)
    if (/[a-zA-Z_]/.test(line[i])) {
      let j = i
      while (j < line.length && /[a-zA-Z0-9_]/.test(line[j])) {
        j++
      }
      const word = line.slice(i, j)
      
      // Check if it's a function call
      let k = j
      while (k < line.length && line[k] === " ") k++
      
      if (line[k] === "(") {
        tokens.push({ type: "function", value: word })
      } else if (keywords.has(word)) {
        tokens.push({ type: "keyword", value: word })
      } else if (builtins.has(word)) {
        tokens.push({ type: "builtin", value: word })
      } else {
        tokens.push({ type: "text", value: word })
      }
      i = j
      continue
    }
    
    // Punctuation and operators
    if (/[{}()\[\];,.:=<>+\-*/%&|!?]/.test(line[i])) {
      tokens.push({ type: "punctuation", value: line[i] })
      i++
      continue
    }
    
    // Whitespace and other characters
    tokens.push({ type: "text", value: line[i] })
    i++
  }
  
  return tokens
}

function HighlightedLine({ line, lineIndex }: { line: string; lineIndex: number }) {
  const tokens = useMemo(() => tokenizeLine(line), [line])
  
  return (
    <div className="leading-6 h-6 whitespace-pre">
      {tokens.map((token, i) => {
        const key = `${lineIndex}-${i}`
        switch (token.type) {
          case "keyword":
            return <span key={key} className="text-rose-400 font-medium">{token.value}</span>
          case "builtin":
            return <span key={key} className="text-cyan-400">{token.value}</span>
          case "function":
            return <span key={key} className="text-violet-400">{token.value}</span>
          case "string":
            return <span key={key} className="text-emerald-400">{token.value}</span>
          case "number":
            return <span key={key} className="text-amber-400">{token.value}</span>
          case "comment":
            return <span key={key} className="text-neutral-500">{token.value}</span>
          case "punctuation":
            return <span key={key} className="text-neutral-400">{token.value}</span>
          default:
            return <span key={key}>{token.value}</span>
        }
      })}
      {line === "" && "\u200B"}
    </div>
  )
}

const MIN_LINES = 20

export function CodeEditor({ value, onChange, language = "javascript", className }: CodeEditorProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const highlightRef = useRef<HTMLDivElement>(null)
  const [lineCount, setLineCount] = useState(MIN_LINES)

  const lines = useMemo(() => value.split("\n"), [value])

  useEffect(() => {
    setLineCount(Math.max(lines.length, MIN_LINES))
  }, [lines.length])

  const handleScroll = useCallback(() => {
    if (textareaRef.current && highlightRef.current) {
      highlightRef.current.scrollTop = textareaRef.current.scrollTop
      highlightRef.current.scrollLeft = textareaRef.current.scrollLeft
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

  // Pad lines to minimum
  const displayLines = useMemo(() => {
    const padded = [...lines]
    while (padded.length < MIN_LINES) {
      padded.push("")
    }
    return padded
  }, [lines])

  return (
    <div className={cn("relative flex h-full bg-card rounded-lg border border-border overflow-hidden", className)}>
      {/* Line numbers */}
      <div className="flex flex-col bg-secondary/50 text-muted-foreground text-right py-4 px-3 font-mono text-sm select-none border-r border-border overflow-hidden">
        {Array.from({ length: lineCount }, (_, i) => (
          <div key={i + 1} className="leading-6 h-6">
            {i + 1}
          </div>
        ))}
      </div>
      
      {/* Editor area */}
      <div className="relative flex-1 overflow-hidden">
        {/* Syntax highlighted layer */}
        <div
          ref={highlightRef}
          className="absolute inset-0 p-4 font-mono text-sm text-foreground overflow-auto pointer-events-none"
          aria-hidden="true"
        >
          {displayLines.map((line, i) => (
            <HighlightedLine key={i} line={line} lineIndex={i} />
          ))}
        </div>
        
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
