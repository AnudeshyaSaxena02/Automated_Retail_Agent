// ============================================================
// hooks/useProductSearch.ts
//
// TanStack Query hook for GET /products/search.
// ============================================================

import { useQuery } from "@tanstack/react-query";
import { searchProducts } from "@/services/productService";
import type { ProductListResponse } from "@/types/contracts/products";

export function useProductSearch(q: string, limit: number = 20, enabled: boolean = true) {
  return useQuery<ProductListResponse, Error>({
    queryKey: ["products", "search", q, limit],
    queryFn: () => searchProducts(q, limit),
    staleTime: 60_000,
    gcTime: 5 * 60_000,
    retry: 1,
    refetchOnWindowFocus: false,
    enabled: enabled && q.trim().length > 0,
  });
}
