# ============================================================
# IDAM — Intelligent Automated Retail Store Backend
# app/ai/recommendation/candidate_generator.py
#
# PURPOSE:
#   Generate a broad pool of candidate products for the scoring
#   engine to rank. Combines two retrieval strategies:
#
#   Strategy A — Semantic retrieval (ChromaDB):
#     Embeds the user's query (or an interest-based fallback
#     query built from the customer's category_interests) and
#     fetches the top N most semantically similar products.
#     Returns cosine similarity scores alongside product_ids.
#
#   Strategy B — Interest-based retrieval (SQLite):
#     Fetches all in-stock products from every category in the
#     customer's category_interests and purchased_categories.
#     These products bypass ChromaDB but still get scored.
#
#   Both pools are merged and deduplicated (by product_id).
#   The merged pool is returned as a list of CandidateProduct
#   dataclasses that carry the semantic_score for scoring.
#
# WHY TWO STRATEGIES?
#   ChromaDB is great when there's a specific query, but without
#   a query (or with a vague one) it may miss obvious products
#   that match the customer's known interests. The SQLite fallback
#   ensures interest-aligned categories are always represented.
# ============================================================

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from app.ai.embeddings.product_embedder import generate_embedding
from app.ai.vectordb.chroma_client import query_similar
from app.database.models import Product

logger = logging.getLogger(__name__)

# Number of candidates to retrieve from ChromaDB per query
_CHROMA_N_RESULTS = 30

# Minimum semantic similarity to include a ChromaDB result
_CHROMA_MIN_SIMILARITY = 0.15


# ── CandidateProduct dataclass ────────────────────────────────

@dataclass
class CandidateProduct:
    """
    A candidate product ready for the scoring engine.

    Carries the full ORM Product object so scoring.py can access
    all fields (category, brand, price, stock, tags) without
    additional DB queries.

    semantic_score is 0.0 for interest-only candidates (i.e.
    those retrieved from SQLite but not from ChromaDB). The
    scoring engine treats 0.0 semantic score as neutral and
    relies on the interest + budget factors instead.
    """
    product: Product
    semantic_score: float = 0.0  # Cosine similarity from ChromaDB (0.0 if not retrieved semantically)


# ── Internal helpers ──────────────────────────────────────────

def _build_fallback_query(
    category_interests: List[str],
    purchased_categories: List[str],
) -> str:
    """
    Build a natural-language fallback query when no user query is given.

    Combines the customer's interest categories into a descriptive
    phrase that can be embedded and used for ChromaDB retrieval.

    Example:
        interests: ["Laptops", "Accessories", "Audio"]
        → "Laptops, Accessories, Audio products and gadgets"
    """
    all_interests = list(dict.fromkeys(category_interests + purchased_categories))  # dedup, preserve order
    if not all_interests:
        return "popular electronics gadgets and accessories"

    categories_str = ", ".join(all_interests[:5])  # cap at 5 to keep the embedding focused
    return f"{categories_str} products and gadgets"


def _semantic_candidates(
    query: str,
    n_results: int,
    db: Session,
) -> Dict[str, CandidateProduct]:
    """
    Retrieve semantically similar products from ChromaDB.

    Returns a dict mapping product_id → CandidateProduct.
    Products are loaded from SQLite to hydrate the full ORM object.

    Args:
        query     : Embedded natural-language query
        n_results : Number of results to request from ChromaDB
        db        : SQLAlchemy session for SQLite hydration

    Returns:
        Dict[product_id, CandidateProduct] — may be empty if ChromaDB
        is not ready or no results meet the minimum similarity threshold.
    """
    candidates: Dict[str, CandidateProduct] = {}

    try:
        query_vector = generate_embedding(query)
        raw_results  = query_similar(query_embedding=query_vector, n_results=n_results)

        ids_list       = raw_results.get("ids", [[]])[0]
        distances_list = raw_results.get("distances", [[]])[0]

        if not ids_list:
            logger.info("[CandidateGen] ChromaDB returned no results.")
            return candidates

        # Hydrate full product data from SQLite
        products_in_db = (
            db.query(Product)
            .filter(Product.product_id.in_(ids_list))
            .all()
        )
        products_map = {p.product_id: p for p in products_in_db}

        for product_id, distance in zip(ids_list, distances_list):
            similarity = round(max(0.0, 1.0 - distance), 4)

            # Apply minimum similarity threshold
            if similarity < _CHROMA_MIN_SIMILARITY:
                continue

            product = products_map.get(product_id)
            if product is None:
                logger.warning(
                    f"[CandidateGen] Product '{product_id}' in ChromaDB but missing in SQLite. Skipping."
                )
                continue

            candidates[product_id] = CandidateProduct(
                product        = product,
                semantic_score = similarity,
            )

        logger.info(
            f"[CandidateGen] ChromaDB returned {len(candidates)} semantic candidates "
            f"(query: '{query[:60]}...')" if len(query) > 60 else
            f"[CandidateGen] ChromaDB returned {len(candidates)} semantic candidates "
            f"(query: '{query}')"
        )

    except Exception as exc:
        logger.warning(
            f"[CandidateGen] ChromaDB semantic retrieval failed: {exc}. "
            "Continuing with interest-only candidates."
        )

    return candidates


def _interest_candidates(
    category_interests: List[str],
    purchased_categories: List[str],
    db: Session,
) -> Dict[str, CandidateProduct]:
    """
    Retrieve products from SQLite based on the customer's interest categories.

    Queries all products whose category matches any of the customer's
    interest categories or purchased categories. Stock filter is NOT
    applied here — filters.py handles that as a separate, explicit step.

    Args:
        category_interests   : Expanding list from CustomerMemory
        purchased_categories : List of categories the customer has bought in
        db                   : SQLAlchemy session

    Returns:
        Dict[product_id, CandidateProduct] with semantic_score = 0.0
    """
    candidates: Dict[str, CandidateProduct] = {}

    all_categories = list(dict.fromkeys(category_interests + purchased_categories))

    if not all_categories:
        logger.info("[CandidateGen] No interest categories found — skipping interest candidates.")
        return candidates

    for category in all_categories:
        products_in_cat = (
            db.query(Product)
            .filter(Product.category.ilike(f"%{category}%"))
            .all()
        )
        for product in products_in_cat:
            if product.product_id not in candidates:
                candidates[product.product_id] = CandidateProduct(
                    product        = product,
                    semantic_score = 0.0,  # No semantic score for interest-only candidates
                )

    logger.info(
        f"[CandidateGen] Interest-based retrieval found {len(candidates)} candidates "
        f"across {len(all_categories)} categories."
    )
    return candidates


# ── Public API ────────────────────────────────────────────────

def get_candidates(
    db: Session,
    query: Optional[str],
    category_interests: List[str],
    purchased_categories: List[str],
    n_results: int = _CHROMA_N_RESULTS,
) -> List[CandidateProduct]:
    """
    Generate a merged, deduplicated candidate pool for scoring.

    Combines semantic retrieval (ChromaDB) and interest-based
    retrieval (SQLite). When both strategies retrieve the same
    product, the semantic_score from ChromaDB is preserved
    (it carries more signal than 0.0).

    Args:
        db                   : SQLAlchemy session
        query                : User's natural-language intent (may be None/empty)
        category_interests   : Customer's expanding interest list from CustomerMemory
        purchased_categories : Categories the customer has purchased from
        n_results            : How many results to request from ChromaDB

    Returns:
        List[CandidateProduct] — unscored, unfiltered, deduplicated
    """
    # ── Strategy B first (interest-based from SQLite) ─────────
    # Lower priority — semantic score stays at 0.0
    interest_pool = _interest_candidates(category_interests, purchased_categories, db)

    # ── Strategy A (semantic from ChromaDB) ───────────────────
    # Build query: use provided query or build fallback from interests
    effective_query = query.strip() if query and query.strip() else _build_fallback_query(
        category_interests, purchased_categories
    )
    semantic_pool = _semantic_candidates(effective_query, n_results, db)

    # ── Merge: semantic scores take priority ──────────────────
    # Start with the interest pool, then overlay/update with semantic results
    merged: Dict[str, CandidateProduct] = {**interest_pool}
    for product_id, candidate in semantic_pool.items():
        if product_id in merged:
            # Product found in both pools — update with the real semantic score
            merged[product_id].semantic_score = candidate.semantic_score
        else:
            merged[product_id] = candidate

    candidates = list(merged.values())

    logger.info(
        f"[CandidateGen] Merged pool: {len(candidates)} total candidates "
        f"({len(semantic_pool)} semantic, {len(interest_pool)} interest-based)."
    )

    return candidates
