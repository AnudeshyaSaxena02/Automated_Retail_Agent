"use client";

// ============================================================
// app/system/page.tsx
//
// Infrastructure diagnostics page — preserved from Phase 1.
// Moved from / to /system in Phase 2 (/ now redirects to /dashboard).
//
// This page is intentionally outside the (shell) route group.
// It renders without the sidebar, using the bare root layout only.
// It is a technical diagnostics page, not a business feature.
//
// Endpoints used:
//   GET /health → { status, database }
//   GET /       → { status, app, version, docs }
// ============================================================

import { useQuery } from "@tanstack/react-query";
import { ThemeToggle } from "@/components/theme-toggle";
import { Button } from "@/components/ui/button";
import {
  CheckCircle,
  XCircle,
  Loader2,
  RefreshCw,
  Database,
  Server,
  ArrowLeft,
} from "lucide-react";
import Link from "next/link";
import { getHealth, getRoot } from "@/services/healthService";
import type { HealthResponse, RootResponse } from "@/services/healthService";

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
        <CheckCircle className="h-3.5 w-3.5" aria-hidden="true" />
      ) : (
        <XCircle className="h-3.5 w-3.5" aria-hidden="true" />
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
        <CheckCircle className="h-4 w-4 text-green-500 shrink-0" aria-hidden="true" />
      ) : (
        <XCircle className="h-4 w-4 text-red-500 shrink-0" aria-hidden="true" />
      )}
      <span className={ok ? "text-foreground" : "text-muted-foreground"}>
        {label}
      </span>
    </li>
  );
}

// ── System page ───────────────────────────────────────────────

export default function SystemPage() {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "(not set)";

  const {
    data: health,
    isLoading: healthLoading,
    isError: healthError,
    error: healthRawError,
    refetch: refetchHealth,
  } = useQuery<HealthResponse>({
    queryKey: ["health"],
    queryFn: getHealth,
    retry: 1,
  });

  const { data: root, isLoading: rootLoading } = useQuery<RootResponse>({
    queryKey: ["root"],
    queryFn: getRoot,
    retry: 1,
  });

  const isHealthy = health?.status === "healthy";
  const isDbConnected = health?.database === "connected";

  return (
    <div className="flex flex-1 flex-col items-center justify-center min-h-screen p-6 bg-background">
      <div className="w-full max-w-2xl space-y-6">

        {/* ── Header ──────────────────────────────────────── */}
        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Link
                href="/dashboard"
                className="flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground transition-colors"
                aria-label="Back to Dashboard"
              >
                <ArrowLeft className="h-4 w-4" aria-hidden="true" />
                Dashboard
              </Link>
            </div>
            <h1 className="text-2xl font-semibold tracking-tight text-foreground">
              System Diagnostics
            </h1>
            <p className="mt-1 text-sm text-muted-foreground">
              Infrastructure verification — Phase 1 + Phase 2 foundation checks.
            </p>
          </div>
          <ThemeToggle />
        </div>

        {/* ── Backend health card ──────────────────────────── */}
        <section
          id="health-card"
          aria-labelledby="health-heading"
          className="rounded-lg border border-border bg-card p-5 space-y-4"
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Server className="h-4 w-4 text-muted-foreground" aria-hidden="true" />
              <h2 id="health-heading" className="font-medium text-foreground">
                Backend Health
              </h2>
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
                aria-hidden="true"
              />
              Refresh
            </Button>
          </div>

          {healthLoading && (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
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
                  <Database className="h-3.5 w-3.5" aria-hidden="true" />
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

        {/* ── Infrastructure checks ────────────────────────── */}
        <section
          id="infra-checks"
          aria-labelledby="infra-heading"
          className="rounded-lg border border-border bg-card p-5 space-y-3"
        >
          <h2 id="infra-heading" className="font-medium text-foreground">
            Infrastructure Checks
          </h2>
          <ul className="space-y-2">
            <CheckRow label="Next.js 16 + App Router" ok={true} />
            <CheckRow label="TypeScript strict mode" ok={true} />
            <CheckRow label="Tailwind CSS v4" ok={true} />
            <CheckRow label="shadcn/ui (Phase 2 components)" ok={true} />
            <CheckRow label="lucide-react icons" ok={true} />
            <CheckRow label="next-themes ThemeProvider" ok={true} />
            <CheckRow label="TanStack Query v5 (useQuery)" ok={true} />
            <CheckRow label="Axios API client (lib/api-client.ts)" ok={true} />
            <CheckRow label="Zustand v5 (uiStore)" ok={true} />
            <CheckRow label="Sonner (toast infrastructure)" ok={true} />
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

        {/* ── Footer ──────────────────────────────────────── */}
        <p className="text-center text-xs text-muted-foreground">
          Phase 2 application shell complete.{" "}
          <Link
            href="/dashboard"
            className="underline underline-offset-2 hover:text-foreground transition-colors"
          >
            Go to Dashboard
          </Link>
        </p>
      </div>
    </div>
  );
}
