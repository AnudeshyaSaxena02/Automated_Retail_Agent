"use client";

// ============================================================
// components/layout/AppLayout.tsx
//
// Root application shell: sidebar (desktop) + header + main content.
//
// Responsive behavior:
//   Desktop (≥768px): permanent sidebar, width transitions via CSS only
//   Mobile  (<768px):  sidebar hidden; hamburger opens Sheet drawer
//
// Zustand sidebarCollapsed controls the DESKTOP collapsed preference.
// Mobile Sheet open/close is transient local state — NOT persisted.
// No viewport state, no useMediaQuery, no additional persisted state.
// ============================================================

import { useState } from "react";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { Sidebar } from "@/components/layout/Sidebar";
import { Header } from "@/components/layout/Header";

interface AppLayoutProps {
  children: React.ReactNode;
}

export function AppLayout({ children }: AppLayoutProps) {
  // Transient mobile drawer state — not persisted, not Zustand
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      {/* Skip to main content — accessibility */}
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:fixed focus:top-2 focus:left-2 focus:z-50 focus:px-4 focus:py-2 focus:rounded-md focus:bg-primary focus:text-primary-foreground focus:text-sm focus:font-medium"
      >
        Skip to main content
      </a>

      {/* Desktop sidebar — hidden on mobile via md:flex */}
      <div className="hidden md:flex">
        <Sidebar />
      </div>

      {/* Mobile sidebar — Sheet drawer */}
      <Sheet open={mobileOpen} onOpenChange={setMobileOpen}>
        <SheetContent side="left" className="p-0 w-64">
          <SheetHeader className="sr-only">
            <SheetTitle>Navigation</SheetTitle>
          </SheetHeader>
          <Sidebar compact />
        </SheetContent>
      </Sheet>

      {/* Main area: header + scrollable content */}
      <div className="flex flex-col flex-1 overflow-hidden">
        <Header onMobileMenuOpen={() => setMobileOpen(true)} />

        <main
          id="main-content"
          className="flex-1 overflow-y-auto p-4 md:p-6"
          tabIndex={-1}
        >
          {children}
        </main>
      </div>
    </div>
  );
}
