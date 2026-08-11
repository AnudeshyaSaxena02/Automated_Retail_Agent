"use client";

// ============================================================
// stores/uiStore.ts
//
// Zustand store for global UI preferences.
//
// Phase 2 scope — exactly three members:
//   sidebarCollapsed   boolean   — desktop sidebar collapsed state
//   toggleSidebar      ()=>void  — flip collapsed
//   setSidebarCollapsed (v)=>void — set explicitly
//
// Persisted to localStorage ("idam-ui") so the sidebar
// preference survives page reloads.
//
// Explicitly excluded:
//   - theme state  (owned by next-themes)
//   - navigation history
//   - customer context
//   - session/auth state
// ============================================================

import { create } from "zustand";
import { persist } from "zustand/middleware";

interface UIStore {
  sidebarCollapsed: boolean;
  toggleSidebar: () => void;
  setSidebarCollapsed: (value: boolean) => void;
}

export const useUIStore = create<UIStore>()(
  persist(
    (set) => ({
      sidebarCollapsed: false,

      toggleSidebar: () =>
        set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),

      setSidebarCollapsed: (value: boolean) =>
        set({ sidebarCollapsed: value }),
    }),
    {
      name: "idam-ui",
      // Only persist the boolean value, not the action functions
      partialize: (state) => ({ sidebarCollapsed: state.sidebarCollapsed }),
    }
  )
);
