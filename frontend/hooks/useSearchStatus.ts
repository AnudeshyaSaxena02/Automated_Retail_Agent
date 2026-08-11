// ============================================================
// hooks/useSearchStatus.ts
//
// TanStack Query wrapper for GET /search/status.
// Used by Dashboard KPI cards: indexed count + engine status.
//
// Query key: ["search-status"]
// Stale time: 120s — index status changes rarely
// ============================================================

import { useQuery } from "@tanstack/react-query";
import { getSearchStatus } from "@/services/searchService";
import type { IndexStatusResponse } from "@/types/contracts/search";

export function useSearchStatus() {
  return useQuery<IndexStatusResponse, Error>({
    queryKey: ["search-status"],
    queryFn: getSearchStatus,
    staleTime: 120_000,      // 2 minutes
    gcTime: 10 * 60_000,     // 10 minutes
    retry: 1,
    refetchOnWindowFocus: false,
  });
}
