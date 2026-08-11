"use client";

// ============================================================
// components/ai/ChatProductCard.tsx
// ============================================================

import { useRouter } from "next/navigation";
import { formatCurrency } from "@/utils/formatCurrency";
import { Card, CardContent, CardFooter, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { ChatProductItem } from "@/types/contracts/chat";

interface ChatProductCardProps {
  product: ChatProductItem;
}

export function ChatProductCard({ product }: ChatProductCardProps) {
  const router = useRouter();

  const score = product.final_score ?? product.similarity_score;
  let scoreColor = "text-muted-foreground";
  if (score !== null) {
    if (score >= 0.8) scoreColor = "text-green-600 dark:text-green-400";
    else if (score >= 0.5) scoreColor = "text-amber-600 dark:text-amber-400";
  }

  return (
    <Card 
      className="flex flex-col cursor-pointer hover:border-primary/50 transition-colors w-[260px] shrink-0 h-full"
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
      <CardHeader className="p-3 pb-1">
        <div className="flex justify-between items-start gap-1">
          <h3 className="font-semibold text-sm leading-tight line-clamp-2">
            {product.name}
          </h3>
          {score !== null && (
            <Badge variant="outline" className={`shrink-0 ${scoreColor} font-mono text-[10px] border-current px-1`}>
              {(score * 100).toFixed(0)}%
            </Badge>
          )}
        </div>
      </CardHeader>

      <CardContent className="p-3 pt-1 flex-grow">
        <p className="text-xs text-muted-foreground line-clamp-3 mb-2">
          {product.reason || "Matched based on your query context."}
        </p>
        <div className="flex flex-wrap gap-1">
          <Badge variant="secondary" className="text-[10px]">{product.category}</Badge>
          {product.brand && (
            <Badge variant="outline" className="text-[10px] text-muted-foreground border-border">
              {product.brand}
            </Badge>
          )}
        </div>
      </CardContent>

      <CardFooter className="p-3 pt-0 flex justify-between items-end">
        <div>
          <p className="font-mono text-[10px] text-muted-foreground mb-1">{product.product_id}</p>
          <p className="text-sm font-bold">{formatCurrency(product.price)}</p>
        </div>
        <div className="text-right">
          <p className={`text-[10px] font-medium ${product.stock > 0 ? "text-muted-foreground" : "text-destructive"}`}>
            {product.stock > 0 ? `${product.stock} left` : "Out of stock"}
          </p>
        </div>
      </CardFooter>
    </Card>
  );
}
