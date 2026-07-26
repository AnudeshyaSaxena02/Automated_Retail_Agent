"use client";

// ============================================================
// components/providers/query-provider.tsx
//
// TanStack Query (React Query v5) client provider.
//
// Wraps the application in a QueryClientProvider so that any
// component tree below can use useQuery, useMutation, etc.
//
// The QueryClient is created once per browser session using
// useState to avoid recreating it on every render.
// ============================================================

import { useState } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

/** Default stale time: 60 seconds. Avoids redundant refetches. */
const STALE_TIME = 60_000;

/** Default cache time: 5 minutes. */
const GC_TIME = 5 * 60_000;

interface QueryProviderProps {
  children: React.ReactNode;
}

export function QueryProvider({ children }: QueryProviderProps) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: STALE_TIME,
            gcTime: GC_TIME,
            retry: 1,
            refetchOnWindowFocus: false,
          },
        },
      })
  );

  return (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
}
