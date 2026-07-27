"use client";

// ============================================================
// components/products/SemanticProductCard.tsx
// ============================================================

import { useRouter } from "next/navigation";
import { formatCurrency } from "@/utils/formatCurrency";
import { Card, CardContent, CardFooter, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { SearchResultItem } from "@/types/contracts/search";

interface SemanticProductCardProps {
  product: SearchResultItem;
}

export function SemanticProductCard({ product }: SemanticProductCardProps) {
  const router = useRouter();

  // Color-code the similarity score
  const score = product.similarity_score;
  const scoreColor = 
    score >= 0.8 ? "text-green-600 dark:text-green-400" :
    score >= 0.5 ? "text-amber-600 dark:text-amber-400" :
    "text-muted-foreground";

  return (
    <Card 
      className="flex flex-col cursor-pointer hover:border-primary/50 transition-colors"
      onClick={() => router.push(`/products/${product.product_id}`)}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          router.push(`/products/${product.product_id}`);
        }
      }}
    >
      <CardHeader className="p-4 pb-2">
        <div className="flex justify-between items-start gap-2">
          <h3 className="font-semibold text-lg leading-tight line-clamp-2">{product.name}</h3>
          <Badge variant="outline" className={`shrink-0 ${scoreColor} font-mono text-xs border-current`}>
            {(score * 100).toFixed(1)}% Match
          </Badge>
        </div>
        <div className="flex flex-wrap gap-1 mt-2">
          <Badge variant="secondary" className="text-xs">{product.category}</Badge>
          {product.brand && (
            <Badge variant="outline" className="text-xs text-muted-foreground border-border">
              {product.brand}
            </Badge>
          )}
        </div>
      </CardHeader>

      <CardContent className="p-4 pt-2 flex-grow">
        <p className="text-sm text-muted-foreground line-clamp-3">
          {product.description || "No description available."}
        </p>
      </CardContent>

      <CardFooter className="p-4 pt-0 flex justify-between items-end">
        <div>
          <p className="font-mono text-xs text-muted-foreground mb-1">ID: {product.product_id}</p>
          <p className="text-xl font-bold">{formatCurrency(product.price)}</p>
        </div>
        <div className="text-right">
          <p className={`text-xs font-medium ${product.stock > 0 ? "text-muted-foreground" : "text-destructive"}`}>
            {product.stock > 0 ? `${product.stock} in stock` : "Out of stock"}
          </p>
        </div>
      </CardFooter>
    </Card>
  );
}
