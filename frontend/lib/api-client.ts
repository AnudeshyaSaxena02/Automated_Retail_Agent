// ============================================================
// lib/api-client.ts
//
// Centralised Axios instance for all backend API calls.
//
// Usage:
//   import { apiClient } from "@/lib/api-client";
//   const data = await apiClient.get("/products");
//
// The base URL is read from NEXT_PUBLIC_API_URL, which is set
// in .env.local for local dev and in the deployment environment
// for production. No URL is ever hardcoded here.
// ============================================================

import axios, { AxiosError, AxiosInstance } from "axios";

const baseURL = process.env.NEXT_PUBLIC_API_URL;

if (!baseURL && typeof window !== "undefined") {
  console.warn(
    "[api-client] NEXT_PUBLIC_API_URL is not set. " +
      "API calls will fail. Set it in .env.local."
  );
}

export const apiClient: AxiosInstance = axios.create({
  baseURL: baseURL ?? "",
  headers: {
    "Content-Type": "application/json",
    Accept: "application/json",
  },
  timeout: 30_000,
});

// ── Response interceptor ──────────────────────────────────────
// Preserves structured backend error details when available.
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    return Promise.reject(error);
  }
);
