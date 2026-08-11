"use client";

// ============================================================
// components/products/ProductTable.tsx
//
// Displays a list of products in a table format.
// Handles clicking a row to navigate to details.
// ============================================================

import { useRouter } from "next/navigation";
import { formatCurrency } from "@/utils/formatCurrency";
import type { Product } from "@/types/contracts/products";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";

interface ProductTableProps {
  products: Product[];
}

export function ProductTable({ products }: ProductTableProps) {
  const router = useRouter();

  if (products.length === 0) {
    return null; // Parent handles empty state
  }

  return (
    <div className="rounded-md border border-border bg-card">
      <Table>
        <TableHeader>
          <TableRow className="bg-muted/30">
            <TableHead className="w-[120px]">Product ID</TableHead>
            <TableHead>Name</TableHead>
            <TableHead>Category</TableHead>
            <TableHead>Brand</TableHead>
            <TableHead className="text-right">Price</TableHead>
            <TableHead className="text-right">Stock</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {products.map((product) => (
            <TableRow
              key={product.product_id}
              className="cursor-pointer hover:bg-muted/50"
              onClick={() => router.push(`/products/${product.product_id}`)}
              role="button"
              tabIndex={0}
              aria-label={`View details for ${product.name}`}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") {
                  e.preventDefault();
                  router.push(`/products/${product.product_id}`);
                }
              }}
            >
              <TableCell className="font-mono text-xs text-muted-foreground">
                {product.product_id}
              </TableCell>
              <TableCell className="font-medium">{product.name}</TableCell>
              <TableCell>
                <Badge variant="secondary" className="font-normal">
                  {product.category}
                </Badge>
              </TableCell>
              <TableCell className="text-muted-foreground">
                {product.brand || "—"}
              </TableCell>
              <TableCell className="text-right font-medium">
                {formatCurrency(product.price)}
              </TableCell>
              <TableCell className="text-right">
                <span
                  className={
                    product.stock === 0
                      ? "text-destructive font-medium"
                      : product.stock < 10
                      ? "text-amber-600 dark:text-amber-400 font-medium"
                      : "text-muted-foreground"
                  }
                >
                  {product.stock === 0 ? "Out of Stock" : product.stock}
                </span>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
