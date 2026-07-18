# ============================================================
# IDAM — Intelligent Automated Retail Store Backend
# app/ai/rag/rag_context_builder.py
#
# PURPOSE:
#   Converts raw search results (SearchResultItem list) into a
#   clean, structured context dict ready for prompt injection.
#
# WHAT IT DOES:
#   1. Formats each retrieved product into a readable text block
#   2. Optionally fetches ProductReview rows from SQLite for top products
#   3. Returns a single dict that build_rag_prompt() consumes
#
# WHY A SEPARATE MODULE?
#   Keeps the transformation logic out of the service layer.
#   The prompt builder should receive clean context — not raw ORM objects.
#   Phase 8 can enrich the same context dict with customer profile data
#   without touching this file.
#
# CONTEXT DICT SCHEMA (returned by build_context()):
#   {
#     "products": [
#       {
#         "rank": 1,
#         "product_id": "PROD001",
#         "name": "Lenovo IdeaPad Slim 5",
#         "category": "Laptops",
#         "brand": "Lenovo",
#         "price": 58999.0,
#         "stock": 100,
#         "description": "Intel i5 13th Gen...",
#         "specifications": {"CPU": "Intel i5", "RAM": "16GB"},
#         "tags": ["laptop", "AI", "coding"],
#         "similarity_score": 0.87,
#         "text_block": "...",   ← pre-formatted for the prompt
#         "reviews": [...]       ← list of review text strings (may be [])
#       },
#       ...
#     ],
#     "total_retrieved": 5,
#     "query": "original user query",
#   }
# ============================================================

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.schemas.search import SearchResultItem

logger = logging.getLogger(__name__)

# Max reviews to fetch per product (keeps prompt size manageable)
_MAX_REVIEWS_PER_PRODUCT = 2

# Max products to fetch reviews for (reviews add token cost)
_MAX_PRODUCTS_WITH_REVIEWS = 3


def _format_product_block(product: SearchResultItem, rank: int) -> str:
    """
    Format a single product as a structured text block for LLM injection.

    The format is designed to be:
      - Compact (fewer tokens)
      - Unambiguous (each field is labeled)
      - Factual (only real catalog data)

    Example output:
        [Product 1] Lenovo IdeaPad Slim 5
        Category: Laptops | Brand: Lenovo | Price: ₹58,999 | Stock: In Stock
        Description: Intel i5 13th Gen, 16GB RAM, 512GB SSD...
        Specs: CPU: Intel i5-13420H, RAM: 16GB, Storage: 512GB SSD
        Tags: laptop, AI, machine learning, coding
        Relevance Score: 0.87
    """
    lines = [f"[Product {rank}] {product.name}"]

    stock_label = "In Stock" if product.stock > 0 else "Out of Stock"
    lines.append(
        f"Category: {product.category} | "
        f"Brand: {product.brand or 'N/A'} | "
        f"Price: ₹{product.price:,.0f} | "
        f"Stock: {stock_label}"
    )

    if product.description:
        lines.append(f"Description: {product.description}")

    if product.specifications:
        specs_str = ", ".join(f"{k}: {v}" for k, v in product.specifications.items())
        lines.append(f"Specs: {specs_str}")

    if product.tags:
        lines.append(f"Tags: {', '.join(product.tags)}")

    lines.append(f"Relevance Score: {product.similarity_score:.2f}")

    return "\n".join(lines)


def _fetch_reviews(
    db: Session,
    product_id: str,
    max_reviews: int = _MAX_REVIEWS_PER_PRODUCT,
) -> List[str]:
    """
    Fetch review texts for a product from SQLite.

    Reviews are ordered by rating descending so the most positive,
    informative reviews appear first in the prompt context.

    Returns [] silently on any error — reviews are optional enrichment,
    not critical to the RAG pipeline.

    Args:
        db         : SQLAlchemy session
        product_id : e.g. "PROD001"
        max_reviews: Maximum number of reviews to return

    Returns:
        List of review text strings (may be empty)
    """
    try:
        from app.database.models import ProductReview
        reviews = (
            db.query(ProductReview)
            .filter(ProductReview.product_id == product_id)
            .order_by(ProductReview.rating.desc())
            .limit(max_reviews)
            .all()
        )
        return [r.review_text for r in reviews if r.review_text]
    except Exception as exc:
        logger.warning(
            f"[RAGContext] Could not fetch reviews for '{product_id}': {exc}. Skipping."
        )
        return []


def build_context(
    query: str,
    products: List[SearchResultItem],
    db: Optional[Session] = None,
    include_reviews: bool = True,
) -> Dict[str, Any]:
    """
    Build a structured RAG context dict from retrieved search results.

    This is the bridge between the semantic search pipeline (Phase 5)
    and the prompt builder (Phase 7). It takes raw SearchResultItems
    and produces a clean, prompt-ready context structure.

    Args:
        query           : The original user query (included for prompt context)
        products        : Ranked list of SearchResultItems from semantic_search()
        db              : SQLAlchemy session — required for review enrichment.
                          If None, reviews are skipped.
        include_reviews : Whether to fetch ProductReview data from SQLite.
                          Set False to skip reviews and reduce prompt length.

    Returns:
        Context dict with structure described in module docstring.
    """
    logger.info(
        f"[RAGContext] Building context for query='{query[:60]}...' "
        f"with {len(products)} products | reviews={'yes' if include_reviews and db else 'no'}"
    )

    product_contexts: List[Dict[str, Any]] = []

    for idx, product in enumerate(products, start=1):
        # Format the product as a readable text block for prompt injection
        text_block = _format_product_block(product, rank=idx)

        # Fetch reviews for top N products only (to manage prompt token cost)
        reviews: List[str] = []
        if include_reviews and db and idx <= _MAX_PRODUCTS_WITH_REVIEWS:
            reviews = _fetch_reviews(db, product.product_id)
            if reviews:
                logger.debug(
                    f"[RAGContext] Fetched {len(reviews)} review(s) for '{product.product_id}'"
                )

        product_contexts.append({
            "rank":             product.rank,
            "product_id":       product.product_id,
            "name":             product.name,
            "category":         product.category,
            "brand":            product.brand,
            "price":            product.price,
            "stock":            product.stock,
            "description":      product.description,
            "specifications":   product.specifications,
            "tags":             product.tags,
            "similarity_score": product.similarity_score,
            "text_block":       text_block,
            "reviews":          reviews,
        })

    context = {
        "query":           query,
        "products":        product_contexts,
        "total_retrieved": len(product_contexts),
    }

    logger.info(
        f"[RAGContext] Context built: {len(product_contexts)} products, "
        f"{sum(len(p['reviews']) for p in product_contexts)} total reviews."
    )

    return context
