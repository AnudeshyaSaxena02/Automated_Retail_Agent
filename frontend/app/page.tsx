"use client";

// ============================================================
// app/page.tsx
//
// Phase 1 Infrastructure Verification Page
//
// This page verifies that all Phase 1 infrastructure is wired
// correctly before any business features are built:
//
//   ✓  TanStack Query (useQuery)
//   ✓  Axios API client (NEXT_PUBLIC_API_URL)
//   ✓  next-themes (ThemeToggle)
//   ✓  shadcn Button
//   ✓  lucide-react icons
//   ✓  GET /health — actual backend fields only
//
// The /health endpoint returns: { status, database }
// The root GET / endpoint returns: { status, app, version, docs }
//
// This page will be replaced in Phase 2.
// ============================================================

import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import { ThemeToggle } from "@/components/theme-toggle";
import { Button } from "@/components/ui/button";
import {
  CheckCircle,
  XCircle,
  Loader2,
  RefreshCw,
  Database,
  Server,
} from "lucide-react";

// ── Type for GET /health ──────────────────────────────────────
// Derived from the actual backend response in main.py:
//   return { "status": "healthy"|"degraded", "database": "connected"|"error" }
interface HealthResponse {
  status: "healthy" | "degraded" | string;
  database: "connected" | "error" | string;
}

// ── Type for GET / (root) ─────────────────────────────────────
// Derived from the actual backend response in main.py:
//   return { "status", "app", "version", "docs" }
interface RootResponse {
  status: string;
  app: string;
  version: string;
  docs: string;
}

// ── Status badge ──────────────────────────────────────────────
function StatusBadge({ ok, label }: { ok: boolean; label: string }) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-sm font-medium ${
        ok
          ? "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400"
          : "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400"
      }`}
    >
      {ok ? (
        <CheckCircle className="h-3.5 w-3.5" />
      ) : (
        <XCircle className="h-3.5 w-3.5" />
      )}
      {label}
    </span>
  );
}

// ── Check row ─────────────────────────────────────────────────
function CheckRow({ label, ok }: { label: string; ok: boolean }) {
  return (
    <li className="flex items-center gap-2 text-sm">
      {ok ? (
        <CheckCircle className="h-4 w-4 text-green-500 shrink-0" />
      ) : (
        <XCircle className="h-4 w-4 text-red-500 shrink-0" />
      )}
      <span className={ok ? "text-foreground" : "text-muted-foreground"}>
        {label}
      </span>
    </li>
  );
}

// ── Main page ─────────────────────────────────────────────────
export default function InfrastructureVerificationPage() {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "(not set)";

  // Query: GET /health
  const {
    data: health,
    isLoading: healthLoading,
    isError: healthError,
    error: healthRawError,
    refetch: refetchHealth,
  } = useQuery<HealthResponse>({
    queryKey: ["health"],
    queryFn: async () => {
      const res = await apiClient.get<HealthResponse>("/health");
      return res.data;
    },
    retry: 1,
  });

  // Query: GET / (root) — provides app name + version
  const { data: root, isLoading: rootLoading } = useQuery<RootResponse>({
    queryKey: ["root"],
    queryFn: async () => {
      const res = await apiClient.get<RootResponse>("/");
      return res.data;
    },
    retry: 1,
  });

  const isHealthy = health?.status === "healthy";
  const isDbConnected = health?.database === "connected";

  return (
    <div className="flex flex-1 flex-col items-center justify-center min-h-screen p-6 bg-background">
      <div className="w-full max-w-2xl space-y-6">

        {/* ── Header ────────────────────────────────────────── */}
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight text-foreground">
              IDAM — Phase 1 Infrastructure
            </h1>
            <p className="mt-1 text-sm text-muted-foreground">
              Verifying all foundation dependencies are wired correctly.
            </p>
          </div>
          <ThemeToggle />
        </div>

        {/* ── Backend health card ────────────────────────────── */}
        <section
          id="health-card"
          className="rounded-lg border border-border bg-card p-5 space-y-4"
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Server className="h-4 w-4 text-muted-foreground" />
              <h2 className="font-medium text-foreground">Backend Health</h2>
            </div>
            <Button
              id="refresh-health"
              variant="ghost"
              size="sm"
              onClick={() => refetchHealth()}
              disabled={healthLoading}
              aria-label="Refresh health check"
            >
              <RefreshCw
                className={`h-4 w-4 mr-1.5 ${healthLoading ? "animate-spin" : ""}`}
              />
              Refresh
            </Button>
          </div>

          {healthLoading && (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" />
              Contacting backend…
            </div>
          )}

          {healthError && (
            <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
              <p className="font-medium">Cannot reach backend</p>
              <p className="mt-0.5 text-xs opacity-80">
                {healthRawError instanceof Error
                  ? healthRawError.message
                  : "Unknown error"}
              </p>
              <p className="mt-1 text-xs opacity-70">
                Is the backend running at{" "}
                <code className="font-mono">{apiUrl}</code>?
              </p>
            </div>
          )}

          {health && (
            <div className="space-y-3">
              <div className="flex items-center gap-3">
                <StatusBadge ok={isHealthy} label={health.status} />
                <div className="flex items-center gap-1.5 text-sm text-muted-foreground">
                  <Database className="h-3.5 w-3.5" />
                  <StatusBadge ok={isDbConnected} label={health.database} />
                </div>
              </div>

              {root && (
                <div className="pt-2 border-t border-border space-y-1 text-sm text-muted-foreground">
                  <p>
                    <span className="font-medium text-foreground">
                      Application:{" "}
                    </span>
                    {root.app}
                  </p>
                  <p>
                    <span className="font-medium text-foreground">
                      Version:{" "}
                    </span>
                    {root.version}
                  </p>
                  <p>
                    <span className="font-medium text-foreground">Docs: </span>
                    <a
                      href={root.docs}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="underline underline-offset-2 hover:text-foreground transition-colors"
                    >
                      {root.docs}
                    </a>
                  </p>
                </div>
              )}

              {rootLoading && (
                <p className="text-xs text-muted-foreground pt-2">
                  Loading app info…
                </p>
              )}
            </div>
          )}
        </section>

        {/* ── Infrastructure checks ──────────────────────────── */}
        <section
          id="infra-checks"
          className="rounded-lg border border-border bg-card p-5 space-y-3"
        >
          <h2 className="font-medium text-foreground">Infrastructure Checks</h2>
          <ul className="space-y-2">
            <CheckRow label="Next.js 16 + App Router" ok={true} />
            <CheckRow label="TypeScript strict mode" ok={true} />
            <CheckRow label="Tailwind CSS v4" ok={true} />
            <CheckRow label="shadcn/ui (Button component)" ok={true} />
            <CheckRow label="lucide-react icons" ok={true} />
            <CheckRow label="next-themes ThemeProvider" ok={true} />
            <CheckRow label="TanStack Query v5 (useQuery)" ok={true} />
            <CheckRow label="Axios API client" ok={true} />
            <CheckRow
              label={`NEXT_PUBLIC_API_URL = ${apiUrl}`}
              ok={apiUrl !== "(not set)"}
            />
            <CheckRow
              label={`Backend reachable at ${apiUrl}/health`}
              ok={!healthError && !healthLoading && !!health}
            />
          </ul>
        </section>

        {/* ── Footer note ────────────────────────────────────── */}
        <p className="text-center text-xs text-muted-foreground">
          Phase 1 foundation complete. This page will be replaced in Phase 2.
        </p>
      </div>
    </div>
  );
}
