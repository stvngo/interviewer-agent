"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { Home, Code, MessageSquare, Settings, HelpCircle, ChevronLeft, ChevronRight } from "lucide-react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"

interface AppSidebarProps {
  isCollapsed: boolean
  onToggle: () => void
}

const navItems = [
  { href: "/", label: "Home", icon: Home },
  { href: "/technical", label: "Technical", icon: Code },
  { href: "/behavioral", label: "Behavioral", icon: MessageSquare },
  { href: "/settings", label: "Settings", icon: Settings },
  { href: "/help", label: "Help", icon: HelpCircle },
]

export function AppSidebar({ isCollapsed, onToggle }: AppSidebarProps) {
  const pathname = usePathname()

  return (
    <aside
      className={cn(
        "flex flex-col h-full bg-sidebar border-r border-sidebar-border transition-all duration-300",
        isCollapsed ? "w-16" : "w-56"
      )}
    >
      <div className="flex items-center justify-between p-4 border-b border-sidebar-border">
        {!isCollapsed && (
          <span className="text-lg font-semibold text-sidebar-foreground tracking-tight">
            Menu
          </span>
        )}
        <Button
          variant="ghost"
          size="icon"
          onClick={onToggle}
          className={cn(
            "text-sidebar-foreground hover:bg-sidebar-accent",
            isCollapsed && "mx-auto"
          )}
        >
          {isCollapsed ? (
            <ChevronRight className="h-4 w-4" />
          ) : (
            <ChevronLeft className="h-4 w-4" />
          )}
        </Button>
      </div>

      <nav className="flex-1 p-2">
        <ul className="space-y-1">
          {navItems.map((item) => {
            const isActive = pathname === item.href
            return (
              <li key={item.href}>
                <Link
                  href={item.href}
                  className={cn(
                    "flex items-center gap-3 px-3 py-2.5 rounded-md text-sm font-medium transition-colors",
                    isActive
                      ? "bg-sidebar-accent text-sidebar-foreground"
                      : "text-sidebar-foreground/70 hover:bg-sidebar-accent hover:text-sidebar-foreground",
                    isCollapsed && "justify-center px-2"
                  )}
                >
                  <item.icon className="h-5 w-5 shrink-0" />
                  {!isCollapsed && <span>{item.label}</span>}
                </Link>
              </li>
            )
          })}
        </ul>
      </nav>
    </aside>
  )
}
