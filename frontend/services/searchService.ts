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
import type { IndexStatusResponse, SemanticSearchResponse } from "@/types/contracts/search";

export async function getSearchStatus(): Promise<IndexStatusResponse> {
  const response = await apiClient.get<IndexStatusResponse>("/search/status");
  return response.data;
}

export async function getSemanticSearch(
  query: string,
  limit: number = 10,
  minScore?: number
): Promise<SemanticSearchResponse> {
  const params: Record<string, string | number> = { q: query, limit };
  if (minScore !== undefined) {
    params.min_score = minScore;
  }
  const response = await apiClient.get<SemanticSearchResponse>("/search/semantic", { params });
  return response.data;
}
