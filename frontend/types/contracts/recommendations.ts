// ============================================================
// types/contracts/recommendations.ts
//
// TypeScript contracts derived from the ACTUAL FastAPI backend
// schemas in app/schemas/recommendation.py.
//
// BACKEND SOURCE:
//   RecommendationRequest    → RecommendationRequest
//   RecommendedProductItem   → RecommendedProductItem
//   RecommendationResponse   → RecommendationResponse
//
// Keep in sync with app/schemas/recommendation.py.
// ============================================================

// ── Request body for POST /recommendations/{customer_id} ──────

export interface RecommendationRequest {
  /**
   * Optional natural-language intent.
   * If omitted, recommendations are driven by purchase history only.
   * Min 2 chars, max 500 chars.
   */
  query?: string | null;
  /**
   * Number of recommendations to return (1–50).
   * Defaults to RECOMMENDATION_TOP_K from backend settings (10).
   */
  top_k?: number | null;
}

// ── One recommended product with full score breakdown ─────────

export interface RecommendedProductItem {
  /** Rank position (1 = highest score). */
  rank: number;
  product_id: string;
  name: string;
  category: string;
  brand: string;
  /** Price in INR. */
  price: number;
  stock: number;
  /** Weighted composite score (0.0–1.0). Higher is better. */
  final_score: number;
  /** How well the product matches category interests, brands, and tags. Weight: 35%. */
  interest_score: number;
  /** Cosine similarity between query embedding and product embedding. Weight: 25%. */
  semantic_score: number;
  /** How well price fits the estimated monthly budget. Weight: 20%. */
  budget_score: number;
  /** Shopping frequency in this product's category. Weight: 10%. */
  frequency_score: number;
  /** Relative purchase count across all customers. Weight: 10%. */
  popularity_score: number;
  /** Auto-generated explanation of why this product was recommended. */
  reason: string;
}

// ── Full response — POST /recommendations/{customer_id} ───────

export interface RecommendationResponse {
  customer_id: string;
  customer_name: string;
  /** Estimated budget for the current period in INR. 0.0 = no history. */
  estimated_budget: number;
  /** "start of month" | "mid month" | "end of month" */
  budget_period: string;
  /** Query used for semantic candidate retrieval. Null if no query provided. */
  query_used: string | null;
  total_recommended: number;
  recommended_products: RecommendedProductItem[];
}
