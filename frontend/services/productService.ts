// ============================================================
// services/productService.ts
//
// Phase 3 scope: Product catalog list, search, details, creation.
// Phase 2 scope: product count.
// ============================================================

import { apiClient } from "@/lib/api-client";
import type { 
  ProductListResponse, 
  Product, 
  ProductCreateRequest 
} from "@/types/contracts/products";

// ── Phase 2: Product Count ────────────────────────────────────
// Used by Dashboard KPI card
export async function getProductCount(): Promise<number> {
  const response = await apiClient.get<ProductListResponse>("/products", {
    params: { limit: 1, offset: 0 },
  });
  return response.data.total;
}

// ── Phase 3: Product Catalog ──────────────────────────────────

export interface GetProductsParams {
  category?: string;
  brand?: string;
  min_price?: number;
  max_price?: number;
  limit?: number;
  offset?: number;
}

export async function getProducts(params: GetProductsParams = {}): Promise<ProductListResponse> {
  const response = await apiClient.get<ProductListResponse>("/products", { params });
  return response.data;
}

export async function getProduct(productId: string): Promise<Product> {
  const response = await apiClient.get<Product>(`/products/${productId}`);
  return response.data;
}

export async function searchProducts(q: string, limit: number = 20): Promise<ProductListResponse> {
  const response = await apiClient.get<ProductListResponse>("/products/search", {
    params: { q, limit },
  });
  return response.data;
}

export async function createProduct(data: ProductCreateRequest): Promise<Product> {
  const response = await apiClient.post<Product>("/products", data);
  return response.data;
}
