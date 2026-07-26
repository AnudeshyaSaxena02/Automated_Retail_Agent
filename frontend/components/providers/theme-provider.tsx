"use client";

// ============================================================
// components/providers/theme-provider.tsx
//
// next-themes ThemeProvider wrapper.
//
// Wraps the application in next-themes' ThemeProvider so that
// any component tree below can call useTheme() to read and
// toggle the current theme.
//
// The `attribute="class"` setting means next-themes applies
// the "dark" class to <html>, which is what shadcn/ui expects.
// ============================================================

import { ThemeProvider as NextThemesProvider } from "next-themes";

interface ThemeProviderProps {
  children: React.ReactNode;
}

export function ThemeProvider({ children }: ThemeProviderProps) {
  return (
    <NextThemesProvider
      attribute="class"
      defaultTheme="system"
      enableSystem
      disableTransitionOnChange
    >
      {children}
    </NextThemesProvider>
  );
}
