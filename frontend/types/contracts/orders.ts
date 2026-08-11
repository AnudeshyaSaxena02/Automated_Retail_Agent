// ============================================================
// types/contracts/orders.ts
//
// TypeScript contracts derived from the ACTUAL FastAPI backend
// schemas in app/schemas/order.py.
//
// BACKEND SOURCE:
//   PurchaseRequest      → PurchaseRequest
//   MemoryUpdateSummary  → MemoryUpdateSummary
//   PurchaseResponse     → PurchaseResponse
//
// Keep in sync with app/schemas/order.py.
// ============================================================

// ── Request body for POST /orders/purchase ────────────────────

export interface PurchaseRequest {
  /** The customer making the purchase, e.g. "CUST001". */
  customer_id: string;
  /** The product being purchased, e.g. "PROD001". */
  product_id: string;
  /** Number of units. Range: 1–100. Defaults to 1. */
  quantity?: number;
}

// ── What the memory engine learned from this purchase ─────────

export interface MemoryUpdateSummary {
  total_purchases: number;
  total_spend: number;
  purchased_categories: string[];
  preferred_brands: string[];
  category_interests: string[];
  monthly_pattern: Record<string, unknown>;
  /** "start of month" | "mid month" | "end of month" */
  budget_period: string;
  /** Current estimated budget ceiling in INR. */
  estimated_budget: number;
}

// ── Response from POST /orders/purchase ───────────────────────

export interface PurchaseResponse {
  success: boolean;
  message: string;
  order_id: number;
  customer_id: string;
  product_id: string;
  product_name: string;
  quantity: number;
  /** Price paid at time of purchase in INR. */
  price_paid: number;
  purchased_at: string; // ISO 8601 datetime string
  memory_updated: MemoryUpdateSummary;
}
