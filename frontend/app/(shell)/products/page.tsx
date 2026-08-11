"use client";

// ============================================================
// app/(shell)/products/page.tsx
//
// Product Catalog Main Page.
// Supports:
//   - Filtered listing (limit, offset, category, brand, min_price, max_price)
//   - Keyword search (q)
//   - Product creation (Dialog + ProductForm)
//
// Behavior:
//   Search and filter APIs are mutually exclusive on backend.
//   If search is active, filters are ignored/disabled.
// ============================================================

import { useState, useEffect, Suspense } from "react";
import { useRouter, usePathname, useSearchParams } from "next/navigation";
import { PageHeader } from "@/components/shared/PageHeader";
import { ErrorBanner } from "@/components/shared/ErrorBanner";
import { LoadingSkeleton } from "@/components/shared/LoadingSkeleton";
import { EmptyState } from "@/components/shared/EmptyState";
import { ProductTable } from "@/components/products/ProductTable";
import { ProductToolbar } from "@/components/products/ProductToolbar";
import { ProductForm } from "@/components/products/ProductForm";
import { ProductNavigation } from "@/components/products/ProductNavigation";
import { useProducts } from "@/hooks/useProducts";
import { useProductSearch } from "@/hooks/useProductSearch";
import { useCreateProduct } from "@/hooks/useCreateProduct";
import { useDebounce } from "@/hooks/useDebounce";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Package, SearchX } from "lucide-react";
import type { ProductCreateRequest } from "@/types/contracts/products";

function ProductsPageContent() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  // ── URL State Sync ──────────────────────────────────────────
  
  // Read initial from URL
  const [q, setQ] = useState(searchParams.get("q") || "");
  const [category, setCategory] = useState(searchParams.get("category") || "");
  const [brand, setBrand] = useState(searchParams.get("brand") || "");
  const [minPrice, setMinPrice] = useState(searchParams.get("min_price") || "");
  const [maxPrice, setMaxPrice] = useState(searchParams.get("max_price") || "");
  const [page, setPage] = useState(Number(searchParams.get("page")) || 1);
  const limit = 20;

  // Debounce fast-changing inputs before pushing to URL / querying
  const debouncedQ = useDebounce(q, 300);
  const debouncedCategory = useDebounce(category, 500);
  const debouncedBrand = useDebounce(brand, 500);
  const debouncedMinPrice = useDebounce(minPrice, 500);
  const debouncedMaxPrice = useDebounce(maxPrice, 500);

  // Sync to URL
  useEffect(() => {
    const params = new URLSearchParams();
    const isSearchActive = debouncedQ.trim().length > 0;

    if (isSearchActive) {
      params.set("q", debouncedQ);
      // In search mode, omit all filter parameters and pagination
    } else {
      if (debouncedCategory) params.set("category", debouncedCategory);
      if (debouncedBrand) params.set("brand", debouncedBrand);
      if (debouncedMinPrice) params.set("min_price", debouncedMinPrice);
      if (debouncedMaxPrice) params.set("max_price", debouncedMaxPrice);
      if (page > 1) params.set("page", page.toString());
    }

    const newQueryString = params.toString();
    const currentQueryString = searchParams.toString();
    
    // Only push if changed to avoid unnecessary renders
    if (newQueryString !== currentQueryString) {
      router.push(`${pathname}?${newQueryString}`, { scroll: false });
    }
  }, [
    debouncedQ,
    debouncedCategory,
    debouncedBrand,
    debouncedMinPrice,
    debouncedMaxPrice,
    page,
    pathname,
    router,
    searchParams,
  ]);

  // ── Queries ───────────────────────────────────────────────

  const isSearchMode = debouncedQ.trim().length > 0;
  const offset = (page - 1) * limit;

  const catalogQuery = useProducts(
    {
      limit,
      offset,
      category: debouncedCategory || undefined,
      brand: debouncedBrand || undefined,
      min_price: debouncedMinPrice ? Number(debouncedMinPrice) : undefined,
      max_price: debouncedMaxPrice ? Number(debouncedMaxPrice) : undefined,
    },
    !isSearchMode // Disable catalog query if searching
  );

  const searchQuery = useProductSearch(debouncedQ, limit, isSearchMode);

  // Active query depends on mode
  const activeQuery = isSearchMode ? searchQuery : catalogQuery;
  const data = activeQuery.data;
  const isLoading = activeQuery.isLoading;
  const error = activeQuery.error;
  const total = data?.total ?? 0;
  const products = data?.products ?? [];

  const totalPages = Math.ceil(total / limit);

  // ── Product Creation ──────────────────────────────────────

  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const createMutation = useCreateProduct();

  const handleCreateSubmit = (data: ProductCreateRequest) => {
    createMutation.mutate(data, {
      onSuccess: () => {
        setIsCreateOpen(false);
        // Page refresh handled by queryClient invalidation in the hook
      },
    });
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Products"
        description="Manage your store's inventory and discover products."
      />
      <ProductNavigation />

      <ProductToolbar
        searchQuery={q}
        onSearchChange={(val) => { setQ(val); setPage(1); }}
        category={category}
        onCategoryChange={(val) => { setCategory(val); setPage(1); }}
        brand={brand}
        onBrandChange={(val) => { setBrand(val); setPage(1); }}
        minPrice={minPrice}
        onMinPriceChange={(val) => { setMinPrice(val); setPage(1); }}
        maxPrice={maxPrice}
        onMaxPriceChange={(val) => { setMaxPrice(val); setPage(1); }}
        onAddProductClick={() => setIsCreateOpen(true)}
      />

      {/* Main Content Area */}
      <section aria-labelledby="product-list-heading" className="min-h-[400px]">
        <h2 id="product-list-heading" className="sr-only">
          Product List
        </h2>

        {error ? (
          <ErrorBanner
            message="Failed to load products. Please check your connection."
            onRetry={() => activeQuery.refetch()}
          />
        ) : isLoading ? (
          <LoadingSkeleton variant="list" count={10} />
        ) : products.length === 0 ? (
          <EmptyState
            icon={isSearchMode ? SearchX : Package}
            title={isSearchMode ? "No search results found" : "No products found"}
            description={
              isSearchMode
                ? `No products matched your search for "${debouncedQ}".`
                : "No products match the selected filters."
            }
            action={{
              label: "Clear Filters",
              onClick: () => {
                setQ("");
                setCategory("");
                setBrand("");
                setMinPrice("");
                setMaxPrice("");
                setPage(1);
              }
            }}
          />
        ) : (
          <div className="space-y-4">
            <ProductTable products={products} />

            {/* Pagination Controls */}
            {totalPages > 1 && (
              <div className="flex items-center justify-between border-t border-border pt-4">
                <p className="text-sm text-muted-foreground">
                  Showing {offset + 1} to {Math.min(offset + limit, total)} of {total} products
                </p>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    disabled={page === 1}
                  >
                    Previous
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                    disabled={page >= totalPages}
                  >
                    Next
                  </Button>
                </div>
              </div>
            )}
            
            {/* Disclaimer for search mode pagination limit */}
            {isSearchMode && total > limit && (
              <p className="text-xs text-muted-foreground text-center">
                Search results are currently limited to the top {limit} matches. 
                Clear search to browse all {total} items using catalog filters.
              </p>
            )}
          </div>
        )}
      </section>

      {/* Create Product Dialog */}
      <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
        <DialogContent className="sm:max-w-[600px] max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Add New Product</DialogTitle>
          </DialogHeader>
          <ProductForm
            onSubmit={handleCreateSubmit}
            isPending={createMutation.isPending}
            onCancel={() => setIsCreateOpen(false)}
          />
        </DialogContent>
      </Dialog>
    </div>
  );
}

export default function ProductsPage() {
  return (
    <Suspense fallback={<LoadingSkeleton variant="kpi" />}>
      <ProductsPageContent />
    </Suspense>
  );
}
