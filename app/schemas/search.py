# ============================================================
# IDAM — Intelligent Automated Retail Store Backend
# app/schemas/search.py
#
# PURPOSE:
#   Pydantic request and response models for the semantic
#   search endpoints.
#
# SCHEMAS:
#   SemanticSearchResponse — the full search result payload
#   SearchResultItem       — one product result + its similarity score
#   IndexStatusResponse    — how many products are indexed + model info
#   IndexAllResponse       — result of a full re-index operation
#   SingleIndexResponse    — result of indexing one product
# ============================================================

from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field


# ── Search result item ────────────────────────────────────────

class SearchResultItem(BaseModel):
    """
    Represents a single product in semantic search results.

    Includes both the product data and its relevance score
    so the caller can optionally filter by min_score or
    display confidence to the user.
    """

    rank: int = Field(
        ...,
        description="1-based ranking position (1 = most relevant)"
    )

    product_id: str = Field(
        ...,
        description="Unique product identifier, e.g. PROD003"
    )

    name: str = Field(
        ...,
        description="Product name"
    )

    category: str = Field(
        ...,
        description="Product category, e.g. Laptops"
    )

    brand: str = Field(
        default="",
        description="Product brand"
    )

    price: float = Field(
        ...,
        description="Product price in INR"
    )

    stock: int = Field(
        default=0,
        description="Available stock units"
    )

    description: Optional[str] = Field(
        default=None,
        description="Full product description"
    )

    specifications: Dict[str, Any] = Field(
        default={},
        description="Product specifications as key-value pairs"
    )

    tags: List[str] = Field(
        default=[],
        description="Semantic tags for this product"
    )

    similarity_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description=(
            "Semantic similarity score (0.0 = unrelated, 1.0 = identical). "
            "Computed as 1 - cosine_distance from ChromaDB."
        )
    )


# ── Search response ──────────────────────────────────────────

class SemanticSearchResponse(BaseModel):
    """
    Full response for GET /search/semantic.
    """

    query: str = Field(
        ...,
        description="The original search query string"
    )

    total: int = Field(
        ...,
        description="Number of results returned"
    )

    results: List[SearchResultItem] = Field(
        ...,
        description="Ranked list of matching products, most relevant first"
    )

    model_used: str = Field(
        ...,
        description="Embedding model used for this search, e.g. all-MiniLM-L6-v2"
    )


# ── Index status ─────────────────────────────────────────────

class IndexStatusResponse(BaseModel):
    """
    Response for GET /search/status.
    Shows how many products are currently indexed and model info.
    """

    status: str = Field(
        ...,
        description="'ready' if indexed products > 0, 'empty' otherwise"
    )

    indexed_count: int = Field(
        ...,
        description="Number of products currently stored in ChromaDB"
    )

    model: str = Field(
        ...,
        description="Embedding model currently loaded"
    )

    vector_dimensions: int = Field(
        ...,
        description="Dimensions of each embedding vector (384 for all-MiniLM-L6-v2)"
    )

    chroma_path: str = Field(
        ...,
        description="Filesystem path where ChromaDB data is stored"
    )


# ── Full index response ───────────────────────────────────────

class IndexAllResponse(BaseModel):
    """
    Response for POST /search/index (full catalog re-index).
    """

    success: bool = Field(
        ...,
        description="True if indexing completed without critical failure"
    )

    indexed: int = Field(
        ...,
        description="Number of products successfully embedded and stored"
    )

    skipped: int = Field(
        default=0,
        description="Number of products skipped (e.g. missing required fields)"
    )

    errors: int = Field(
        default=0,
        description="Number of products that failed to index"
    )

    error_details: List[str] = Field(
        default=[],
        description="Error messages for any failed products (for debugging)"
    )

    message: str = Field(
        ...,
        description="Human-readable summary of the indexing operation"
    )


# ── Single product index response ────────────────────────────

class SingleIndexResponse(BaseModel):
    """
    Response for POST /search/index/{product_id} (single product index).
    """

    success: bool = Field(
        ...,
        description="True if the product was indexed successfully"
    )

    product_id: str = Field(
        ...,
        description="The product that was indexed"
    )

    message: str = Field(
        ...,
        description="Human-readable result message"
    )

    error: Optional[str] = Field(
        default=None,
        description="Error detail if indexing failed"
    )
