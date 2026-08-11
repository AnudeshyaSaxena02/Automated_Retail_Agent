// ============================================================
// hooks/useProducts.ts
//
// TanStack Query hook for GET /products with filters.
// ============================================================

import { useQuery } from "@tanstack/react-query";
import { getProducts, type GetProductsParams } from "@/services/productService";
import type { ProductListResponse } from "@/types/contracts/products";

export function useProducts(params: GetProductsParams, enabled: boolean = true) {
  return useQuery<ProductListResponse, Error>({
    queryKey: ["products", params],
    queryFn: () => getProducts(params),
    staleTime: 60_000,
    gcTime: 5 * 60_000,
    retry: 1,
    refetchOnWindowFocus: false,
    enabled,
  });
}
