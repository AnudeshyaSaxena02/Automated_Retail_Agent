// ============================================================
// types/contracts/products.ts
//
// TypeScript contracts derived from the ACTUAL FastAPI backend
// schemas in app/schemas/product.py.
//
// BACKEND SOURCE:
//   ProductCreate        → ProductCreateRequest
//   ProductResponse      → Product
//   ProductListResponse  → ProductListResponse
//
// Keep in sync with app/schemas/product.py.
// ============================================================

// ── Request body for POST /products ──────────────────────────

export interface ProductCreateRequest {
  product_id: string;
  name: string;
  description?: string | null;
  category: string;
  brand?: string | null;
  /** Price in INR. Must be > 0. */
  price: number;
  /** Defaults to 100 on the backend. */
  stock?: number;
  specifications?: Record<string, unknown>;
  tags?: string[];
}

// ── Single product — GET /products/{id}, POST /products ───────

export interface Product {
  /** Auto-incremented database row ID. */
  id: number;
  /** Application-level unique identifier, e.g. "PROD001". */
  product_id: string;
  name: string;
  description: string | null;
  category: string;
  brand: string | null;
  /** Price in INR. */
  price: number;
  stock: number;
  specifications: Record<string, unknown>;
  tags: string[];
  created_at: string; // ISO 8601 datetime string
}

// ── Paginated list — GET /products ───────────────────────────

export interface ProductListResponse {
  total: number;
  products: Product[];
}
