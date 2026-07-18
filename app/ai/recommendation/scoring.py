# ============================================================
# IDAM — Intelligent Automated Retail Store Backend
# app/ai/recommendation/scoring.py
#
# PURPOSE:
#   Compute a weighted composite score for every candidate product.
#   Produces a sorted, ranked list of ScoredProduct objects.
#
# SCORING FORMULA:
#   Final Score =
#     WEIGHT_INTEREST  × Customer Interest Score   (0.35)
#   + WEIGHT_SEMANTIC  × Semantic Similarity Score  (0.25)
#   + WEIGHT_BUDGET    × Budget Compatibility Score  (0.20)
#   + WEIGHT_FREQUENCY × Purchase Frequency Score    (0.10)
#   + WEIGHT_POPULARITY× Product Popularity Score    (0.10)
#
# ALL WEIGHTS ARE CONFIGURABLE CONSTANTS — change them here
# to re-tune the engine without touching any other file.
#
# FACTOR DETAILS:
#
#   Interest Score:
#     - Exact category match with purchased_categories: 1.0
#     - Category in category_interests (not yet purchased): 0.7
#     - No category match: 0.1 base (product still has a chance)
#     - Preferred brand bonus: +0.2 (capped at 1.0)
#     - Tag overlap bonus: +0.05 per overlapping tag (capped at 1.0)
#
#   Semantic Score:
#     - From ChromaDB cosine similarity (already 0.0–1.0)
#     - 0.0 for interest-only candidates (not retrieved semantically)
#
#   Budget Score:
#     - 1.0 - |price - budget| / budget  (clamped to [0, 1])
#     - 0.5 (neutral) when budget = 0.0 (no purchase history)
#     - Products significantly above budget score near 0
#     - Products near the budget score near 1.0
#
#   Frequency Score:
#     - Orders by this customer in this product's category
#       divided by the max category order count for this customer
#     - Normalized to [0, 1]; 0.0 if no category orders at all
#
#   Popularity Score:
#     - Total orders for this product across ALL customers
#       divided by the most-ordered product's order count
#     - Normalized to [0, 1]; 0.0 if no orders exist in DB
#
# REASON STRING:
#   A human-readable explanation is generated from the scores.
#   It does NOT call the LLM — it's rule-based text assembly.
#   The LLM explanation phase comes later (Phase 9+).
# ============================================================

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.ai.recommendation.candidate_generator import CandidateProduct
from app.database.models import Order, json_to_list

logger = logging.getLogger(__name__)


# ── Scoring weights ───────────────────────────────────────────
# These must sum to 1.0. Adjust to re-tune the engine.
WEIGHT_INTEREST   = 0.35
WEIGHT_SEMANTIC   = 0.25
WEIGHT_BUDGET     = 0.20
WEIGHT_FREQUENCY  = 0.10
WEIGHT_POPULARITY = 0.10

# Validate at import time (sanity check)
_WEIGHT_SUM = round(WEIGHT_INTEREST + WEIGHT_SEMANTIC + WEIGHT_BUDGET + WEIGHT_FREQUENCY + WEIGHT_POPULARITY, 4)
assert _WEIGHT_SUM == 1.0, f"Scoring weights must sum to 1.0, got {_WEIGHT_SUM}"


# ── ScoredProduct dataclass ───────────────────────────────────

@dataclass
class ScoredProduct:
    """
    A candidate product after scoring.

    All score fields are in [0.0, 1.0].
    final_score is the weighted composite.
    """
    product:          Any    # Product ORM object
    final_score:      float
    interest_score:   float
    semantic_score:   float
    budget_score:     float
    frequency_score:  float
    popularity_score: float
    reason:           str


# ── Factor 1: Customer Interest Score ────────────────────────

def _compute_interest_score(
    candidate: CandidateProduct,
    purchased_categories: List[str],
    category_interests: List[str],
    preferred_brands: List[str],
    interest_tags: List[str],
) -> float:
    """
    Score how well the product aligns with the customer's interests.

    Scoring logic (additive, capped at 1.0):
      - Purchased category match:  +1.0 (already buys this category)
      - Interest category match:   +0.7 (interested but hasn't bought yet)
      - No category match:          0.1 (base score — not zero)
      - Preferred brand match:     +0.2
      - Each tag overlap:          +0.05 (max +0.20)

    Args:
        candidate            : CandidateProduct being scored
        purchased_categories : Categories the customer has bought from
        category_interests   : Broader interest categories (never shrinks)
        preferred_brands     : Brands the customer prefers
        interest_tags        : Flat list of keywords from all interests

    Returns:
        float in [0.0, 1.0]
    """
    product  = candidate.product
    category = product.category or ""
    brand    = product.brand or ""
    tags     = json_to_list(product.tags) if isinstance(product.tags, str) else (product.tags or [])

    # Category score
    if category in purchased_categories:
        score = 1.0
    elif any(category.lower() in interest.lower() or interest.lower() in category.lower()
             for interest in category_interests):
        score = 0.7
    else:
        score = 0.1  # base — don't zero out; semantic/budget may still make it relevant

    # Brand bonus
    if brand and brand in preferred_brands:
        score += 0.2

    # Tag overlap bonus (max +0.20 = 4 matches × 0.05)
    if interest_tags and tags:
        product_tags_lower = {str(t).lower() for t in tags}
        interest_tags_lower = {str(t).lower() for t in interest_tags}
        overlap_count = len(product_tags_lower & interest_tags_lower)
        score += min(overlap_count * 0.05, 0.20)

    return round(min(score, 1.0), 4)


# ── Factor 3: Budget Compatibility Score ─────────────────────

def _compute_budget_score(price: float, budget_estimate: float) -> float:
    """
    Score how well the product price fits the customer's estimated budget.

    Formula: 1.0 - |price - budget| / budget  (clamped to [0.0, 1.0])

    Behavior:
      - price == budget:       score = 1.0  (perfect fit)
      - price == budget × 0.5: score = 0.5  (half the budget)
      - price == budget × 2.0: score = 0.0  (double the budget)
      - budget == 0.0:          score = 0.5  (neutral; no history)

    Args:
        price           : Product price in INR
        budget_estimate : Customer's estimated budget for this period

    Returns:
        float in [0.0, 1.0]
    """
    if budget_estimate <= 0.0:
        return 0.5  # neutral when no purchase history exists

    deviation_ratio = abs(price - budget_estimate) / budget_estimate
    score = 1.0 - deviation_ratio
    return round(max(0.0, min(score, 1.0)), 4)


# ── Factor 4: Purchase Frequency Score ───────────────────────

def _compute_frequency_score(
    category: str,
    category_purchase_counts: Dict[str, int],
    max_category_count: int,
) -> float:
    """
    Score based on how often the customer buys in this product's category.

    Normalizes the category's purchase count against the customer's
    most-purchased category. Reflects category affinity.

    Args:
        category                : The product's category
        category_purchase_counts: {category: order_count} for this customer
        max_category_count      : Highest count across all categories

    Returns:
        float in [0.0, 1.0]; 0.0 if customer has no orders
    """
    if max_category_count == 0:
        return 0.0

    count = 0
    # Case-insensitive lookup
    for cat, cnt in category_purchase_counts.items():
        if cat.lower() == category.lower():
            count = cnt
            break

    return round(count / max_category_count, 4)


# ── Factor 5: Popularity Score ────────────────────────────────

def _fetch_popularity_map(db: Session) -> Dict[str, int]:
    """
    Compute total order counts per product across all customers.

    Single aggregation query — runs once per recommendation request,
    not once per product. The result is passed to score_product()
    as a pre-computed dict.

    Returns:
        Dict[product_id, total_order_count]
    """
    try:
        rows = (
            db.query(Order.product_id, func.count(Order.id).label("cnt"))
            .group_by(Order.product_id)
            .all()
        )
        return {row.product_id: row.cnt for row in rows}
    except Exception as exc:
        logger.warning(f"[Scoring] Failed to fetch popularity data: {exc}. Defaulting to 0.")
        return {}


def _compute_popularity_score(product_id: str, popularity_map: Dict[str, int]) -> float:
    """
    Normalized popularity score for a product.

    Score = this product's orders ÷ most-ordered product's orders.

    Args:
        product_id     : The product to score
        popularity_map : Precomputed {product_id: total_orders} dict

    Returns:
        float in [0.0, 1.0]
    """
    if not popularity_map:
        return 0.0

    count     = popularity_map.get(product_id, 0)
    max_count = max(popularity_map.values())

    if max_count == 0:
        return 0.0

    return round(count / max_count, 4)


# ── Reason string builder ─────────────────────────────────────

def _build_reason(
    product_category:    str,
    product_brand:       str,
    purchased_categories: List[str],
    category_interests:  List[str],
    preferred_brands:    List[str],
    interest_score:      float,
    semantic_score:      float,
    budget_score:        float,
    frequency_score:     float,
    final_score:         float,
) -> str:
    """
    Build a human-readable reason string from scoring signals.

    Uses rule-based text assembly — no LLM involved.
    The reason is concise and factual, listing the most impactful
    signals that elevated this product's score.

    Returns:
        String like "Matches preferred category (Accessories) and
        preferred brand (Logitech). Price fits monthly budget."
    """
    parts: List[str] = []

    # Category signal
    if product_category in purchased_categories:
        parts.append(f"Matches frequently purchased category ({product_category})")
    elif any(product_category.lower() in i.lower() or i.lower() in product_category.lower()
             for i in category_interests):
        parts.append(f"Matches customer interest category ({product_category})")

    # Brand signal
    if product_brand and product_brand in preferred_brands:
        parts.append(f"preferred brand ({product_brand})")

    # Semantic signal
    if semantic_score >= 0.6:
        parts.append("strong semantic match to your query")
    elif semantic_score >= 0.3:
        parts.append("relevant to your query")

    # Budget signal
    if budget_score >= 0.8:
        parts.append("price fits estimated monthly budget well")
    elif budget_score >= 0.5:
        parts.append("price is within acceptable budget range")
    elif budget_score < 0.3:
        parts.append("price is above typical monthly budget")

    # Frequency signal
    if frequency_score >= 0.7:
        parts.append("frequently purchased category for this customer")

    # Default reason when nothing stands out
    if not parts:
        parts.append("discovered via semantic and interest matching")

    return ". ".join(p.capitalize() for p in parts) + "."


# ── Core scoring function ─────────────────────────────────────

def score_product(
    candidate:              CandidateProduct,
    purchased_categories:   List[str],
    category_interests:     List[str],
    preferred_brands:       List[str],
    interest_tags:          List[str],
    budget_estimate:        float,
    category_purchase_counts: Dict[str, int],
    max_category_count:     int,
    popularity_map:         Dict[str, int],
) -> ScoredProduct:
    """
    Compute all scoring factors and return a ScoredProduct.

    This function is pure from the caller's perspective — it takes
    pre-computed context dicts (popularity_map, category_purchase_counts)
    to avoid making DB calls per product.

    Args:
        candidate                : CandidateProduct (product + semantic_score)
        purchased_categories     : Categories the customer has purchased
        category_interests       : Customer's expanding interest list
        preferred_brands         : Customer's preferred brands
        interest_tags            : Flat keyword list from interests (for tag overlap)
        budget_estimate          : Customer's estimated budget for today's period
        category_purchase_counts : {category: count} for this customer
        max_category_count       : Max category count (for normalization)
        popularity_map           : {product_id: total_orders} across all customers

    Returns:
        ScoredProduct with all factor scores + weighted final_score + reason
    """
    product = candidate.product

    # ── Compute individual factors ────────────────────────────
    interest_score = _compute_interest_score(
        candidate, purchased_categories, category_interests,
        preferred_brands, interest_tags,
    )
    semantic_score   = candidate.semantic_score  # already 0.0–1.0 from ChromaDB
    budget_score     = _compute_budget_score(product.price, budget_estimate)
    frequency_score  = _compute_frequency_score(
        product.category or "", category_purchase_counts, max_category_count
    )
    popularity_score = _compute_popularity_score(product.product_id, popularity_map)

    # ── Weighted composite ────────────────────────────────────
    final_score = (
        WEIGHT_INTEREST   * interest_score
      + WEIGHT_SEMANTIC   * semantic_score
      + WEIGHT_BUDGET     * budget_score
      + WEIGHT_FREQUENCY  * frequency_score
      + WEIGHT_POPULARITY * popularity_score
    )
    final_score = round(min(final_score, 1.0), 4)

    # ── Human-readable reason ─────────────────────────────────
    reason = _build_reason(
        product_category     = product.category or "",
        product_brand        = product.brand or "",
        purchased_categories = purchased_categories,
        category_interests   = category_interests,
        preferred_brands     = preferred_brands,
        interest_score       = interest_score,
        semantic_score       = semantic_score,
        budget_score         = budget_score,
        frequency_score      = frequency_score,
        final_score          = final_score,
    )

    return ScoredProduct(
        product          = product,
        final_score      = final_score,
        interest_score   = round(interest_score, 4),
        semantic_score   = round(semantic_score, 4),
        budget_score     = round(budget_score, 4),
        frequency_score  = round(frequency_score, 4),
        popularity_score = round(popularity_score, 4),
        reason           = reason,
    )


# ── Batch scoring ─────────────────────────────────────────────

def _build_category_purchase_counts(orders: List[Any]) -> Dict[str, int]:
    """
    Build a {category: count} dict from the customer's orders.

    Each order dict must have a 'product_category' key (from
    customer_service.get_customer_orders()).

    Args:
        orders : List of order dicts from get_customer_orders()

    Returns:
        {category_name: purchase_count}
    """
    counts: Dict[str, int] = {}
    for order in orders:
        category = order.get("product_category", "")
        if category:
            counts[category] = counts.get(category, 0) + 1
    return counts


def score_all_candidates(
    candidates:           List[CandidateProduct],
    customer_profile:     Dict[str, Any],
    orders:               List[Any],
    db:                   Session,
    top_k:                int = 10,
) -> List[ScoredProduct]:
    """
    Score every candidate and return the top-K ranked results.

    Pre-computes shared context (popularity map, category counts)
    once before the per-product loop to avoid O(n) DB queries.

    Args:
        candidates       : Filtered candidate pool from filters.py
        customer_profile : Profile dict from build_customer_profile()
        orders           : Order list from get_customer_orders()
        db               : SQLAlchemy session (for popularity query)
        top_k            : Number of top results to return

    Returns:
        List[ScoredProduct] sorted by final_score descending, capped at top_k
    """
    if not candidates:
        logger.info("[Scoring] No candidates to score — returning empty list.")
        return []

    # ── Pre-compute shared scoring context ────────────────────
    purchased_categories   = customer_profile.get("purchased_categories", [])
    category_interests     = customer_profile.get("category_interests", [])
    preferred_brands       = customer_profile.get("preferred_brands", [])
    budget_estimate        = customer_profile.get("budget_estimate", 0.0)

    # Build flat tag list from all interest categories for overlap scoring
    # (simple: use category names as tags; can be extended with actual tag DB later)
    interest_tags: List[str] = list(
        dict.fromkeys(category_interests + purchased_categories)
    )

    # Category purchase frequency context
    order_list             = orders if orders else []
    category_counts        = _build_category_purchase_counts(order_list)
    max_category_count     = max(category_counts.values()) if category_counts else 0

    # Popularity map — one DB query for all products
    popularity_map = _fetch_popularity_map(db)

    logger.info(
        f"[Scoring] Scoring {len(candidates)} candidates | "
        f"budget=₹{budget_estimate:,.0f} | "
        f"categories={purchased_categories} | "
        f"popularity_map size={len(popularity_map)}"
    )

    # ── Score every candidate ─────────────────────────────────
    scored: List[ScoredProduct] = []
    for candidate in candidates:
        sp = score_product(
            candidate              = candidate,
            purchased_categories   = purchased_categories,
            category_interests     = category_interests,
            preferred_brands       = preferred_brands,
            interest_tags          = interest_tags,
            budget_estimate        = budget_estimate,
            category_purchase_counts = category_counts,
            max_category_count     = max_category_count,
            popularity_map         = popularity_map,
        )
        scored.append(sp)

    # ── Sort by final_score descending ────────────────────────
    scored.sort(key=lambda s: s.final_score, reverse=True)

    # ── Return top-K ─────────────────────────────────────────
    result = scored[:top_k]
    logger.info(
        f"[Scoring] Scoring complete. "
        f"Top score: {result[0].final_score:.4f} | "
        f"Bottom score: {result[-1].final_score:.4f} | "
        f"Returning top {len(result)}."
    )
    return result
