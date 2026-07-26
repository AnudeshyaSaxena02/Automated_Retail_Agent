// ============================================================
// hooks/useProductCount.ts
//
// TanStack Query wrapper for GET /products?limit=1 → total.
// Used by Dashboard KPI card "Products in Catalog".
//
// Query key: ["product-count"]
// Stale time: 60s
// ============================================================

import { useQuery } from "@tanstack/react-query";
import { getProductCount } from "@/services/productService";

export function useProductCount() {
  return useQuery<number, Error>({
    queryKey: ["product-count"],
    queryFn: getProductCount,
    staleTime: 60_000,
    gcTime: 5 * 60_000,
    retry: 1,
    refetchOnWindowFocus: false,
  });
}
