// ============================================================
// services/searchService.ts
//
// Phase 2 scope: search index status only for Dashboard KPI.
// Semantic search service added in Phase 5 (AI Workspace).
//
// Endpoint:
//   GET /search/status → IndexStatusResponse
// ============================================================

import { apiClient } from "@/lib/api-client";
import type { IndexStatusResponse } from "@/types/contracts/search";

export async function getSearchStatus(): Promise<IndexStatusResponse> {
  const response = await apiClient.get<IndexStatusResponse>("/search/status");
  return response.data;
}
