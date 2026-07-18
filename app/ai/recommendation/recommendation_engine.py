# ============================================================
# IDAM — Intelligent Automated Retail Store Backend
# app/ai/recommendation/recommendation_engine.py
#
# PURPOSE:
#   Pipeline coordinator for the Phase 8 recommendation engine.
#   Orchestrates the full recommendation pipeline in 5 steps:
#
#   1. Build customer profile (from CustomerMemory ORM)
#   2. Generate candidate product pool (ChromaDB + SQLite)
#   3. Apply filters (out-of-stock, recently purchased)
#   4. Score and rank candidates (5-factor weighted model)
#   5. Return top-K ScoredProduct list
#
# DESIGN:
#   This file is the ONLY entry point the service layer calls.
#   It composes the three sub-modules (candidate_generator,
#   filters, scoring) without knowing about DB sessions, FastAPI,
#   or HTTP — that belongs in recommendation_service.py.
#
#   All logging at this level uses the prefix [Engine] to make
#   the pipeline trace easy to follow in the server log.
# ============================================================

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.ai.recommendation.candidate_generator import get_candidates
from app.ai.recommendation.customer_profile_builder import build_customer_profile
from app.ai.recommendation.filters import apply_all_filters
from app.ai.recommendation.scoring import score_all_candidates, ScoredProduct
from app.config.settings import settings
from app.database.models import Customer, CustomerMemory

logger = logging.getLogger(__name__)


# ── Pipeline result dataclass ─────────────────────────────────

class RecommendationResult:
    """
    Container returned by run().

    Carries the customer profile context alongside the ranked
    product list so the service layer can build the API response
    without re-querying the database.
    """

    def __init__(
        self,
        customer_profile:     Dict[str, Any],
        scored_products:      List[ScoredProduct],
        query_used:           Optional[str],
    ):
        self.customer_profile  = customer_profile
        self.scored_products   = scored_products
        self.query_used        = query_used


# ── Main pipeline function ────────────────────────────────────

def run(
    db:       Session,
    customer: Customer,
    memory:   CustomerMemory,
    orders:   List[Dict[str, Any]],
    query:    Optional[str] = None,
    top_k:    Optional[int] = None,
) -> RecommendationResult:
    """
    Execute the full recommendation pipeline for a customer.

    Called by recommendation_service.py after loading all
    necessary ORM objects from the database. This function
    does NOT perform any DB queries directly — it delegates
    to sub-modules and receives pre-loaded data.

    Pipeline steps (with logging prefix for each):
      [Engine] Step 1 — Build customer profile
      [Engine] Step 2 — Generate candidate pool
      [Engine] Step 3 — Apply filters
      [Engine] Step 4 — Score and rank
      [Engine] Step 5 — Return result

    Args:
        db       : SQLAlchemy session (passed to candidate_generator
                   and filters for their own queries)
        customer : Customer ORM object
        memory   : CustomerMemory ORM object
        orders   : List of order dicts from get_customer_orders()
        query    : Optional natural-language intent from the API request
        top_k    : Number of top products to return (defaults to settings)

    Returns:
        RecommendationResult with profile dict + sorted ScoredProduct list
    """
    effective_top_k = top_k if top_k is not None else settings.recommendation_top_k
    recency_days    = settings.recommendation_recency_days

    logger.info(
        f"[Engine] Starting recommendation pipeline for '{customer.customer_id}' | "
        f"query={'None' if not query else repr(query[:60])} | "
        f"top_k={effective_top_k} | recency_days={recency_days}"
    )

    # ── Step 1: Build customer profile ───────────────────────
    logger.info("[Engine] Step 1 — Building customer profile...")
    customer_profile = build_customer_profile(memory=memory, customer=customer)

    category_interests   = customer_profile.get("category_interests", [])
    purchased_categories = customer_profile.get("purchased_categories", [])

    logger.info(
        f"[Engine] Profile built: budget=₹{customer_profile.get('budget_estimate', 0):,.0f} | "
        f"interests={category_interests} | "
        f"brands={customer_profile.get('preferred_brands', [])}"
    )

    # ── Step 2: Generate candidate pool ──────────────────────
    logger.info("[Engine] Step 2 — Generating candidate pool...")
    candidates = get_candidates(
        db                   = db,
        query                = query,
        category_interests   = category_interests,
        purchased_categories = purchased_categories,
    )
    logger.info(f"[Engine] Candidate pool size: {len(candidates)}")

    # ── Step 3: Apply filters ─────────────────────────────────
    logger.info("[Engine] Step 3 — Applying filters...")
    filtered_candidates = apply_all_filters(
        candidates   = candidates,
        db           = db,
        customer_id  = customer.customer_id,
        recency_days = recency_days,
    )
    logger.info(f"[Engine] Filtered pool size: {len(filtered_candidates)}")

    # Handle edge case: all candidates filtered out
    if not filtered_candidates:
        logger.warning(
            f"[Engine] All candidates were filtered out for '{customer.customer_id}'. "
            "Returning empty recommendations."
        )
        return RecommendationResult(
            customer_profile = customer_profile,
            scored_products  = [],
            query_used       = query,
        )

    # ── Step 4: Score and rank candidates ────────────────────
    logger.info(f"[Engine] Step 4 — Scoring {len(filtered_candidates)} candidates...")
    order_list = orders if orders else []

    scored_products = score_all_candidates(
        candidates       = filtered_candidates,
        customer_profile = customer_profile,
        orders           = order_list,
        db               = db,
        top_k            = effective_top_k,
    )

    # ── Step 5: Return result ─────────────────────────────────
    logger.info(
        f"[Engine] Step 5 — Pipeline complete. "
        f"Returning {len(scored_products)} recommendations for '{customer.customer_id}'."
    )

    return RecommendationResult(
        customer_profile = customer_profile,
        scored_products  = scored_products,
        query_used       = query,
    )
