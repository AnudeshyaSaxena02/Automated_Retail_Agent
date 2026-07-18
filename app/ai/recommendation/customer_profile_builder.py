# ============================================================
# IDAM — Intelligent Automated Retail Store Backend
# app/ai/recommendation/customer_profile_builder.py
#
# PURPOSE:
#   Converts a CustomerMemory ORM row into a clean, structured
#   profile dict ready for prompt injection.
#
# WHAT IT PRODUCES:
#   A "customer_profile" dict consumed by build_rag_prompt().
#   The dict contains everything the LLM needs to personalise
#   a recommendation — budget, brands, history, interests.
#
# PROFILE DICT SCHEMA:
#   {
#     "customer_id":       "CUST001",
#     "name":              "Rahul Sharma",
#     "budget_estimate":   58999.0,    ← based on today's date
#     "budget_period":     "start of month",
#     "preferred_brands":  ["Lenovo", "Sony"],
#     "purchased_categories": ["Laptops", "Accessories"],
#     "category_interests":   ["Laptops", "Accessories", "Audio"],
#     "total_purchases":   4,
#     "total_spend":       104987.0,
#     "is_budget_conscious": False,    ← True if avg spend < 5000
#     "summary":  "Human-readable one-liner for prompt injection",
#   }
#
# PHASE 9 EXTENSION:
#   This builder can be extended with collaborative filtering signals
#   (e.g., "customers like Rahul also bought...") without changing
#   the prompt_builder or service layer.
# ============================================================

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from app.database.models import CustomerMemory, Customer
from app.database.models import json_to_list

logger = logging.getLogger(__name__)

# Threshold below which we consider a customer "budget-conscious"
# Used to adjust LLM recommendation tone and product filtering
_BUDGET_CONSCIOUS_THRESHOLD = 5000.0


def _get_budget_estimate(memory: CustomerMemory) -> tuple:
    """
    Return (budget_estimate: float, period_label: str) based on today.

    Uses the three-period budget model from Phase 4:
      Days  1–10  → avg_budget_start  (post-salary, highest spend)
      Days 11–20  → avg_budget_mid    (moderate spend)
      Days 21–31  → avg_budget_end    (pre-salary, lowest spend)

    Returns (0.0, "unknown") if no purchase history exists yet.
    """
    day = datetime.utcnow().day

    if day <= 10:
        estimate = memory.avg_budget_start or 0.0
        period   = "start of month"
    elif day <= 20:
        estimate = memory.avg_budget_mid or 0.0
        period   = "mid month"
    else:
        estimate = memory.avg_budget_end or 0.0
        period   = "end of month"

    return estimate, period


def build_customer_profile(
    memory: CustomerMemory,
    customer: Optional[Customer] = None,
) -> Dict[str, Any]:
    """
    Build a structured customer profile dict from a CustomerMemory row.

    Called by llm_service.handle_rag_query() when customer_id is provided.
    The returned dict is passed directly to build_rag_prompt() as
    the customer_profile argument.

    Args:
        memory   : CustomerMemory ORM object (the AI memory for this customer)
        customer : Customer ORM object (for name). Optional — used for display only.

    Returns:
        Profile dict with budget, brands, interests, and a summary string.
    """
    budget_estimate, budget_period = _get_budget_estimate(memory)

    preferred_brands    = json_to_list(memory.preferred_brands)
    purchased_categories = json_to_list(memory.purchased_categories)
    category_interests  = json_to_list(memory.category_interests)

    is_budget_conscious = (
        budget_estimate > 0 and budget_estimate < _BUDGET_CONSCIOUS_THRESHOLD
    )

    # Build a human-readable summary for prompt injection
    budget_str = f"₹{budget_estimate:,.0f}" if budget_estimate > 0 else "unknown"
    brands_str = ", ".join(preferred_brands[:4]) if preferred_brands else "no preference"
    cats_str   = ", ".join(purchased_categories[:4]) if purchased_categories else "none yet"

    summary_parts = [
        f"Budget: ~{budget_str} ({budget_period})",
        f"Preferred brands: {brands_str}",
        f"Has bought: {cats_str}",
    ]
    if is_budget_conscious:
        summary_parts.append("Prefers affordable / budget options")

    summary = " | ".join(summary_parts)

    profile: Dict[str, Any] = {
        "customer_id":          memory.customer_id,
        "name":                 customer.name if customer else memory.customer_id,
        "budget_estimate":      budget_estimate,
        "budget_period":        budget_period,
        "preferred_brands":     preferred_brands,
        "purchased_categories": purchased_categories,
        "category_interests":   category_interests,
        "total_purchases":      memory.total_purchases or 0,
        "total_spend":          memory.total_spend or 0.0,
        "is_budget_conscious":  is_budget_conscious,
        "summary":              summary,
    }

    logger.debug(
        f"[ProfileBuilder] Built profile for '{memory.customer_id}': {summary}"
    )

    return profile
