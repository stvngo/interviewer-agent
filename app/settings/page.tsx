"use client"

import { useState, useCallback } from "react"
import { MainLayout } from "@/components/main-layout"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Upload, FileText, X, Check } from "lucide-react"
import { cn } from "@/lib/utils"

type Difficulty = "intern" | "junior" | "mid" | "senior" | "staff"
type InterviewType = "technical" | "behavioral" | "system-design"

interface Settings {
  difficulty: Difficulty
  interviewTypes: InterviewType[]
  voiceEnabled: boolean
  autoSave: boolean
}

export default function SettingsPage() {
  const [settings, setSettings] = useState<Settings>({
    difficulty: "mid",
    interviewTypes: ["technical", "behavioral"],
    voiceEnabled: true,
    autoSave: true,
  })
  const [resumeFile, setResumeFile] = useState<File | null>(null)
  const [isDragging, setIsDragging] = useState(false)
  const [saved, setSaved] = useState(false)

  const difficulties: { value: Difficulty; label: string; description: string }[] = [
    { value: "intern", label: "Intern", description: "Entry-level questions" },
    { value: "junior", label: "Junior", description: "1-2 years experience" },
    { value: "mid", label: "Mid-Level", description: "3-5 years experience" },
    { value: "senior", label: "Senior", description: "5+ years experience" },
    { value: "staff", label: "Staff+", description: "Leadership & architecture" },
  ]

  const interviewTypes: { value: InterviewType; label: string }[] = [
    { value: "technical", label: "Technical Coding" },
    { value: "behavioral", label: "Behavioral" },
    { value: "system-design", label: "System Design" },
  ]

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    const file = e.dataTransfer.files[0]
    if (file && (file.type === "application/pdf" || file.name.endsWith(".pdf"))) {
      setResumeFile(file)
    }
  }, [])

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      setResumeFile(file)
    }
  }, [])

  const removeResume = useCallback(() => {
    setResumeFile(null)
  }, [])

  const toggleInterviewType = useCallback((type: InterviewType) => {
    setSettings((prev) => ({
      ...prev,
      interviewTypes: prev.interviewTypes.includes(type)
        ? prev.interviewTypes.filter((t) => t !== type)
        : [...prev.interviewTypes, type],
    }))
  }, [])

  const handleSave = useCallback(() => {
    // Simulate saving
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }, [])

  return (
    <MainLayout>
      <div className="max-w-3xl mx-auto space-y-8">
        <div>
          <h1 className="text-2xl font-semibold text-foreground tracking-tight">Settings</h1>
          <p className="text-muted-foreground mt-1">
            Customize your interview experience
          </p>
        </div>

        {/* Difficulty Selection */}
        <Card>
          <CardHeader>
            <CardTitle>Experience Level</CardTitle>
            <CardDescription>
              Select your target role level to adjust question difficulty
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
              {difficulties.map((diff) => (
                <button
                  key={diff.value}
                  onClick={() => setSettings((prev) => ({ ...prev, difficulty: diff.value }))}
                  className={cn(
                    "flex flex-col items-center p-4 rounded-lg border transition-colors",
                    settings.difficulty === diff.value
                      ? "border-primary bg-primary/10"
                      : "border-border hover:border-foreground/30"
                  )}
                >
                  <span className="font-medium text-foreground text-sm">{diff.label}</span>
                  <span className="text-xs text-muted-foreground mt-1">{diff.description}</span>
                </button>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Interview Types */}
        <Card>
          <CardHeader>
            <CardTitle>Interview Types</CardTitle>
            <CardDescription>
              Choose which types of interviews you want to practice
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-3">
              {interviewTypes.map((type) => (
                <button
                  key={type.value}
                  onClick={() => toggleInterviewType(type.value)}
                  className={cn(
                    "flex items-center gap-2 px-4 py-2 rounded-lg border transition-colors",
                    settings.interviewTypes.includes(type.value)
                      ? "border-primary bg-primary/10"
                      : "border-border hover:border-foreground/30"
                  )}
                >
                  {settings.interviewTypes.includes(type.value) && (
                    <Check className="h-4 w-4 text-primary" />
                  )}
                  <span className="text-sm font-medium text-foreground">{type.label}</span>
                </button>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Resume Upload */}
        <Card>
          <CardHeader>
            <CardTitle>Resume</CardTitle>
            <CardDescription>
              Upload your resume for personalized interview questions
            </CardDescription>
          </CardHeader>
          <CardContent>
            {resumeFile ? (
              <div className="flex items-center justify-between p-4 bg-secondary rounded-lg">
                <div className="flex items-center gap-3">
                  <FileText className="h-8 w-8 text-foreground" />
                  <div>
                    <p className="font-medium text-foreground">{resumeFile.name}</p>
                    <p className="text-sm text-muted-foreground">
                      {(resumeFile.size / 1024).toFixed(1)} KB
                    </p>
                  </div>
                </div>
                <Button variant="ghost" size="icon" onClick={removeResume}>
                  <X className="h-4 w-4" />
                </Button>
              </div>
            ) : (
              <div
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                className={cn(
                  "border-2 border-dashed rounded-lg p-8 text-center transition-colors",
                  isDragging
                    ? "border-primary bg-primary/5"
                    : "border-border hover:border-foreground/30"
                )}
              >
                <Upload className="h-8 w-8 text-muted-foreground mx-auto mb-4" />
                <p className="text-foreground font-medium mb-1">
                  Drag and drop your resume here
                </p>
                <p className="text-sm text-muted-foreground mb-4">or</p>
                <label>
                  <input
                    type="file"
                    accept=".pdf"
                    onChange={handleFileSelect}
                    className="hidden"
                  />
                  <Button variant="outline" asChild>
                    <span className="cursor-pointer">Browse Files</span>
                  </Button>
                </label>
                <p className="text-xs text-muted-foreground mt-4">
                  Supported format: PDF
                </p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Preferences */}
        <Card>
          <CardHeader>
            <CardTitle>Preferences</CardTitle>
            <CardDescription>
              Additional settings for your interview sessions
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium text-foreground">Voice Agent</p>
                <p className="text-sm text-muted-foreground">
                  Enable voice interaction with the AI interviewer
                </p>
              </div>
              <button
                onClick={() =>
                  setSettings((prev) => ({ ...prev, voiceEnabled: !prev.voiceEnabled }))
                }
                className={cn(
                  "w-12 h-6 rounded-full transition-colors relative",
                  settings.voiceEnabled ? "bg-primary" : "bg-secondary"
                )}
              >
                <div
                  className={cn(
                    "absolute top-1 w-4 h-4 rounded-full bg-foreground transition-transform",
                    settings.voiceEnabled ? "translate-x-7" : "translate-x-1"
                  )}
                />
              </button>
            </div>
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium text-foreground">Auto-save</p>
                <p className="text-sm text-muted-foreground">
                  Automatically save your code and notes
                </p>
              </div>
              <button
                onClick={() => setSettings((prev) => ({ ...prev, autoSave: !prev.autoSave }))}
                className={cn(
                  "w-12 h-6 rounded-full transition-colors relative",
                  settings.autoSave ? "bg-primary" : "bg-secondary"
                )}
              >
                <div
                  className={cn(
                    "absolute top-1 w-4 h-4 rounded-full bg-foreground transition-transform",
                    settings.autoSave ? "translate-x-7" : "translate-x-1"
                  )}
                />
              </button>
            </div>
          </CardContent>
        </Card>

        {/* Save Button */}
        <div className="flex justify-end">
          <Button onClick={handleSave} className="gap-2">
            {saved ? (
              <>
                <Check className="h-4 w-4" />
                Saved
              </>
            ) : (
              "Save Settings"
            )}
          </Button>
        </div>
      </div>
    </MainLayout>
  )
}
