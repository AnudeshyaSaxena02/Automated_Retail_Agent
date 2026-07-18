# ============================================================
# IDAM — Intelligent Automated Retail Store Backend
# app/services/search_service.py
#
# PURPOSE:
#   Orchestrates the full semantic search pipeline.
#   Called by the search API router — never by other services.
#
# SEMANTIC SEARCH PIPELINE (per query):
#   1. generate_embedding(query)          — embed the user's query
#   2. chroma_client.query_similar()      — find nearest product vectors
#   3. product_service.get_products_by_ids() — hydrate from SQLite
#   4. Reorder + score results            — align with ChromaDB ranking
#   5. Return List[SearchResultItem]      — ranked results with scores
#
# WHY HYDRATE FROM SQLITE?
#   ChromaDB stores only the embedding + lightweight metadata
#   (name, category, brand, price). Full product data (description,
#   specs, tags, stock) lives in SQLite and is fetched after search.
#   This keeps ChromaDB lean and SQLite as the single source of truth.
# ============================================================

import json
import logging
from typing import List, Optional

from sqlalchemy.orm import Session

from app.ai.embeddings.product_embedder import generate_embedding, get_model_info
from app.ai.vectordb.chroma_client import query_similar, get_collection_count
from app.config.settings import settings
from app.schemas.search import SearchResultItem, SemanticSearchResponse, IndexStatusResponse

logger = logging.getLogger(__name__)


# ── JSON helpers ─────────────────────────────────────────────

def _safe_json_list(value: Optional[str]) -> list:
    """Parse a JSON string into a list, returning [] on failure."""
    if not value:
        return []
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return []


def _safe_json_dict(value: Optional[str]) -> dict:
    """Parse a JSON string into a dict, returning {} on failure."""
    if not value:
        return {}
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return {}


# ── Core semantic search ──────────────────────────────────────

def semantic_search(
    db: Session,
    query: str,
    limit: int = 10,
    min_score: float = 0.0,
) -> SemanticSearchResponse:
    """
    Run a full semantic search query against the product index.

    Accepts a natural-language query string and returns the most
    semantically relevant products, ranked by similarity score.

    Works even when exact keywords are absent — the embedding model
    understands meaning, not just literal text matches.

    EXAMPLES:
        "I need a gaming laptop for AI"
           → matches laptops with gaming/AI/machine-learning tags
        "Show me lightweight laptops"
           → matches thin/portable/ultrabook-tagged laptops
        "I want wireless headphones with good battery"
           → matches Bluetooth headphones with long battery life

    Args:
        db        : SQLAlchemy session (used to hydrate full product data)
        query     : The user's natural-language search query
        limit     : Max number of results to return (default 10)
        min_score : Minimum similarity score threshold 0.0–1.0 (default 0.0)
                    Results below this score are filtered out.

    Returns:
        SemanticSearchResponse with ranked SearchResultItem list
    """

    logger.info(f"[Search] Semantic query: '{query}' | limit={limit} | min_score={min_score}")

    # ── Step 1: Embed the query ──────────────────────────────
    # We embed the query with the SAME model used to embed products.
    # This is critical — mixing models would produce incomparable vectors.
    query_vector: List[float] = generate_embedding(query)

    # ── Step 2: Query ChromaDB for similar product vectors ───
    raw_results = query_similar(
        query_embedding=query_vector,
        n_results=limit,
    )

    ids_list:       List[str]   = raw_results.get("ids", [[]])[0]
    distances_list: List[float] = raw_results.get("distances", [[]])[0]

    if not ids_list:
        logger.info("[Search] ChromaDB returned no results.")
        return SemanticSearchResponse(
            query=query,
            total=0,
            results=[],
            model_used=settings.embedding_model,
        )

    # ── Step 3: Hydrate full product data from SQLite ────────
    # ChromaDB only stores lightweight metadata; full specs/description
    # live in SQLite. We fetch them all in one query for efficiency.
    from app.database.models import Product

    products_map: dict = {}
    products_in_db = (
        db.query(Product)
        .filter(Product.product_id.in_(ids_list))
        .all()
    )
    for p in products_in_db:
        products_map[p.product_id] = p

    # ── Step 4: Build ranked result list ────────────────────
    # ChromaDB returns results in ranked order (smallest distance first).
    # We preserve that ranking while computing the similarity score.
    results: List[SearchResultItem] = []

    for rank_idx, (product_id, distance) in enumerate(zip(ids_list, distances_list), start=1):
        # Convert cosine distance to similarity score
        # distance 0.0 = identical → score 1.0
        # distance 1.0 = opposite  → score 0.0
        similarity_score = round(max(0.0, 1.0 - distance), 4)

        # Apply min_score filter
        if similarity_score < min_score:
            logger.debug(
                f"[Search] Skipping '{product_id}' — score {similarity_score:.4f} < min {min_score}"
            )
            continue

        # Get the full product from our hydration map
        product = products_map.get(product_id)
        if not product:
            # Product in ChromaDB but not in SQLite (stale index)
            logger.warning(
                f"[Search] Product '{product_id}' found in ChromaDB but missing in SQLite. "
                "Index may be stale — run POST /search/index to refresh."
            )
            continue

        results.append(SearchResultItem(
            rank             = rank_idx,
            product_id       = product.product_id,
            name             = product.name,
            category         = product.category,
            brand            = product.brand or "",
            price            = product.price,
            stock            = product.stock,
            description      = product.description,
            specifications   = _safe_json_dict(product.specifications),
            tags             = _safe_json_list(product.tags),
            similarity_score = similarity_score,
        ))

    logger.info(
        f"[Search] Returning {len(results)} results for query: '{query}'"
    )

    return SemanticSearchResponse(
        query      = query,
        total      = len(results),
        results    = results,
        model_used = settings.embedding_model,
    )


# ── Index status ──────────────────────────────────────────────

def get_search_status() -> IndexStatusResponse:
    """
    Return the current state of the ChromaDB product index.

    Used by GET /search/status to let callers check if the index
    is ready before running searches.

    Returns:
        IndexStatusResponse with count, model info, and storage path
    """
    indexed_count = get_collection_count()
    model_info    = get_model_info()

    return IndexStatusResponse(
        status            = "ready" if indexed_count > 0 else "empty",
        indexed_count     = indexed_count,
        model             = model_info["model_name"],
        vector_dimensions = model_info["vector_dimensions"],
        chroma_path       = settings.chroma_db_path,
    )
