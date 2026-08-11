// ============================================================
// types/contracts/llm.ts
//
// TypeScript contracts derived from the ACTUAL FastAPI backend
// schemas in app/schemas/llm.py.
//
// BACKEND SOURCE:
//   LLMQueryRequest   → LLMQueryRequest
//   LLMQueryResponse  → LLMQueryResponse
//   RAGQueryRequest   → RAGQueryRequest
//   RAGProductItem    → RAGProductItem
//   RAGQueryResponse  → RAGQueryResponse
//   LLMErrorResponse  → LLMErrorResponse
//
// Keep in sync with app/schemas/llm.py.
// ============================================================

// ── POST /llm/query — Request ─────────────────────────────────

export interface LLMQueryRequest {
  /**
   * Natural-language query to send to the LLM.
   * Min 2 chars, max 2000 chars.
   */
  query: string;
  /**
   * Optional customer ID for personalised responses (Phase 8+).
   */
  customer_id?: string | null;
}

// ── POST /llm/query — Response ────────────────────────────────

export interface LLMQueryResponse {
  /** The LLM's conversational response to the query. */
  response: string;
  /** LLM provider used: "Groq" or "Gemini". */
  provider: string;
}

// ── POST /llm/rag-query — Request ────────────────────────────

export interface RAGQueryRequest {
  /**
   * Natural-language product query.
   * The system will search the catalog and inject results into the LLM context.
   * Min 2 chars, max 2000 chars.
   */
  query: string;
  /**
   * Number of products to retrieve from ChromaDB (1–20).
   * Defaults to RAG_TOP_K from backend settings (5).
   */
  top_k?: number | null;
  /**
   * Minimum similarity score for retrieved products (0.0–1.0).
   * Defaults to SIMILARITY_THRESHOLD from backend settings (0.3).
   */
  min_score?: number | null;
  /**
   * Optional customer ID for personalised responses (Phase 8).
   */
  customer_id?: string | null;
}

// ── One product retrieved from ChromaDB and shown to the LLM ─

export interface RAGProductItem {
  /** Retrieval rank (1 = most relevant). */
  rank: number;
  product_id: string;
  name: string;
  category: string;
  brand: string;
  /** Price in INR. */
  price: number;
  stock: number;
  /** Semantic similarity score (0.0–1.0). */
  similarity_score: number;
}

// ── POST /llm/rag-query — Response ───────────────────────────

export interface RAGQueryResponse {
  /** The LLM's response, grounded in real catalog products. */
  response: string;
  /** LLM provider used: "Groq" or "Gemini". */
  provider: string;
  /**
   * True if real catalog products were injected into the prompt.
   * False if no matching products were found (graceful fallback).
   */
  rag_used: boolean;
  /** Number of products retrieved from ChromaDB. */
  products_retrieved: number;
  /** Products that were retrieved and shown to the LLM. */
  products: RAGProductItem[];
}

// ── Standardised error from LLM endpoints ────────────────────

export interface LLMErrorResponse {
  detail: string;
}
