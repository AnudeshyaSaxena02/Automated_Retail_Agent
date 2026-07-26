"use client";

// ============================================================
// app/(shell)/products/[productId]/page.tsx
//
// Product Detail Page.
// Displays detailed information for a single product.
// ============================================================

import { use, Suspense } from "react";
import { useRouter } from "next/navigation";
import { useProduct } from "@/hooks/useProduct";
import { PageHeader } from "@/components/shared/PageHeader";
import { ErrorBanner } from "@/components/shared/ErrorBanner";
import { LoadingSkeleton } from "@/components/shared/LoadingSkeleton";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ArrowLeft, Tag, Box, Hash } from "lucide-react";
import { formatCurrency } from "@/utils/formatCurrency";
import { formatDate } from "@/utils/formatDate";

interface ProductDetailsPageProps {
  params: Promise<{ productId: string }>;
}

function ProductDetailsContent({ productId }: { productId: string }) {
  const router = useRouter();
  const { data: product, isLoading, error, refetch } = useProduct(productId);

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="h-10 w-32 bg-muted animate-pulse rounded" />
        <LoadingSkeleton variant="card" />
        <LoadingSkeleton variant="list" count={4} />
      </div>
    );
  }

  if (error || !product) {
    return (
      <div className="space-y-6">
        <Button variant="ghost" onClick={() => router.push("/products")}>
          <ArrowLeft className="mr-2 h-4 w-4" /> Back to Catalog
        </Button>
        <ErrorBanner
          message={`Failed to load product '${productId}'. It may not exist.`}
          onRetry={() => refetch()}
        />
      </div>
    );
  }

  const specsEntries = Object.entries(product.specifications || {});

  return (
    <div className="space-y-6 max-w-5xl">
      {/* Back Button */}
      <div>
        <Button
          variant="ghost"
          onClick={() => router.push("/products")}
          className="text-muted-foreground hover:text-foreground -ml-4"
        >
          <ArrowLeft className="mr-2 h-4 w-4" /> Back to Catalog
        </Button>
      </div>

      <PageHeader 
        title={product.name} 
        description={`Product ID: ${product.product_id}`}
        actions={
          <div className="flex items-center gap-2 mt-2 sm:mt-0">
            <Badge variant="secondary" className="text-sm">
              {product.category}
            </Badge>
            {product.brand && (
              <Badge variant="outline" className="text-sm">
                {product.brand}
              </Badge>
            )}
          </div>
        }
      />

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Left Column: Key Info */}
        <div className="md:col-span-2 space-y-6">
          <section className="rounded-lg border border-border bg-card p-6 space-y-4">
            <h2 className="text-lg font-semibold text-foreground border-b border-border pb-2">
              Overview
            </h2>
            <div className="prose prose-sm dark:prose-invert max-w-none text-muted-foreground">
              {product.description ? (
                <p>{product.description}</p>
              ) : (
                <p className="italic">No description provided.</p>
              )}
            </div>

            {product.tags && product.tags.length > 0 && (
              <div className="pt-4 flex flex-wrap gap-2">
                {product.tags.map((tag, idx) => (
                  <Badge key={idx} variant="secondary" className="bg-muted text-muted-foreground font-normal">
                    <Tag className="mr-1 h-3 w-3" />
                    {tag}
                  </Badge>
                ))}
              </div>
            )}
          </section>

          {/* Specifications */}
          <section className="rounded-lg border border-border bg-card p-6 space-y-4">
            <h2 className="text-lg font-semibold text-foreground border-b border-border pb-2">
              Specifications
            </h2>
            {specsEntries.length > 0 ? (
              <dl className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
                {specsEntries.map(([key, value]) => (
                  <div key={key} className="flex flex-col space-y-1">
                    <dt className="text-muted-foreground">{key}</dt>
                    <dd className="font-medium text-foreground">{String(value)}</dd>
                  </div>
                ))}
              </dl>
            ) : (
              <p className="text-sm text-muted-foreground italic">
                No specifications available.
              </p>
            )}
          </section>
        </div>

        {/* Right Column: Pricing & Inventory */}
        <div className="space-y-6">
          <section className="rounded-lg border border-border bg-card p-6 space-y-6">
            <div>
              <p className="text-sm text-muted-foreground mb-1">Pricing</p>
              <p className="text-3xl font-bold text-foreground">
                {formatCurrency(product.price)}
              </p>
            </div>

            <div className="border-t border-border pt-4">
              <p className="text-sm text-muted-foreground mb-2 flex items-center gap-2">
                <Box className="h-4 w-4" /> Inventory Status
              </p>
              <div className="flex items-center justify-between">
                <span className="font-medium text-foreground">Stock Level</span>
                <span
                  className={`font-semibold ${
                    product.stock === 0
                      ? "text-destructive"
                      : product.stock < 10
                      ? "text-amber-600 dark:text-amber-400"
                      : "text-green-600 dark:text-green-500"
                  }`}
                >
                  {product.stock === 0 ? "Out of Stock" : product.stock}
                </span>
              </div>
            </div>

            <div className="border-t border-border pt-4 space-y-2">
              <div className="flex items-center justify-between text-xs text-muted-foreground">
                <span className="flex items-center gap-1"><Hash className="h-3 w-3"/> System ID</span>
                <span className="font-mono">{product.id}</span>
              </div>
              <div className="flex items-center justify-between text-xs text-muted-foreground">
                <span>Added</span>
                <span>{formatDate(product.created_at)}</span>
              </div>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}

export default function ProductDetailsPage({ params }: ProductDetailsPageProps) {
  // Use React.use() to unwrap the Promise for params in Next.js 15+ App Router
  const resolvedParams = use(params);
  
  return (
    <Suspense fallback={<LoadingSkeleton variant="kpi" />}>
      <ProductDetailsContent productId={resolvedParams.productId} />
    </Suspense>
  );
}
