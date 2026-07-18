# ============================================================
# IDAM — Intelligent Automated Retail Store Backend
# app/ai/recommendation/filters.py
#
# PURPOSE:
#   Remove products that should never appear in recommendations.
#
# FILTERS APPLIED (in order):
#   1. filter_out_of_stock      — Remove products with stock == 0
#   2. filter_recently_purchased— Remove products bought within
#                                 recency_days (default: 30 days)
#
# WHY A SEPARATE MODULE?
#   Keeps filtering concerns completely independent of scoring.
#   Each filter is a pure function — easy to test, easy to extend
#   (e.g., add a "not discontinued" filter later without touching
#   the scoring or engine code).
#
# IMPORTANT:
#   Filters ONLY remove from the candidate pool — they never add.
#   apply_all_filters() is the only public entry point; call it
#   from recommendation_engine.py to run all filters in sequence.
# ============================================================

import logging
from datetime import datetime, timedelta
from typing import List, Set

from sqlalchemy.orm import Session

from app.ai.recommendation.candidate_generator import CandidateProduct
from app.database.models import Order

logger = logging.getLogger(__name__)


# ── Filter 1: Out-of-stock ────────────────────────────────────

def filter_out_of_stock(candidates: List[CandidateProduct]) -> List[CandidateProduct]:
    """
    Remove any product with zero stock from the candidate pool.

    A product with stock == 0 cannot be purchased, so recommending
    it would frustrate customers. This is the highest-priority filter.

    Args:
        candidates : List of CandidateProduct to filter

    Returns:
        Filtered list with only in-stock products
    """
    before = len(candidates)
    result = [c for c in candidates if c.product.stock > 0]
    removed = before - len(result)

    if removed:
        logger.info(f"[Filters] Removed {removed} out-of-stock product(s).")
    return result


# ── Filter 2: Recently purchased ─────────────────────────────

def _get_recently_purchased_ids(
    db: Session,
    customer_id: str,
    recency_days: int,
) -> Set[str]:
    """
    Return the set of product_ids the customer purchased within
    the last `recency_days` days.

    Uses a single SQLite query to avoid N+1 problems.
    Returns an empty set if the customer has no recent orders
    or on any database error (fails safe — no filtering done).

    Args:
        db           : SQLAlchemy session
        customer_id  : Customer whose orders to check
        recency_days : Lookback window in days

    Returns:
        Set[str] of product_ids purchased recently
    """
    try:
        cutoff = datetime.utcnow() - timedelta(days=recency_days)
        recent_orders = (
            db.query(Order.product_id)
            .filter(
                Order.customer_id == customer_id,
                Order.purchased_at >= cutoff,
            )
            .all()
        )
        recent_ids = {row.product_id for row in recent_orders}
        logger.debug(
            f"[Filters] Customer '{customer_id}' has {len(recent_ids)} "
            f"recently purchased product(s) in last {recency_days} days."
        )
        return recent_ids

    except Exception as exc:
        logger.warning(
            f"[Filters] Failed to fetch recent orders for '{customer_id}': {exc}. "
            "Skipping recency filter (all candidates kept)."
        )
        return set()


def filter_recently_purchased(
    candidates: List[CandidateProduct],
    db: Session,
    customer_id: str,
    recency_days: int = 30,
) -> List[CandidateProduct]:
    """
    Remove products the customer has purchased in the last N days.

    We avoid re-recommending very recent purchases because the
    customer already has them — recommending them again adds no value
    and makes the engine look unaware of the customer's history.

    Note: Products purchased LONGER ago than recency_days are kept.
    The idea is that after ~30 days, suggesting consumables or
    accessories again may be valid (e.g., power bank, notebooks).

    Args:
        candidates   : List of CandidateProduct to filter
        db           : SQLAlchemy session
        customer_id  : The requesting customer's ID
        recency_days : Lookback window (default 30 days)

    Returns:
        Filtered list excluding recent purchases
    """
    if not candidates:
        return candidates

    recent_ids = _get_recently_purchased_ids(db, customer_id, recency_days)
    if not recent_ids:
        return candidates  # Nothing to filter

    before = len(candidates)
    result = [c for c in candidates if c.product.product_id not in recent_ids]
    removed = before - len(result)

    if removed:
        logger.info(
            f"[Filters] Removed {removed} recently purchased product(s) "
            f"(last {recency_days} days) for customer '{customer_id}'."
        )
    return result


# ── Composite filter ──────────────────────────────────────────

def apply_all_filters(
    candidates: List[CandidateProduct],
    db: Session,
    customer_id: str,
    recency_days: int = 30,
) -> List[CandidateProduct]:
    """
    Run all filters in sequence on the candidate pool.

    Order matters:
      1. filter_out_of_stock        (fastest check, no DB needed)
      2. filter_recently_purchased  (requires one DB query)

    This is the ONLY public function the recommendation engine
    should call. Adding a new filter means adding it here.

    Args:
        candidates   : Raw candidate pool from candidate_generator
        db           : SQLAlchemy session
        customer_id  : The requesting customer's ID
        recency_days : Lookback window for recency filter

    Returns:
        Cleaned candidate pool, ready for scoring
    """
    original_count = len(candidates)

    # Step 1: remove out-of-stock products
    candidates = filter_out_of_stock(candidates)

    # Step 2: remove recently purchased products
    candidates = filter_recently_purchased(
        candidates, db, customer_id, recency_days
    )

    logger.info(
        f"[Filters] Filtering complete: {original_count} candidates → {len(candidates)} "
        f"after all filters."
    )
    return candidates
