"use client";

// ============================================================
// components/layout/Header.tsx
//
// Top bar of the application shell.
//
// Contents:
//   Left  — hamburger menu button (mobile) + AppBreadcrumb
//   Right — backend health dot + ThemeToggle
//
// Backend health dot:
//   Green  — status === "healthy"
//   Amber  — status === "degraded"
//   Gray   — loading or network error (backend unreachable)
// ============================================================

import { Menu } from "lucide-react";
import { ThemeToggle } from "@/components/theme-toggle";
import { AppBreadcrumb } from "@/components/layout/Breadcrumb";
import { useHealth } from "@/hooks/useHealth";
import { cn } from "@/lib/utils";

interface HeaderProps {
  onMobileMenuOpen: () => void;
}

export function Header({ onMobileMenuOpen }: HeaderProps) {
  const { data: health, isLoading } = useHealth();

  const healthColor = isLoading
    ? "bg-muted-foreground/40"
    : health?.status === "healthy"
    ? "bg-green-500"
    : health?.status === "degraded"
    ? "bg-amber-500"
    : "bg-muted-foreground/40"; // error / unreachable

  const healthLabel = isLoading
    ? "Checking backend status..."
    : health?.status === "healthy"
    ? "Backend healthy"
    : health?.status === "degraded"
    ? "Backend degraded"
    : "Backend unreachable";

  return (
    <header
      role="banner"
      className="flex items-center justify-between h-14 px-4 border-b border-border bg-background shrink-0"
    >
      {/* Left section */}
      <div className="flex items-center gap-3">
        {/* Mobile menu button — hidden on desktop */}
        <button
          onClick={onMobileMenuOpen}
          className="md:hidden flex items-center justify-center rounded-md p-2 text-muted-foreground hover:bg-accent hover:text-accent-foreground transition-colors"
          aria-label="Open navigation menu"
        >
          <Menu className="h-5 w-5" aria-hidden="true" />
        </button>

        <AppBreadcrumb />
      </div>

      {/* Right section */}
      <div className="flex items-center gap-3">
        {/* Backend health indicator */}
        <div
          role="status"
          aria-label={healthLabel}
          title={healthLabel}
          className="flex items-center gap-1.5"
        >
          <span
            className={cn("h-2 w-2 rounded-full", healthColor)}
            aria-hidden="true"
          />
          <span className="text-xs text-muted-foreground hidden sm:inline">
            {isLoading
              ? "..."
              : health?.status === "healthy"
              ? "Operational"
              : health?.status === "degraded"
              ? "Degraded"
              : "Offline"}
          </span>
        </div>

        <ThemeToggle />
      </div>
    </header>
  );
}
