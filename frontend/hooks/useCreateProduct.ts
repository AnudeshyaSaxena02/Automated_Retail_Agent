// ============================================================
// hooks/useCreateProduct.ts
//
// TanStack Query hook for POST /products.
// Includes success/error handling with sonner toasts.
// ============================================================

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { createProduct } from "@/services/productService";
import type { ProductCreateRequest, Product } from "@/types/contracts/products";
import { extractApiError } from "@/types/api";
import { toast } from "sonner";

export function useCreateProduct() {
  const queryClient = useQueryClient();

  return useMutation<Product, Error, ProductCreateRequest>({
    mutationFn: createProduct,
    onSuccess: (data) => {
      toast.success("Product created successfully", {
        description: `${data.name} (${data.product_id}) has been added to the catalog.`,
      });
      // Invalidate both count and list queries to ensure dashboard and catalog reflect changes
      queryClient.invalidateQueries({ queryKey: ["product-count"] });
      queryClient.invalidateQueries({ queryKey: ["products"] });
    },
    onError: (error) => {
      const apiError = extractApiError(error);
      toast.error("Failed to create product", {
        description: apiError.message,
      });
    },
  });
}
