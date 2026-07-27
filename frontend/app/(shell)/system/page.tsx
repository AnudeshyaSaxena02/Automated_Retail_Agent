"use client";

import { useQuery } from "@tanstack/react-query";
import { PageHeader } from "@/components/shared/PageHeader";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  Activity,
  Server,
  Database,
  DatabaseZap,
  RefreshCw,
  ExternalLink,
  CircleCheck,
  TriangleAlert,
  CircleX
} from "lucide-react";
import { getHealth, getRoot, type HealthResponse, type RootResponse } from "@/services/healthService";
import { useSearchStatus } from "@/hooks/useSearchStatus";

function StatusIcon({ state, className }: { state: "operational" | "degraded" | "unavailable" | "checking" | "unknown", className?: string }) {
  switch (state) {
    case "operational":
      return <CircleCheck className={`text-green-500 ${className}`} aria-hidden="true" />;
    case "degraded":
      return <TriangleAlert className={`text-amber-500 ${className}`} aria-hidden="true" />;
    case "unavailable":
      return <CircleX className={`text-destructive ${className}`} aria-hidden="true" />;
    default:
      return <Activity className={`text-muted-foreground ${className}`} aria-hidden="true" />;
  }
}

export default function SystemPage() {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "Unknown";

  const {
    data: health,
    isLoading: healthLoading,
    isError: healthError,
    refetch: refetchHealth,
    isRefetching: healthRefetching,
  } = useQuery<HealthResponse>({
    queryKey: ["health"],
    queryFn: getHealth,
    retry: 1,
  });

  const {
    data: root,
    refetch: refetchRoot,
    isRefetching: rootRefetching,
  } = useQuery<RootResponse>({
    queryKey: ["root"],
    queryFn: getRoot,
    retry: 1,
  });

  const {
    data: search,
    isLoading: searchLoading,
    isError: searchError,
    refetch: refetchSearch,
    isRefetching: searchRefetching,
  } = useSearchStatus();

  const handleRefresh = () => {
    refetchHealth();
    refetchRoot();
    refetchSearch();
  };

  const isInitialLoading = (healthLoading && !health) || (searchLoading && !search);
  const isRefreshing = healthRefetching || rootRefetching || searchRefetching;

  let overallState: "checking" | "operational" | "degraded" | "unavailable" = "checking";
  let overallTitle = "Checking System Status...";
  let overallDesc = "Fetching initial diagnostics from platform services.";
  let bannerClass = "bg-muted text-muted-foreground border-border";

  if (!isInitialLoading) {
    if (healthError || !health) {
      overallState = "unavailable";
      overallTitle = "System Unavailable";
      overallDesc = "Critical API communication failed. The backend service is unreachable.";
      bannerClass = "bg-destructive/10 text-destructive border-destructive/20";
    } else if (
      health.status === "healthy" &&
      health.database === "connected" &&
      (!searchError && search?.status === "ready")
    ) {
      overallState = "operational";
      overallTitle = "All Systems Operational";
      overallDesc = "Platform services, connectivity, and search infrastructure are running normally.";
      bannerClass = "bg-green-500/10 text-green-700 dark:text-green-400 border-green-500/20";
    } else {
      overallState = "degraded";
      overallTitle = "System Degraded";
      overallDesc = "The core platform is reachable, but one or more services are reporting issues.";
      bannerClass = "bg-amber-500/10 text-amber-700 dark:text-amber-400 border-amber-500/20";
    }
  }

  return (
    <div className="max-w-5xl mx-auto w-full pb-12">
      <PageHeader
        title="System Health & Diagnostics"
        description="Monitor platform services, connectivity, and runtime health."
        actions={
          <Button variant="outline" onClick={handleRefresh} disabled={isInitialLoading || isRefreshing}>
            <RefreshCw className={`mr-2 h-4 w-4 ${isRefreshing ? "animate-spin" : ""}`} aria-hidden="true" />
            Refresh Status
          </Button>
        }
      />

      <div className="grid gap-6">
        {/* Overall Status Banner */}
        <div className={`rounded-lg border p-5 flex items-start gap-4 transition-colors ${bannerClass}`}>
          <div className="mt-0.5">
            <StatusIcon state={overallState} className="h-6 w-6" />
          </div>
          <div>
            <h2 className="text-lg font-semibold tracking-tight">{overallTitle}</h2>
            <p className="text-sm mt-1 opacity-90">{overallDesc}</p>
          </div>
        </div>

        {/* Service Overview Cards */}
        <div className="grid gap-4 md:grid-cols-3">
          {/* API Service */}
          <Card>
            <CardContent className="p-5 flex items-start gap-4">
              <div className="rounded-full bg-primary/10 p-2.5 shrink-0">
                <Server className="h-5 w-5 text-primary" aria-hidden="true" />
              </div>
              <div className="space-y-1">
                <p className="text-sm font-medium leading-none">API Service</p>
                <div className="flex items-center gap-1.5 mt-1">
                  <StatusIcon
                    state={healthError ? "unavailable" : health?.status === "healthy" ? "operational" : health?.status === "degraded" ? "degraded" : "checking"}
                    className="h-3.5 w-3.5"
                  />
                  <span className="text-sm font-medium">
                    {healthError ? "Unavailable" : health?.status === "healthy" ? "Operational" : health?.status === "degraded" ? "Degraded" : "Checking"}
                  </span>
                </div>
                <p className="text-xs text-muted-foreground pt-1">
                  {root ? `Version ${root.version}` : "IDAM Backend"}
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Database */}
          <Card>
            <CardContent className="p-5 flex items-start gap-4">
              <div className="rounded-full bg-primary/10 p-2.5 shrink-0">
                <Database className="h-5 w-5 text-primary" aria-hidden="true" />
              </div>
              <div className="space-y-1">
                <p className="text-sm font-medium leading-none">Database</p>
                <div className="flex items-center gap-1.5 mt-1">
                  <StatusIcon
                    state={healthError ? "unavailable" : health?.database === "connected" ? "operational" : health?.database ? "degraded" : "checking"}
                    className="h-3.5 w-3.5"
                  />
                  <span className="text-sm font-medium">
                    {healthError ? "Unknown" : health?.database === "connected" ? "Connected" : health?.database || "Checking"}
                  </span>
                </div>
                <p className="text-xs text-muted-foreground pt-1">
                  Application Database
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Search Index */}
          <Card>
            <CardContent className="p-5 flex items-start gap-4">
              <div className="rounded-full bg-primary/10 p-2.5 shrink-0">
                <DatabaseZap className="h-5 w-5 text-primary" aria-hidden="true" />
              </div>
              <div className="space-y-1">
                <p className="text-sm font-medium leading-none">Vector Search</p>
                <div className="flex items-center gap-1.5 mt-1">
                  <StatusIcon
                    state={searchError ? "unavailable" : search?.status === "ready" ? "operational" : search?.status === "empty" ? "degraded" : "checking"}
                    className="h-3.5 w-3.5"
                  />
                  <span className="text-sm font-medium capitalize">
                    {searchError ? "Unavailable" : search?.status || "Checking"}
                  </span>
                </div>
                <p className="text-xs text-muted-foreground pt-1">
                  {search ? `${search.indexed_count} products indexed` : "Search infrastructure"}
                </p>
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="grid gap-6 md:grid-cols-2">
          {/* Service Diagnostics */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Service Diagnostics</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="grid grid-cols-[1fr_2fr] gap-2 border-b border-border pb-4 last:border-0 last:pb-0">
                  <span className="text-sm font-medium text-muted-foreground">API Service</span>
                  <span className="text-sm">
                    {healthError ? "Cannot connect to the backend server." : health ? "Backend responding normally." : "Checking..."}
                  </span>
                </div>
                <div className="grid grid-cols-[1fr_2fr] gap-2 border-b border-border pb-4 last:border-0 last:pb-0">
                  <span className="text-sm font-medium text-muted-foreground">Database</span>
                  <span className="text-sm">
                    {healthError ? "Connectivity unknown." : health?.database === "connected" ? "Database connectivity reported successfully by backend health check." : health?.database ? `Reported state: ${health.database}` : "Checking..."}
                  </span>
                </div>
                <div className="grid grid-cols-[1fr_2fr] gap-2 border-b border-border pb-4 last:border-0 last:pb-0">
                  <span className="text-sm font-medium text-muted-foreground">Search Engine</span>
                  <div className="text-sm space-y-1">
                    <p>{searchError ? "Vector database unreachable." : search ? "ChromaDB index connected." : "Checking..."}</p>
                    {search && (
                      <p className="text-muted-foreground text-xs">Model: {search.model}</p>
                    )}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Application Information */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Application Information</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="grid grid-cols-[1fr_2fr] gap-2">
                  <span className="text-sm font-medium text-muted-foreground">Application</span>
                  <span className="text-sm">{root?.app || "IDAM Retail Intelligence Platform"}</span>
                </div>
                <div className="grid grid-cols-[1fr_2fr] gap-2">
                  <span className="text-sm font-medium text-muted-foreground">Backend Version</span>
                  <span className="text-sm">{root?.version || "Unknown"}</span>
                </div>
                <div className="grid grid-cols-[1fr_2fr] gap-2">
                  <span className="text-sm font-medium text-muted-foreground">Environment</span>
                  <span className="text-sm capitalize">{process.env.NODE_ENV || "Unknown"}</span>
                </div>
                <div className="grid grid-cols-[1fr_2fr] gap-2">
                  <span className="text-sm font-medium text-muted-foreground">API Endpoint</span>
                  <span className="text-sm font-mono break-all">{apiUrl}</span>
                </div>

                {root?.docs && (
                  <div className="pt-4 mt-2 border-t border-border">
                    <Button variant="outline" size="sm" onClick={() => window.open(root.docs, '_blank', 'noopener,noreferrer')}>
                      <ExternalLink className="mr-2 h-4 w-4" aria-hidden="true" />
                      Open API Documentation
                    </Button>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
