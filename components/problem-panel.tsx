"use client"

import { cn } from "@/lib/utils"

interface Example {
  input: string
  output: string
  explanation?: string
}

interface Problem {
  title: string
  difficulty: string
  description: string
  examples: Example[]
  constraints: string[]
}

interface ProblemPanelProps {
  problem: Problem
  className?: string
}

export function ProblemPanel({ problem, className }: ProblemPanelProps) {
  const difficultyColor: Record<string, string> = {
    Easy: "text-emerald-400 bg-emerald-500/20",
    Medium: "text-amber-400 bg-amber-500/20",
    Hard: "text-rose-400 bg-rose-500/20",
  }

  return (
    <div className={cn("flex flex-col bg-card rounded-lg border border-border overflow-hidden", className)}>
      <div className="px-4 py-3 border-b border-border">
        <div className="flex items-center justify-between">
          <h2 className="font-medium text-foreground">{problem.title}</h2>
          <span className={cn("text-xs px-2 py-1 rounded-full", difficultyColor[problem.difficulty])}>
            {problem.difficulty}
          </span>
        </div>
      </div>

      <div className="flex-1 overflow-auto p-4 space-y-6">
        {/* Description */}
        <div>
          <p className="text-sm text-foreground/90 leading-relaxed whitespace-pre-wrap">
            {problem.description}
          </p>
        </div>

        {/* Examples */}
        <div className="space-y-4">
          <h3 className="text-sm font-medium text-foreground">Examples</h3>
          {problem.examples.map((example, index) => (
            <div key={index} className="bg-secondary/50 rounded-lg p-3 space-y-2">
              <div>
                <span className="text-xs text-muted-foreground">Input:</span>
                <code className="block text-sm font-mono text-foreground mt-1">
                  {example.input}
                </code>
              </div>
              <div>
                <span className="text-xs text-muted-foreground">Output:</span>
                <code className="block text-sm font-mono text-foreground mt-1">
                  {example.output}
                </code>
              </div>
              {example.explanation && (
                <div>
                  <span className="text-xs text-muted-foreground">Explanation:</span>
                  <p className="text-sm text-foreground/80 mt-1">{example.explanation}</p>
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Constraints */}
        <div className="space-y-2">
          <h3 className="text-sm font-medium text-foreground">Constraints</h3>
          <ul className="space-y-1">
            {problem.constraints.map((constraint, index) => (
              <li key={index} className="text-sm text-muted-foreground font-mono">
                {constraint}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  )
}

export type { Problem }
