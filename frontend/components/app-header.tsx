"use client"

import { Bell, User, Settings } from "lucide-react"
import { Button } from "@/components/ui/button"
import Link from "next/link"

export function AppHeader() {
  return (
    <header className="h-14 border-b border-border bg-card flex items-center justify-between px-6">
      <div className="flex items-center gap-2">
        <span className="text-xl font-semibold tracking-tight text-foreground">
          InterviewPro
        </span>
      </div>
      
      <div className="flex items-center gap-1">
        <Button variant="ghost" size="icon" className="text-muted-foreground hover:text-foreground">
          <Bell className="h-5 w-5" />
        </Button>
        <Button variant="ghost" size="icon" className="text-muted-foreground hover:text-foreground">
          <User className="h-5 w-5" />
        </Button>
        <Link href="/settings">
          <Button variant="ghost" size="icon" className="text-muted-foreground hover:text-foreground">
            <Settings className="h-5 w-5" />
          </Button>
        </Link>
      </div>
    </header>
  )
}
