# ============================================================
# IDAM — Intelligent Automated Retail Store Backend
# app/api/search.py
#
# PURPOSE:
#   FastAPI router for all semantic search endpoints.
#   Routes are thin — they only handle HTTP concerns
#   (query params, status codes, error responses).
#   All logic lives in search_service.py and product_index.py.
#
# ENDPOINTS:
#   GET  /search/semantic              — Run semantic search
#   GET  /search/status                — Check index status
#   POST /search/index                 — Re-index all products
#   POST /search/index/{product_id}    — Index a single product
# ============================================================

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.config.settings import settings
from app.services.search_service import semantic_search, get_search_status
from app.ai.vectordb.product_index import index_all_products, index_single_product
from app.schemas.search import (
    SemanticSearchResponse,
    IndexStatusResponse,
    IndexAllResponse,
    SingleIndexResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# ── GET /search/semantic ──────────────────────────────────────

@router.get(
    "/semantic",
    response_model=SemanticSearchResponse,
    summary="Semantic product search",
    description=(
        "Search products using natural-language queries. "
        "Returns semantically relevant products even when exact keywords are absent. "
        "Powered by sentence-transformers (all-MiniLM-L6-v2) + ChromaDB vector similarity."
    ),
)
def semantic_search_endpoint(
    q: str = Query(
        ...,
        min_length=2,
        description="Natural-language search query. Examples: 'gaming laptop for AI', 'wireless headphones with good battery'",
        example="I need a gaming laptop for AI development",
    ),
    limit: int = Query(
        default=10,
        ge=1,
        le=50,
        description="Maximum number of results to return (1–50)",
    ),
    min_score: float = Query(
        default=settings.similarity_threshold,
        ge=0.0,
        le=1.0,
        description=(
            "Minimum similarity score threshold (0.0–1.0). "
            "Results below this score are excluded. "
            f"Server default is {settings.similarity_threshold} (set via SIMILARITY_THRESHOLD in .env). "
            "Override per-request: use 0.0 to disable filtering, 0.5 for strict matching."
        ),
    ),
    db: Session = Depends(get_db),
):
    """
    Run a semantic search against the product catalog.

    Unlike keyword search (`/products/search`), this endpoint understands
    meaning — not just literal text matches.

    **Query examples that work:**
    - `"I need a gaming laptop for AI"` → finds laptops with GPU/AI/gaming tags
    - `"Show me lightweight laptops"` → finds ultrabooks and thin laptops
    - `"I want wireless headphones with good battery"` → finds Bluetooth audio gear

    **How it works:**
    1. Your query is converted to a 384-dimensional vector
    2. ChromaDB finds the most similar product vectors (cosine similarity)
    3. Full product data is fetched from SQLite and returned with scores

    **similarity_score:** 1.0 = exact match, 0.0 = totally unrelated
    """
    try:
        response = semantic_search(
            db        = db,
            query     = q,
            limit     = limit,
            min_score = min_score,
        )
        return response

    except RuntimeError as exc:
        # ChromaDB not initialized or embedding model not loaded
        logger.error(f"[Search API] Runtime error during semantic search: {exc}")
        raise HTTPException(
            status_code=503,
            detail=(
                "Semantic search is not available. "
                "The index may not be initialized yet. "
                "Try POST /search/index to index the catalog first."
            ),
        )
    except Exception as exc:
        logger.error(f"[Search API] Unexpected error during semantic search: {exc}")
        raise HTTPException(
            status_code=500,
            detail=f"Semantic search failed: {str(exc)}",
        )


# ── GET /search/status ────────────────────────────────────────

@router.get(
    "/status",
    response_model=IndexStatusResponse,
    summary="Check semantic search index status",
    description="Returns the number of indexed products, the embedding model in use, and the ChromaDB storage path.",
)
def index_status():
    """
    Check whether the product index is ready for semantic search.

    Returns:
    - `status`: `"ready"` if products are indexed, `"empty"` if not
    - `indexed_count`: Number of products currently in ChromaDB
    - `model`: Embedding model name
    - `vector_dimensions`: Size of each embedding vector
    - `chroma_path`: Filesystem path where ChromaDB stores its data

    If `status` is `"empty"`, call `POST /search/index` to build the index.
    """
    try:
        return get_search_status()
    except Exception as exc:
        logger.error(f"[Search API] Failed to get index status: {exc}")
        raise HTTPException(
            status_code=500,
            detail=f"Could not retrieve index status: {str(exc)}",
        )


# ── POST /search/index ────────────────────────────────────────

@router.post(
    "/index",
    response_model=IndexAllResponse,
    summary="Index all products into ChromaDB",
    description=(
        "Reads every product from SQLite, generates embeddings, "
        "and upserts them into ChromaDB. Safe to call multiple times — uses upsert."
    ),
)
def index_all(db: Session = Depends(get_db)):
    """
    Re-index the full product catalog for semantic search.

    **When to use:**
    - After adding multiple new products in bulk
    - If the semantic search results seem stale or incorrect
    - On a fresh deployment (though startup also does this automatically)

    **Safe to call anytime** — uses upsert, so existing products are updated,
    not duplicated. New products are added to the index.

    The response includes counts of indexed / skipped / errored products.
    """
    try:
        result = index_all_products(db)

        success  = result.errors == 0
        message  = (
            f"Indexed {result.indexed} products successfully."
            if success
            else f"Indexed {result.indexed} products with {result.errors} errors."
        )

        return IndexAllResponse(
            success       = success,
            indexed       = result.indexed,
            skipped       = result.skipped,
            errors        = result.errors,
            error_details = result.error_details,
            message       = message,
        )

    except Exception as exc:
        logger.error(f"[Search API] Full index operation failed: {exc}")
        raise HTTPException(
            status_code=500,
            detail=f"Indexing failed: {str(exc)}",
        )


# ── POST /search/index/{product_id} ──────────────────────────

@router.post(
    "/index/{product_id}",
    response_model=SingleIndexResponse,
    summary="Index a single product into ChromaDB",
    description=(
        "Generates an embedding for one specific product and upserts it into ChromaDB. "
        "Use this after adding a new product via POST /products."
    ),
)
def index_one(
    product_id: str,
    db: Session = Depends(get_db),
):
    """
    Index a single product by its product_id.

    **When to use:**
    After adding a new product via `POST /products`, call this endpoint
    so the new product immediately appears in semantic search results.

    Example: After `POST /products` creates `PROD021`, call
    `POST /search/index/PROD021` to make it searchable.
    """
    try:
        result = index_single_product(db, product_id)

        if result.errors > 0:
            error_detail = result.error_details[0] if result.error_details else "Unknown error"
            # Return 404 if product not found, 500 for other errors
            status_code = 404 if "not found" in error_detail.lower() else 500
            raise HTTPException(
                status_code=status_code,
                detail=error_detail,
            )

        return SingleIndexResponse(
            success    = True,
            product_id = product_id,
            message    = f"Product '{product_id}' indexed successfully.",
            error      = None,
        )

    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except Exception as exc:
        logger.error(f"[Search API] Single index failed for '{product_id}': {exc}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to index product '{product_id}': {str(exc)}",
        )
