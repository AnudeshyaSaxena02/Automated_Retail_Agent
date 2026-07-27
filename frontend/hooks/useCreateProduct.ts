// ============================================================
// hooks/useCreateProduct.ts
//
// TanStack Query hook for POST /products.
// Includes success/error handling with sonner toasts.
// ============================================================

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { createProduct } from "@/services/productService";
import { indexSingleProduct } from "@/services/searchService";
import type { ProductCreateRequest, Product } from "@/types/contracts/products";
import { extractApiError } from "@/types/api";
import { toast } from "sonner";

export function useCreateProduct() {
  const queryClient = useQueryClient();

  return useMutation<Product, Error, ProductCreateRequest>({
    mutationFn: async (requestData) => {
      // 1. Create product
      const product = await createProduct(requestData);
      
      // 2. Index product
      try {
        await indexSingleProduct(product.product_id);
        toast.success("Product created successfully", {
          description: `${product.name} (${product.product_id}) has been added to the catalog and search index.`,
        });
      } catch (error) {
        const apiError = extractApiError(error as Error);
        toast.warning("Product created, but indexing failed", {
          description: `Product ${product.product_id} was added, but search index failed: ${apiError.message}`,
        });
      }
      
      return product;
    },
    onSuccess: () => {
      // Invalidate count, list, and search status to ensure UI reflects changes
      queryClient.invalidateQueries({ queryKey: ["product-count"] });
      queryClient.invalidateQueries({ queryKey: ["products"] });
      queryClient.invalidateQueries({ queryKey: ["search-status"] });
    },
    onError: (error) => {
      const apiError = extractApiError(error);
      toast.error("Failed to create product", {
        description: apiError.message,
      });
    },
  });
}
