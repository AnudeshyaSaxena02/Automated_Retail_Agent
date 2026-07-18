# ============================================================
# IDAM — Intelligent Automated Retail Store Backend
# app/services/recommendation_service.py
#
# PURPOSE:
#   Orchestrates the recommendation pipeline from the API layer.
#   The only file that talks to both the DB and the engine.
#
# RESPONSIBILITIES:
#   1. Validate the customer exists (raises ValueError if not)
#   2. Load CustomerMemory, Customer, and Order history from DB
#   3. Call recommendation_engine.run() with the loaded data
#   4. Convert ScoredProduct list → RecommendationResponse schema
#
# ERROR HANDLING:
#   ValueError (customer not found) → caller raises HTTPException(404)
#   All other exceptions propagate naturally (caught by FastAPI).
#
# DEPENDENCY INJECTION:
#   Receives db: Session via FastAPI's Depends(get_db).
#   Never creates its own DB session.
# ============================================================

import logging
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.ai.recommendation.recommendation_engine import run as run_engine
from app.schemas.recommendation import (
    RecommendationResponse,
    RecommendedProductItem,
)
from app.services.customer_service import (
    get_customer_by_id,
    get_customer_memory,
    get_customer_orders,
)

logger = logging.getLogger(__name__)


def get_recommendations(
    db:          Session,
    customer_id: str,
    query:       Optional[str] = None,
    top_k:       Optional[int] = None,
) -> RecommendationResponse:
    """
    Generate personalised product recommendations for a customer.

    Full pipeline:
      1. Validate + load customer
      2. Load memory and orders from DB
      3. Run recommendation engine (candidate gen → filter → score)
      4. Build and return RecommendationResponse

    Args:
        db          : Active SQLAlchemy session (injected by FastAPI)
        customer_id : Customer's string ID, e.g. 'CUST001'
        query       : Optional natural-language intent string
        top_k       : Override for number of results (uses settings default if None)

    Returns:
        RecommendationResponse — scored, ranked product list with full metadata

    Raises:
        HTTPException(404) — if the customer_id does not exist
        HTTPException(500) — on unexpected engine failure
    """
    logger.info(
        f"[RecService] get_recommendations: customer='{customer_id}' | "
        f"query={repr(query)} | top_k={top_k}"
    )

    # ── Step 1: Validate customer ─────────────────────────────
    customer = get_customer_by_id(db, customer_id)
    if not customer:
        logger.warning(f"[RecService] Customer '{customer_id}' not found.")
        raise HTTPException(
            status_code=404,
            detail=f"Customer '{customer_id}' not found. "
                   "Ensure the customer_id matches a valid customer in the system.",
        )

    # ── Step 2: Load memory ───────────────────────────────────
    memory = get_customer_memory(db, customer_id)
    if not memory:
        # Memory row should always exist (seed data or memory_engine creates it)
        # If missing, raise 404 rather than crashing
        logger.warning(
            f"[RecService] No CustomerMemory found for '{customer_id}'. "
            "Ensure the customer has been seeded or has made at least one purchase."
        )
        raise HTTPException(
            status_code=404,
            detail=(
                f"No memory profile found for customer '{customer_id}'. "
                "The customer may not have any purchase history yet. "
                "Recommendations will be available after the first purchase."
            ),
        )

    # ── Step 3: Load order history ────────────────────────────
    orders_data  = get_customer_orders(db, customer_id)
    order_list   = orders_data.get("orders", []) if orders_data else []

    logger.info(
        f"[RecService] Loaded {len(order_list)} orders for '{customer_id}'."
    )

    # ── Step 4: Run the recommendation engine ─────────────────
    try:
        result = run_engine(
            db       = db,
            customer = customer,
            memory   = memory,
            orders   = order_list,
            query    = query,
            top_k    = top_k,
        )
    except Exception as exc:
        logger.exception(
            f"[RecService] Recommendation engine failed for '{customer_id}': {exc}"
        )
        raise HTTPException(
            status_code=500,
            detail=(
                f"Recommendation engine encountered an error: {str(exc)}. "
                "Please try again or contact support."
            ),
        ) from exc

    # ── Step 5: Build API response ────────────────────────────
    profile = result.customer_profile

    recommended_products = [
        RecommendedProductItem(
            rank             = idx + 1,
            product_id       = sp.product.product_id,
            name             = sp.product.name,
            category         = sp.product.category,
            brand            = sp.product.brand or "",
            price            = sp.product.price,
            stock            = sp.product.stock,
            final_score      = sp.final_score,
            interest_score   = sp.interest_score,
            semantic_score   = sp.semantic_score,
            budget_score     = sp.budget_score,
            frequency_score  = sp.frequency_score,
            popularity_score = sp.popularity_score,
            reason           = sp.reason,
        )
        for idx, sp in enumerate(result.scored_products)
    ]

    response = RecommendationResponse(
        customer_id          = customer_id,
        customer_name        = customer.name,
        estimated_budget     = profile.get("budget_estimate", 0.0),
        budget_period        = profile.get("budget_period", "unknown"),
        query_used           = result.query_used,
        total_recommended    = len(recommended_products),
        recommended_products = recommended_products,
    )

    logger.info(
        f"[RecService] Returning {len(recommended_products)} recommendations "
        f"for customer '{customer_id}'."
    )

    return response
