// ============================================================
// components/shared/LoadingSkeleton.tsx
//
// Generic skeleton placeholder component.
// Uses shadcn Skeleton primitive (requires: pnpm dlx shadcn add skeleton).
//
// Variants:
//   "kpi"   — matches KPI card dimensions (Dashboard)
//   "list"  — a stack of horizontal rows (tables / customer lists)
//   "card"  — a generic card placeholder
// ============================================================

import { Skeleton } from "@/components/ui/skeleton";

interface LoadingSkeletonProps {
  variant?: "kpi" | "list" | "card";
  count?: number;
}

export function LoadingSkeleton({
  variant = "card",
  count = 1,
}: LoadingSkeletonProps) {
  if (variant === "kpi") {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {Array.from({ length: count }).map((_, i) => (
          <div
            key={i}
            className="rounded-lg border border-border bg-card p-5 space-y-3"
          >
            <Skeleton className="h-4 w-28" />
            <Skeleton className="h-8 w-16" />
            <Skeleton className="h-3 w-20" />
          </div>
        ))}
      </div>
    );
  }

  if (variant === "list") {
    return (
      <div className="space-y-2">
        {Array.from({ length: count }).map((_, i) => (
          <div key={i} className="flex items-center gap-4 py-2">
            <Skeleton className="h-4 w-20" />
            <Skeleton className="h-4 flex-1" />
            <Skeleton className="h-4 w-32" />
          </div>
        ))}
      </div>
    );
  }

  // card (default)
  return (
    <div className="space-y-4">
      {Array.from({ length: count }).map((_, i) => (
        <div
          key={i}
          className="rounded-lg border border-border bg-card p-5 space-y-3"
        >
          <Skeleton className="h-5 w-40" />
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-3/4" />
        </div>
      ))}
    </div>
  );
}
