// ============================================================
// app/(shell)/customers/page.tsx
//
// Phase 4: Customer Directory with client-side filtering and
// pagination (backend GET /customers returns all customers).
// ============================================================

"use client";

"use client";

import { useState, useEffect, Suspense } from "react";
import { useRouter, usePathname, useSearchParams } from "next/navigation";
import { PageHeader } from "@/components/shared/PageHeader";
import { useCustomers } from "@/hooks/useCustomers";
import { CustomerTable } from "@/components/customers/CustomerTable";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Search } from "lucide-react";
import { useDebounce } from "@/hooks/useDebounce";
import { LoadingSkeleton } from "@/components/shared/LoadingSkeleton";
import { ErrorBanner } from "@/components/shared/ErrorBanner";

function CustomersPageContent() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  // Read URL initial state
  const initialQ = searchParams.get("q") || "";
  const initialPage = Number(searchParams.get("page")) || 1;

  const [q, setQ] = useState(initialQ);
  const [page, setPage] = useState(initialPage);
  
  const debouncedQ = useDebounce(q, 300);
  const limit = 20;

  // Sync to URL
  useEffect(() => {
    const params = new URLSearchParams();
    if (debouncedQ.trim().length > 0) {
      params.set("q", debouncedQ);
    }
    if (page > 1) {
      params.set("page", page.toString());
    }

    const newQuery = params.toString();
    const currentQuery = searchParams.toString();
    
    if (newQuery !== currentQuery) {
      router.push(`${pathname}?${newQuery}`, { scroll: false });
    }
  }, [debouncedQ, page, pathname, router, searchParams]);

  const { data, isLoading, error, refetch } = useCustomers();

  if (isLoading) {
    return (
      <div className="space-y-6">
        <PageHeader title="Customers" description="Manage your store's customer base." />
        <LoadingSkeleton variant="list" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <PageHeader title="Customers" description="Manage your store's customer base." />
        <ErrorBanner 
          message={error.message} 
          onRetry={() => refetch()} 
        />
      </div>
    );
  }

  // Client-side filtering
  const allCustomers = data?.customers || [];
  const searchLower = debouncedQ.toLowerCase();
  
  const filteredCustomers = searchLower 
    ? allCustomers.filter(c => 
        c.customer_id.toLowerCase().includes(searchLower) ||
        c.name.toLowerCase().includes(searchLower) ||
        (c.email && c.email.toLowerCase().includes(searchLower))
      )
    : allCustomers;

  // Client-side pagination
  const totalPages = Math.max(1, Math.ceil(filteredCustomers.length / limit));
  
  // Safe page clamping
  const safePage = Math.min(Math.max(1, page), totalPages);

  const offset = (safePage - 1) * limit;
  const paginatedCustomers = filteredCustomers.slice(offset, offset + limit);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Customers"
        description="View customer profiles, preferences, and purchase history."
      />

      {/* Toolbar */}
      <div className="flex flex-col sm:flex-row gap-4 items-center justify-between">
        <div className="relative w-full max-w-sm">
          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            type="search"
            placeholder="Search by name, ID, or email..."
            className="pl-8"
            value={q}
            onChange={(e) => {
              setQ(e.target.value);
              setPage(1); // Reset page on search
            }}
          />
        </div>
      </div>

      <CustomerTable 
        customers={paginatedCustomers} 
        emptyTitle={searchLower ? `No results for "${debouncedQ}"` : "No customers found"}
        emptyDescription={searchLower ? "Try adjusting your search query." : "There are currently no customers in the database."}
      />

      {/* Pagination Controls */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between mt-4">
          <div className="text-sm text-muted-foreground">
            Showing {offset + 1} to {Math.min(offset + limit, filteredCustomers.length)} of {filteredCustomers.length} customers
          </div>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              disabled={safePage <= 1}
              onClick={() => setPage(p => Math.max(1, p - 1))}
            >
              Previous
            </Button>
            <div className="flex items-center px-4 text-sm font-medium">
              Page {safePage} of {totalPages}
            </div>
            <Button
              variant="outline"
              size="sm"
              disabled={safePage >= totalPages}
              onClick={() => setPage(p => Math.min(totalPages, p + 1))}
            >
              Next
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}

export default function CustomersPage() {
  return (
    <Suspense fallback={
      <div className="space-y-6">
        <PageHeader title="Customers" description="Manage your store's customer base." />
        <LoadingSkeleton variant="list" />
      </div>
    }>
      <CustomersPageContent />
    </Suspense>
  );
}
