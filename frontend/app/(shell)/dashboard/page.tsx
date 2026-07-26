"use client";

// ============================================================
// app/(shell)/dashboard/page.tsx
//
// Dashboard — operational platform overview.
//
// Data sources (all real backend endpoints):
//   GET /products?limit=1  → total product count
//   GET /customers          → total customer count + list
//   GET /search/status      → indexed count + engine status
//   GET /health             → backend operational status
//
// Rules:
//   - No fabricated metrics (revenue, sales, orders, trends)
//   - Each KPI card handles loading/error independently
//   - Customer Overview labeled accurately (no recency assumption)
//   - Customer rows are informational only (no /customers/{id} links in Phase 2)
// ============================================================

import { PageHeader } from "@/components/shared/PageHeader";
import { LoadingSkeleton } from "@/components/shared/LoadingSkeleton";
import { ErrorBanner } from "@/components/shared/ErrorBanner";
import { EmptyState } from "@/components/shared/EmptyState";
import { useProductCount } from "@/hooks/useProductCount";
import { useCustomers } from "@/hooks/useCustomers";
import { useSearchStatus } from "@/hooks/useSearchStatus";
import { useHealth } from "@/hooks/useHealth";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Package,
  Users,
  Database,
  Cpu,
  Sparkles,
  ArrowRight,
} from "lucide-react";
import Link from "next/link";
import { extractApiError } from "@/types/api";

// ── KPI Card ──────────────────────────────────────────────────

interface KpiCardProps {
  title: string;
  icon: React.ReactNode;
  isLoading: boolean;
  error: Error | null;
  onRetry: () => void;
  children: React.ReactNode;
}

function KpiCard({
  title,
  icon,
  isLoading,
  error,
  onRetry,
  children,
}: KpiCardProps) {
  return (
    <Card role="region" aria-label={title}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">
          {title}
        </CardTitle>
        <div className="text-muted-foreground">{icon}</div>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="space-y-2 pt-1">
            <div className="h-8 w-16 animate-pulse rounded bg-muted" />
            <div className="h-3 w-20 animate-pulse rounded bg-muted" />
          </div>
        ) : error ? (
          <ErrorBanner
            message={extractApiError(error).message || "Failed to load"}
            onRetry={onRetry}
          />
        ) : (
          children
        )}
      </CardContent>
    </Card>
  );
}

// ── Quick Action Link ─────────────────────────────────────────

interface QuickActionProps {
  label: string;
  description: string;
  href: string;
  icon: React.ReactNode;
}

function QuickAction({ label, description, href, icon }: QuickActionProps) {
  return (
    <Link
      href={href}
      aria-label={`Navigate to ${label}`}
      className="flex items-center gap-4 rounded-lg border border-border bg-card p-4 hover:bg-accent hover:text-accent-foreground transition-colors group"
    >
      <div className="rounded-md bg-primary/10 p-2 text-primary shrink-0">
        {icon}
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-foreground truncate">{label}</p>
        <p className="text-xs text-muted-foreground truncate">{description}</p>
      </div>
      <ArrowRight
        className="h-4 w-4 text-muted-foreground group-hover:text-foreground transition-colors shrink-0"
        aria-hidden="true"
      />
    </Link>
  );
}

// ── Dashboard Page ────────────────────────────────────────────

export default function DashboardPage() {
  const productCount = useProductCount();
  const customers = useCustomers();
  const searchStatus = useSearchStatus();
  const health = useHealth();

  const displayedCustomers = customers.data?.customers.slice(0, 5) ?? [];

  return (
    <div className="space-y-8">
      <PageHeader
        title="Dashboard"
        description="Platform operational overview"
      />

      {/* ── KPI Cards ─────────────────────────────────────── */}
      <section aria-labelledby="kpi-heading">
        <h2 id="kpi-heading" className="sr-only">
          Key Metrics
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">

          {/* Products in Catalog */}
          <KpiCard
            title="Products in Catalog"
            icon={<Package className="h-4 w-4" aria-hidden="true" />}
            isLoading={productCount.isLoading}
            error={productCount.error}
            onRetry={() => productCount.refetch()}
          >
            {productCount.data === 0 ? (
              <p className="text-sm text-muted-foreground">
                No products in catalog
              </p>
            ) : (
              <>
                <p
                  className="text-3xl font-bold text-foreground"
                  aria-label={`${productCount.data} products`}
                >
                  {productCount.data?.toLocaleString("en-IN")}
                </p>
                <p className="text-xs text-muted-foreground mt-1">products</p>
              </>
            )}
          </KpiCard>

          {/* Registered Customers */}
          <KpiCard
            title="Registered Customers"
            icon={<Users className="h-4 w-4" aria-hidden="true" />}
            isLoading={customers.isLoading}
            error={customers.error}
            onRetry={() => customers.refetch()}
          >
            {customers.data?.total === 0 ? (
              <p className="text-sm text-muted-foreground">
                No customers registered
              </p>
            ) : (
              <>
                <p
                  className="text-3xl font-bold text-foreground"
                  aria-label={`${customers.data?.total} customers`}
                >
                  {customers.data?.total?.toLocaleString("en-IN")}
                </p>
                <p className="text-xs text-muted-foreground mt-1">customers</p>
              </>
            )}
          </KpiCard>

          {/* Indexed for Search */}
          <KpiCard
            title="Indexed for Search"
            icon={<Database className="h-4 w-4" aria-hidden="true" />}
            isLoading={searchStatus.isLoading}
            error={searchStatus.error}
            onRetry={() => searchStatus.refetch()}
          >
            {searchStatus.data?.indexed_count === 0 ? (
              <p className="text-xs text-muted-foreground">
                Index empty — semantic search unavailable
              </p>
            ) : (
              <>
                <p
                  className="text-3xl font-bold text-foreground"
                  aria-label={`${searchStatus.data?.indexed_count} products indexed`}
                >
                  {searchStatus.data?.indexed_count?.toLocaleString("en-IN")}
                </p>
                <p className="text-xs text-muted-foreground mt-1">
                  products indexed
                </p>
              </>
            )}
          </KpiCard>

          {/* Search Engine Status */}
          <KpiCard
            title="Search Engine"
            icon={<Cpu className="h-4 w-4" aria-hidden="true" />}
            isLoading={searchStatus.isLoading}
            error={searchStatus.error}
            onRetry={() => searchStatus.refetch()}
          >
            {searchStatus.data ? (
              <div className="space-y-2">
                <Badge
                  variant={
                    searchStatus.data.status === "ready"
                      ? "default"
                      : "secondary"
                  }
                  aria-label={`Search engine status: ${searchStatus.data.status}`}
                >
                  {searchStatus.data.status === "ready" ? "Ready" : "Index Empty"}
                </Badge>
                <p className="text-xs text-muted-foreground">
                  {searchStatus.data.model}
                </p>
              </div>
            ) : null}
          </KpiCard>
        </div>
      </section>

      {/* ── Quick Actions ─────────────────────────────────── */}
      <section aria-labelledby="quick-actions-heading">
        <h2
          id="quick-actions-heading"
          className="text-base font-semibold text-foreground mb-3"
        >
          Quick Actions
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <QuickAction
            label="Browse Products"
            description="View and search the product catalog"
            href="/products"
            icon={<Package className="h-4 w-4" aria-hidden="true" />}
          />
          <QuickAction
            label="View Customers"
            description="Explore customer profiles and data"
            href="/customers"
            icon={<Users className="h-4 w-4" aria-hidden="true" />}
          />
          <QuickAction
            label="AI Workspace"
            description="Chat with the AI shopping assistant"
            href="/ai"
            icon={<Sparkles className="h-4 w-4" aria-hidden="true" />}
          />
        </div>
      </section>

      {/* ── System Status ─────────────────────────────────── */}
      <section aria-labelledby="system-status-heading">
        <h2
          id="system-status-heading"
          className="text-base font-semibold text-foreground mb-3"
        >
          System Status
        </h2>
        <div className="rounded-lg border border-border bg-card px-5 py-4">
          {health.isLoading ? (
            <div className="flex items-center gap-2">
              <div className="h-2 w-2 rounded-full bg-muted-foreground/40 animate-pulse" />
              <span className="text-sm text-muted-foreground">
                Checking backend status...
              </span>
            </div>
          ) : health.error ? (
            <div className="flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-destructive shrink-0" />
              <span className="text-sm text-muted-foreground">
                Backend unreachable
              </span>
            </div>
          ) : (
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div className="flex items-center gap-2">
                <span
                  className={`h-2 w-2 rounded-full shrink-0 ${
                    health.data?.status === "healthy"
                      ? "bg-green-500"
                      : "bg-amber-500"
                  }`}
                  aria-hidden="true"
                />
                <span className="text-sm text-foreground font-medium">
                  {health.data?.status === "healthy"
                    ? "All systems operational"
                    : "System degraded"}
                </span>
              </div>
              <div className="flex items-center gap-4 text-xs text-muted-foreground">
                <span>
                  Database:{" "}
                  <span
                    className={
                      health.data?.database === "connected"
                        ? "text-green-600 dark:text-green-400"
                        : "text-amber-600 dark:text-amber-400"
                    }
                  >
                    {health.data?.database}
                  </span>
                </span>
                <Link
                  href="/system"
                  className="underline underline-offset-2 hover:text-foreground transition-colors"
                  aria-label="View full system diagnostics"
                >
                  View diagnostics
                </Link>
              </div>
            </div>
          )}
        </div>
      </section>

      {/* ── Customer Overview ─────────────────────────────── */}
      <section aria-labelledby="customer-overview-heading">
        <h2
          id="customer-overview-heading"
          className="text-base font-semibold text-foreground mb-3"
        >
          Customer Overview
        </h2>
        {/* NOTE: GET /customers has no recency ordering guarantee.
            Rows are informational only — no click navigation in Phase 2.
            Customer detail links added in Phase 4. */}

        {customers.isLoading ? (
          <LoadingSkeleton variant="list" count={5} />
        ) : customers.error ? (
          <ErrorBanner
            message="Failed to load customers"
            onRetry={() => customers.refetch()}
          />
        ) : displayedCustomers.length === 0 ? (
          <EmptyState
            icon={Users}
            title="No customers registered yet"
            description="Customers appear here once they are added to the system."
          />
        ) : (
          <div className="rounded-lg border border-border bg-card overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border bg-muted/30">
                  <th
                    scope="col"
                    className="py-3 px-4 text-left text-xs font-medium text-muted-foreground uppercase tracking-wide"
                  >
                    Customer ID
                  </th>
                  <th
                    scope="col"
                    className="py-3 px-4 text-left text-xs font-medium text-muted-foreground uppercase tracking-wide"
                  >
                    Name
                  </th>
                  <th
                    scope="col"
                    className="py-3 px-4 text-left text-xs font-medium text-muted-foreground uppercase tracking-wide hidden sm:table-cell"
                  >
                    Email
                  </th>
                </tr>
              </thead>
              <tbody>
                {displayedCustomers.map((customer, index) => (
                  <tr
                    key={customer.customer_id}
                    className={
                      index < displayedCustomers.length - 1
                        ? "border-b border-border"
                        : ""
                    }
                  >
                    <td className="py-3 px-4 font-mono text-xs text-muted-foreground">
                      {customer.customer_id}
                    </td>
                    <td className="py-3 px-4 font-medium text-foreground">
                      {customer.name}
                    </td>
                    <td className="py-3 px-4 text-muted-foreground hidden sm:table-cell">
                      {customer.email ?? "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {(customers.data?.total ?? 0) > 5 && (
              <div className="border-t border-border px-4 py-2 text-xs text-muted-foreground">
                Showing 5 of {customers.data?.total} customers. Full customer
                management available in Phase 4.
              </div>
            )}
          </div>
        )}
      </section>
    </div>
  );
}
