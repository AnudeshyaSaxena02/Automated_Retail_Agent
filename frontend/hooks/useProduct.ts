// ============================================================
// hooks/useProduct.ts
//
// TanStack Query hook for GET /products/{productId}.
// ============================================================

import { useQuery } from "@tanstack/react-query";
import { getProduct } from "@/services/productService";
import type { Product } from "@/types/contracts/products";

export function useProduct(productId: string) {
  return useQuery<Product, Error>({
    queryKey: ["product", productId],
    queryFn: () => getProduct(productId),
    staleTime: 60_000,
    gcTime: 5 * 60_000,
    retry: 1,
    refetchOnWindowFocus: false,
    enabled: !!productId,
  });
}
