// ============================================================
// hooks/useHealth.ts
//
// TanStack Query wrapper for GET /health.
// Used by Header health indicator dot and system page.
//
// Query key: ["health"]
// Stale time: 60s — health status rarely changes mid-session
// ============================================================

import { useQuery } from "@tanstack/react-query";
import { getHealth } from "@/services/healthService";
import type { HealthResponse } from "@/services/healthService";

export function useHealth() {
  return useQuery<HealthResponse, Error>({
    queryKey: ["health"],
    queryFn: getHealth,
    staleTime: 60_000,       // 60 seconds
    gcTime: 5 * 60_000,      // 5 minutes
    retry: 1,                // one retry on failure
    refetchOnWindowFocus: false,
  });
}
