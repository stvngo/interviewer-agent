"use client"

import { useState, useEffect } from "react"
import { MainLayout } from "@/components/main-layout"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Plus, Code, MessageSquare, Clock, Calendar, ArrowRight, Trash2 } from "lucide-react"
import Link from "next/link"
import { listSessions, type Session } from "@/lib/api"

interface Interview {
  id: string
  type: "technical" | "behavioral"
  title: string
  date: Date
  duration: number
  status: string
}

function sessionToInterview(s: Session): Interview {
  return {
    id: s.session_id,
    type: s.round_type === "behavioral" ? "behavioral" : "technical",
    title: s.title || `${s.round_type.charAt(0).toUpperCase() + s.round_type.slice(1)} Session`,
    date: new Date(s.created_at),
    duration: s.duration_minutes ?? 0,
    status: s.status,
  }
}

export default function HomePage() {
  const [interviews, setInterviews] = useState<Interview[]>([])
  const [loaded, setLoaded] = useState(false)

  useEffect(() => {
    listSessions()
      .then((res) => {
        setInterviews(res.sessions.map(sessionToInterview))
      })
      .catch(() => {
        // backend may not be running yet -- show empty state
      })
      .finally(() => setLoaded(true))
  }, [])

  const deleteInterview = (id: string) => {
    setInterviews(interviews.filter((i) => i.id !== id))
  }

  const completedCount = interviews.filter((i) => i.status === "completed").length
  const activeCount = interviews.filter((i) => i.status === "active" || i.status === "created").length

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
              <CardDescription>Active</CardDescription>
              <CardTitle className="text-3xl font-semibold">{activeCount}</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-xs text-muted-foreground">In-progress sessions</p>
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
              {!loaded ? (
                <div className="p-8 text-center">
                  <p className="text-muted-foreground">Loading sessions...</p>
                </div>
              ) : interviews.length === 0 ? (
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
                            {interview.duration > 0 && (
                              <span className="text-xs text-muted-foreground flex items-center gap-1">
                                <Clock className="h-3 w-3" />
                                {interview.duration} min
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                      
                      <div className="flex items-center gap-3">
                        <span
                          className={`text-xs px-2 py-1 rounded-full ${
                            interview.status === "completed"
                              ? "bg-emerald-500/20 text-emerald-400"
                              : interview.status === "active"
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
