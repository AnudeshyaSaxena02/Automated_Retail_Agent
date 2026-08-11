"use client";

// ============================================================
// app/(shell)/products/search/page.tsx
//
// Semantic Smart Search Page (Phase 5).
// Powered by GET /search/semantic
// ============================================================

import { useState, useEffect, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { PageHeader } from "@/components/shared/PageHeader";
import { ErrorBanner } from "@/components/shared/ErrorBanner";
import { LoadingSkeleton } from "@/components/shared/LoadingSkeleton";
import { EmptyState } from "@/components/shared/EmptyState";
import { SemanticProductCard } from "@/components/products/SemanticProductCard";
import { ProductNavigation } from "@/components/products/ProductNavigation";
import { useSemanticSearch } from "@/hooks/useSemanticSearch";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Sparkles, Search } from "lucide-react";

function SemanticSearchContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const initialQ = searchParams.get("q") || "";

  const activeQuery = initialQ;
  const [inputQuery, setInputQuery] = useState(initialQ);

  // Sync state when URL changes
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setInputQuery(initialQ);
  }, [initialQ]);

  const handleSearch = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!inputQuery.trim()) return;
    router.push(`/products/search?q=${encodeURIComponent(inputQuery.trim())}`);
  };

  const { data, isLoading, error, refetch } = useSemanticSearch(activeQuery, 20);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Products"
        description="Manage your store's inventory and discover products."
      />
      <ProductNavigation />

      <div className="bg-card border border-border p-4 rounded-lg flex gap-2 items-center">
        <Sparkles className="h-5 w-5 text-primary shrink-0" />
        <form onSubmit={handleSearch} className="flex-grow flex gap-2">
          <Input
            placeholder="Describe what you're looking for..."
            value={inputQuery}
            onChange={(e) => setInputQuery(e.target.value)}
            className="flex-grow text-base"
          />
          <Button type="submit" disabled={!inputQuery.trim() || isLoading}>
            <Search className="h-4 w-4 mr-2" />
            Search
          </Button>
        </form>
      </div>

      <section aria-label="Search Results">
        {!activeQuery ? (
          <EmptyState
            icon={Sparkles}
            title="Smart Search"
            description="Type a natural language query above to find semantically related products, even if they don't share exact keywords."
          />
        ) : error ? (
          <ErrorBanner
            message="Failed to perform semantic search. Is the AI backend running?"
            onRetry={() => refetch()}
          />
        ) : isLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
             {Array.from({ length: 8 }).map((_, i) => (
                <LoadingSkeleton key={i} variant="card" />
             ))}
          </div>
        ) : data?.results.length === 0 ? (
          <EmptyState
            icon={Search}
            title="No matches found"
            description={`Could not find any products semantically related to "${activeQuery}". Try adjusting your query.`}
          />
        ) : (
          <div className="space-y-4">
            <div className="flex justify-between items-end">
               <p className="text-sm text-muted-foreground">
                 Found <strong className="text-foreground">{data?.total}</strong> results using model <code className="bg-muted px-1 rounded">{data?.model_used}</code>
               </p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
              {data?.results.map((product) => (
                <SemanticProductCard key={product.product_id} product={product} />
              ))}
            </div>
          </div>
        )}
      </section>
    </div>
  );
}

export default function SemanticSearchPage() {
  return (
    <Suspense fallback={<LoadingSkeleton variant="kpi" />}>
      <SemanticSearchContent />
    </Suspense>
  );
}
