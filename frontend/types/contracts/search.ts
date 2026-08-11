// ============================================================
// types/contracts/search.ts
//
// TypeScript contracts derived from the ACTUAL FastAPI backend
// schemas in app/schemas/search.py.
//
// BACKEND SOURCE:
//   SearchResultItem      → SearchResultItem
//   SemanticSearchResponse → SemanticSearchResponse
//   IndexStatusResponse   → IndexStatusResponse
//   IndexAllResponse      → IndexAllResponse
//   SingleIndexResponse   → SingleIndexResponse
//
// Keep in sync with app/schemas/search.py.
// ============================================================

// ── One product in search results ────────────────────────────

export interface SearchResultItem {
  /** 1-based ranking position (1 = most relevant). */
  rank: number;
  product_id: string;
  name: string;
  category: string;
  brand: string;
  /** Price in INR. */
  price: number;
  stock: number;
  description: string | null;
  specifications: Record<string, unknown>;
  tags: string[];
  /**
   * Semantic similarity score (0.0 = unrelated, 1.0 = identical).
   * Computed as 1 - cosine_distance from ChromaDB.
   */
  similarity_score: number;
}

// ── Full response — GET /search/semantic ─────────────────────

export interface SemanticSearchResponse {
  /** The original search query string. */
  query: string;
  total: number;
  results: SearchResultItem[];
  /** Embedding model used, e.g. "all-MiniLM-L6-v2". */
  model_used: string;
}

// ── Index status — GET /search/status ────────────────────────

export interface IndexStatusResponse {
  /** "ready" if indexed_count > 0, "empty" otherwise. */
  status: string;
  indexed_count: number;
  model: string;
  /** Dimensions of each embedding vector (384 for all-MiniLM-L6-v2). */
  vector_dimensions: number;
  chroma_path: string;
}

// ── Full index — POST /search/index ──────────────────────────

export interface IndexAllResponse {
  success: boolean;
  indexed: number;
  skipped: number;
  errors: number;
  error_details: string[];
  message: string;
}

// ── Single product index — POST /search/index/{product_id} ───

export interface SingleIndexResponse {
  success: boolean;
  product_id: string;
  message: string;
  error: string | null;
}
