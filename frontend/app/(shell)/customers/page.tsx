// ============================================================
// app/(shell)/customers/page.tsx — Phase 4 stub
// ============================================================

import { PageHeader } from "@/components/shared/PageHeader";
import { Users } from "lucide-react";

export const metadata = {
  title: "Customers — IDAM",
};

export default function CustomersPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="Customers"
        description="Customer management — coming in Phase 4"
      />
      <div className="flex flex-col items-center justify-center py-20 text-center">
        <div className="rounded-full bg-muted p-6 mb-4">
          <Users className="h-10 w-10 text-muted-foreground" aria-hidden="true" />
        </div>
        <h2 className="text-lg font-semibold text-foreground mb-2">
          Customers — Phase 4
        </h2>
        <p className="text-sm text-muted-foreground max-w-sm">
          Full customer list, profiles, AI memory, and order history will be
          implemented in Phase 4.
        </p>
      </div>
    </div>
  );
}
