// ============================================================
// types/contracts/customers.ts
//
// TypeScript contracts derived from the ACTUAL FastAPI backend
// schemas in app/schemas/customer.py.
//
// BACKEND SOURCE:
//   CustomerResponse        → Customer
//   CustomerListResponse    → CustomerListResponse
//   CustomerMemoryResponse  → CustomerMemory
//   OrderItemResponse       → CustomerOrderItem
//   CustomerOrdersResponse  → CustomerOrdersResponse
//
// Keep in sync with app/schemas/customer.py.
// ============================================================

// ── Basic customer profile — GET /customers/{customer_id} ────

export interface Customer {
  /** Auto-incremented database row ID. */
  id: number;
  /** Application-level unique identifier, e.g. "CUST001". */
  customer_id: string;
  name: string;
  email: string | null;
  created_at: string; // ISO 8601 datetime string
}

// ── Paginated list — GET /customers ──────────────────────────

export interface CustomerListResponse {
  total: number;
  customers: Customer[];
}

// ── AI memory — GET /customers/{customer_id}/memory ──────────

export interface CustomerMemory {
  customer_id: string;
  purchased_categories: string[];
  preferred_brands: string[];
  favorite_products: string[];
  total_purchases: number;
  total_spend: number;
  /** Average spend on days 1–10 of the month. */
  avg_budget_start: number;
  /** Average spend on days 11–20 of the month. */
  avg_budget_mid: number;
  /** Average spend on days 21–31 of the month. */
  avg_budget_end: number;
  monthly_pattern: Record<string, unknown>;
  category_interests: string[];
  visit_count: number;
  last_visit: string | null; // ISO 8601 or null
  updated_at: string | null; // ISO 8601 or null
  /**
   * Estimated budget for the current date + spending history.
   * Computed by the backend service layer.
   */
  current_budget_estimate: number | null;
}

// ── Single order item — used inside CustomerOrdersResponse ───

export interface CustomerOrderItem {
  /** Auto-incremented row ID for the order. */
  id: number;
  product_id: string;
  /** Joined from products table. May be null if product was deleted. */
  product_name: string | null;
  product_category: string | null;
  product_brand: string | null;
  quantity: number;
  /** Price paid at time of purchase in INR. */
  price_paid: number;
  purchased_at: string; // ISO 8601 datetime string
}

// ── Order history — GET /customers/{customer_id}/orders ───────

export interface CustomerOrdersResponse {
  customer_id: string;
  customer_name: string;
  total_orders: number;
  total_spend: number;
  orders: CustomerOrderItem[];
}
