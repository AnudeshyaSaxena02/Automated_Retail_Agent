// ============================================================
// types/contracts/chat.ts
//
// TypeScript contracts derived from the ACTUAL FastAPI backend
// schemas in app/schemas/chat.py.
//
// BACKEND SOURCE:
//   ChatRequest      → ChatRequest
//   ChatProductItem  → ChatProductItem
//   ChatResponse     → ChatResponse
//
// Keep in sync with app/schemas/chat.py.
// ============================================================

// ── Request body for POST /chat/{customer_id} ────────────────

export interface ChatRequest {
  /**
   * Natural-language message from the customer.
   * Min 2 chars, max 1000 chars.
   */
  message: string;
}

// ── One product in the chat response ─────────────────────────

export interface ChatProductItem {
  product_id: string;
  name: string;
  category: string;
  brand: string;
  /** Price in INR. */
  price: number;
  stock: number;
  /**
   * Cosine similarity score from ChromaDB.
   * Only present for semantic search results.
   */
  similarity_score: number | null;
  /**
   * Weighted recommendation score.
   * Only present for recommendation engine results.
   */
  final_score: number | null;
  /**
   * Auto-generated reason this product was recommended.
   * Only present for recommendation engine results.
   */
  reason: string | null;
}

// ── Full response — POST /chat/{customer_id} ──────────────────

export interface ChatResponse {
  customer_id: string;
  /**
   * Detected intent label.
   * One of: "product_search" | "product_details" | "recommendation" |
   * "product_comparison" | "customer_history" | "order_history" |
   * "budget_query" | "general_chat"
   */
  intent: string;
  /** LLM provider that generated the response: "groq" or "gemini". */
  provider: string;
  /** The LLM's conversational response to the customer's message. */
  response: string;
  /**
   * Products included in the response.
   * Empty for order_history, customer_history, and general_chat intents.
   */
  products: ChatProductItem[];
  /**
   * Additional context. May include:
   * - budget_detected (number)
   * - intent_confidence (number)
   * - rag_used (boolean)
   * - total_products (number)
   */
  metadata: Record<string, unknown>;
}
