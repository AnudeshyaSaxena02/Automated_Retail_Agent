// ============================================================
// services/healthService.ts
//
// HTTP wrappers for the backend health and root endpoints.
//
// Endpoints:
//   GET /health → HealthResponse
//   GET /       → RootResponse
//
// Used by: useHealth hook (Header health dot), system page
// ============================================================

import { apiClient } from "@/lib/api-client";

export interface HealthResponse {
  status: "healthy" | "degraded" | string;
  database: "connected" | "error" | string;
}

export interface RootResponse {
  status: string;
  app: string;
  version: string;
  docs: string;
}

export async function getHealth(): Promise<HealthResponse> {
  const response = await apiClient.get<HealthResponse>("/health");
  return response.data;
}

export async function getRoot(): Promise<RootResponse> {
  const response = await apiClient.get<RootResponse>("/");
  return response.data;
}
