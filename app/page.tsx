"use client"

import { useState } from "react"
import { MainLayout } from "@/components/main-layout"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Plus, Code, MessageSquare, Clock, Calendar, ArrowRight, Trash2 } from "lucide-react"
import Link from "next/link"

interface Interview {
  id: string
  type: "technical" | "behavioral"
  title: string
  date: Date
  duration: number
  status: "completed" | "in-progress" | "scheduled"
}

const mockInterviews: Interview[] = [
  {
    id: "1",
    type: "technical",
    title: "Two Sum Problem",
    date: new Date(2026, 3, 10, 14, 0),
    duration: 45,
    status: "completed",
  },
  {
    id: "2",
    type: "behavioral",
    title: "Leadership Experience",
    date: new Date(2026, 3, 11, 10, 30),
    duration: 30,
    status: "completed",
  },
  {
    id: "3",
    type: "technical",
    title: "Binary Search Tree",
    date: new Date(2026, 3, 12, 15, 0),
    duration: 45,
    status: "scheduled",
  },
]

export default function HomePage() {
  const [interviews, setInterviews] = useState<Interview[]>(mockInterviews)

  const deleteInterview = (id: string) => {
    setInterviews(interviews.filter((i) => i.id !== id))
  }

  const completedCount = interviews.filter((i) => i.status === "completed").length
  const scheduledCount = interviews.filter((i) => i.status === "scheduled").length

  return (
    <MainLayout>
      <div className="max-w-6xl mx-auto space-y-8">
        {/* Page Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-foreground tracking-tight">
              Welcome back
            </h1>
            <p className="text-muted-foreground mt-1">
              Manage your interview practice sessions
            </p>
          </div>
          
          <div className="flex items-center gap-3">
            <Link href="/technical">
              <Button variant="outline" className="gap-2">
                <Code className="h-4 w-4" />
                New Technical
              </Button>
            </Link>
            <Link href="/behavioral">
              <Button className="gap-2">
                <Plus className="h-4 w-4" />
                New Behavioral
              </Button>
            </Link>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card>
            <CardHeader className="pb-2">
              <CardDescription>Total Sessions</CardDescription>
              <CardTitle className="text-3xl font-semibold">{interviews.length}</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-xs text-muted-foreground">All-time practice sessions</p>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="pb-2">
              <CardDescription>Completed</CardDescription>
              <CardTitle className="text-3xl font-semibold">{completedCount}</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-xs text-muted-foreground">Sessions finished</p>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="pb-2">
              <CardDescription>Scheduled</CardDescription>
              <CardTitle className="text-3xl font-semibold">{scheduledCount}</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-xs text-muted-foreground">Upcoming sessions</p>
            </CardContent>
          </Card>
        </div>

        {/* Quick Start */}
        <div>
          <h2 className="text-lg font-medium text-foreground mb-4">Quick Start</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Link href="/technical">
              <Card className="group cursor-pointer hover:border-foreground/30 transition-colors">
                <CardContent className="flex items-center gap-4 p-6">
                  <div className="p-3 bg-secondary rounded-lg">
                    <Code className="h-6 w-6 text-foreground" />
                  </div>
                  <div className="flex-1">
                    <h3 className="font-medium text-foreground">Technical Interview</h3>
                    <p className="text-sm text-muted-foreground">Practice coding problems with AI</p>
                  </div>
                  <ArrowRight className="h-5 w-5 text-muted-foreground group-hover:text-foreground transition-colors" />
                </CardContent>
              </Card>
            </Link>
            
            <Link href="/behavioral">
              <Card className="group cursor-pointer hover:border-foreground/30 transition-colors">
                <CardContent className="flex items-center gap-4 p-6">
                  <div className="p-3 bg-secondary rounded-lg">
                    <MessageSquare className="h-6 w-6 text-foreground" />
                  </div>
                  <div className="flex-1">
                    <h3 className="font-medium text-foreground">Behavioral Interview</h3>
                    <p className="text-sm text-muted-foreground">Practice soft skills and STAR method</p>
                  </div>
                  <ArrowRight className="h-5 w-5 text-muted-foreground group-hover:text-foreground transition-colors" />
                </CardContent>
              </Card>
            </Link>
          </div>
        </div>

        {/* Recent Sessions */}
        <div>
          <h2 className="text-lg font-medium text-foreground mb-4">Recent Sessions</h2>
          <Card>
            <CardContent className="p-0">
              {interviews.length === 0 ? (
                <div className="p-8 text-center">
                  <p className="text-muted-foreground">No interviews yet. Start your first session!</p>
                </div>
              ) : (
                <div className="divide-y divide-border">
                  {interviews.map((interview) => (
                    <div
                      key={interview.id}
                      className="flex items-center justify-between p-4 hover:bg-secondary/30 transition-colors"
                    >
                      <div className="flex items-center gap-4">
                        <div className="p-2 bg-secondary rounded-lg">
                          {interview.type === "technical" ? (
                            <Code className="h-4 w-4 text-foreground" />
                          ) : (
                            <MessageSquare className="h-4 w-4 text-foreground" />
                          )}
                        </div>
                        <div>
                          <h3 className="font-medium text-foreground">{interview.title}</h3>
                          <div className="flex items-center gap-3 mt-1">
                            <span className="text-xs text-muted-foreground flex items-center gap-1">
                              <Calendar className="h-3 w-3" />
                              {interview.date.toLocaleDateString()}
                            </span>
                            <span className="text-xs text-muted-foreground flex items-center gap-1">
                              <Clock className="h-3 w-3" />
                              {interview.duration} min
                            </span>
                          </div>
                        </div>
                      </div>
                      
                      <div className="flex items-center gap-3">
                        <span
                          className={`text-xs px-2 py-1 rounded-full ${
                            interview.status === "completed"
                              ? "bg-emerald-500/20 text-emerald-400"
                              : interview.status === "in-progress"
                              ? "bg-amber-500/20 text-amber-400"
                              : "bg-secondary text-muted-foreground"
                          }`}
                        >
                          {interview.status}
                        </span>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => deleteInterview(interview.id)}
                          className="text-muted-foreground hover:text-destructive"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </MainLayout>
  )
}
