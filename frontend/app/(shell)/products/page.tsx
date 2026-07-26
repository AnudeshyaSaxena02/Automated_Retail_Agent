// ============================================================
// app/(shell)/products/page.tsx — Phase 3 stub
// ============================================================

import { PageHeader } from "@/components/shared/PageHeader";
import { Package } from "lucide-react";

export const metadata = {
  title: "Products — IDAM",
};

export default function ProductsPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="Products"
        description="Product catalog management — coming in Phase 3"
      />
      <div className="flex flex-col items-center justify-center py-20 text-center">
        <div className="rounded-full bg-muted p-6 mb-4">
          <Package className="h-10 w-10 text-muted-foreground" aria-hidden="true" />
        </div>
        <h2 className="text-lg font-semibold text-foreground mb-2">
          Products — Phase 3
        </h2>
        <p className="text-sm text-muted-foreground max-w-sm">
          Full product catalog, search, filtering, and product detail pages will
          be implemented in Phase 3.
        </p>
      </div>
    </div>
  );
}
