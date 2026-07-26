// ============================================================
// services/productService.ts
//
// Phase 2 scope: product count only.
// Full product CRUD/search services added in Phase 3.
//
// Endpoint:
//   GET /products?limit=1&offset=0 → ProductListResponse
//
// VERIFIED: The backend computes `total` via query.count() BEFORE
// applying limit/offset (product_service.py L60). Using limit=1
// to derive count is safe — total reflects the full catalog.
// ============================================================

import { apiClient } from "@/lib/api-client";

interface ProductCountResponse {
  total: number;
  products: unknown[];
}

export async function getProductCount(): Promise<number> {
  const response = await apiClient.get<ProductCountResponse>("/products", {
    params: { limit: 1, offset: 0 },
  });
  return response.data.total;
}
