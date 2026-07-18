# ============================================================
# app/ai/memory/memory_engine.py
#
# PURPOSE:
#   The core of the "continuous learning" system.
#   Called automatically after every purchase to update the
#   customer's evolving AI memory.
#
# WHAT IT UPDATES:
#   - purchased_categories   (append new, no duplicates)
#   - preferred_brands       (append new, no duplicates)
#   - favorite_products      (append product_id, no duplicates)
#   - category_interests     (ONLY grows — never shrinks)
#   - monthly_pattern        (which categories per week of month)
#   - avg_budget_start/mid/end (running averages by time-of-month)
#   - budget_count_start/mid/end (counts for running averages)
#   - total_purchases, total_spend
#   - last_visit, updated_at
#
# HOW RUNNING AVERAGES WORK:
#   new_avg = (old_avg * old_count + new_amount) / (old_count + 1)
#   This is a cumulative moving average that improves over time.
#
# BUDGET PERIODS:
#   Days  1–10  → start (typically highest spend — just got paid)
#   Days 11–20  → mid   (moderate spending)
#   Days 21–31  → end   (lowest spend — nearing next salary)
#
# WEEK-OF-MONTH MAPPING (for monthly_pattern):
#   Days  1–7   → "week1"
#   Days  8–14  → "week2"
#   Days 15–21  → "week3"
#   Days 22–31  → "week4"
# ============================================================

import json
from datetime import datetime
from sqlalchemy.orm import Session

from app.database.models import CustomerMemory, Product, Order


# ── JSON helpers (local — no circular import) ─────────────
def _load_list(val: str) -> list:
    try:
        return json.loads(val) if val else []
    except Exception:
        return []

def _load_dict(val: str) -> dict:
    try:
        return json.loads(val) if val else {}
    except Exception:
        return {}

def _append_unique(lst: list, item: str) -> list:
    """Append item to list only if not already present. Preserves order."""
    if item and item not in lst:
        lst.append(item)
    return lst


def _get_budget_period(day_of_month: int) -> str:
    """Map a day of month (1–31) to budget period label."""
    if day_of_month <= 10:
        return "start"
    elif day_of_month <= 20:
        return "mid"
    else:
        return "end"


def _get_week_label(day_of_month: int) -> str:
    """Map a day of month to its week label for monthly_pattern."""
    if day_of_month <= 7:
        return "week1"
    elif day_of_month <= 14:
        return "week2"
    elif day_of_month <= 21:
        return "week3"
    else:
        return "week4"


def _update_running_average(old_avg: float, old_count: int, new_value: float) -> float:
    """
    Compute a cumulative moving average.

    Formula: new_avg = (old_avg * old_count + new_value) / (old_count + 1)

    This is mathematically equivalent to recalculating the average
    from scratch each time, but much more efficient — we only need
    the current average and count, not the full history.
    """
    return (old_avg * old_count + new_value) / (old_count + 1)


# ── Main update function ───────────────────────────────────

def update_memory(
    db: Session,
    customer_id: str,
    product: Product,
    order: Order,
) -> CustomerMemory:
    """
    Update a customer's AI memory after a purchase.

    This is the central function of the continuous learning system.
    It is called by order_service.py immediately after saving an order.

    Args:
        db          : Active database session
        customer_id : The customer who made the purchase
        product     : The Product ORM object that was purchased
        order       : The saved Order ORM object (has price_paid, purchased_at)

    Returns:
        The updated CustomerMemory object (already committed to DB)
    """

    # ── Step 1: Load the customer's memory row ─────────────
    memory = (
        db.query(CustomerMemory)
        .filter(CustomerMemory.customer_id == customer_id)
        .first()
    )

    if not memory:
        # Should not happen if seed data exists, but handle gracefully
        memory = CustomerMemory(customer_id=customer_id)
        db.add(memory)

    # ── Step 2: Parse all JSON columns into Python objects ─
    categories   = _load_list(memory.purchased_categories)
    brands       = _load_list(memory.preferred_brands)
    fav_products = _load_list(memory.favorite_products)
    interests    = _load_list(memory.category_interests)
    pattern      = _load_dict(memory.monthly_pattern)

    # ── Step 3: Extract purchase metadata ─────────────────
    purchase_dt  = order.purchased_at
    day          = purchase_dt.day
    price        = order.price_paid
    category     = product.category
    brand        = product.brand or ""
    product_id   = product.product_id

    # ── Step 4: Update category + brand lists ─────────────
    categories   = _append_unique(categories, category)
    brands       = _append_unique(brands, brand) if brand else brands
    fav_products = _append_unique(fav_products, product_id)

    # category_interests ONLY grows — never shrinks
    # This captures evolving customer interests over time
    interests    = _append_unique(interests, category)

    # ── Step 5: Update monthly shopping pattern ───────────
    # Records which categories the customer buys in each week
    week_label = _get_week_label(day)
    week_cats  = pattern.get(week_label, [])
    if category not in week_cats:
        week_cats.append(category)
    pattern[week_label] = week_cats

    # ── Step 6: Update dynamic budget averages ────────────
    period = _get_budget_period(day)

    if period == "start":
        memory.avg_budget_start = _update_running_average(
            memory.avg_budget_start, memory.budget_count_start, price
        )
        memory.budget_count_start += 1

    elif period == "mid":
        memory.avg_budget_mid = _update_running_average(
            memory.avg_budget_mid, memory.budget_count_mid, price
        )
        memory.budget_count_mid += 1

    else:  # end
        memory.avg_budget_end = _update_running_average(
            memory.avg_budget_end, memory.budget_count_end, price
        )
        memory.budget_count_end += 1

    # ── Step 7: Update totals ─────────────────────────────
    memory.total_purchases += 1
    memory.total_spend     += price

    # ── Step 8: Update visit tracking ────────────────────
    memory.last_visit  = datetime.utcnow()
    memory.updated_at  = datetime.utcnow()
    memory.visit_count = (memory.visit_count or 0) + 1

    # ── Step 9: Save JSON columns back as strings ─────────
    memory.purchased_categories = json.dumps(categories)
    memory.preferred_brands     = json.dumps(brands)
    memory.favorite_products    = json.dumps(fav_products)
    memory.category_interests   = json.dumps(interests)
    memory.monthly_pattern      = json.dumps(pattern)

    # ── Step 10: Commit ───────────────────────────────────
    db.commit()
    db.refresh(memory)

    return memory


def get_memory_summary(memory: CustomerMemory) -> dict:
    """
    Return a concise, human-readable summary of a customer's memory.
    Used in the purchase response to show what was learned.
    Used by the recommendation engine to build LLM context.
    """
    today = datetime.utcnow().day

    if today <= 10:
        budget_estimate = memory.avg_budget_start
        period_label    = "start of month"
    elif today <= 20:
        budget_estimate = memory.avg_budget_mid
        period_label    = "mid month"
    else:
        budget_estimate = memory.avg_budget_end
        period_label    = "end of month"

    return {
        "customer_id":         memory.customer_id,
        "total_purchases":     memory.total_purchases,
        "total_spend":         memory.total_spend,
        "purchased_categories": _load_list(memory.purchased_categories),
        "preferred_brands":    _load_list(memory.preferred_brands),
        "category_interests":  _load_list(memory.category_interests),
        "monthly_pattern":     _load_dict(memory.monthly_pattern),
        "budget_period":       period_label,
        "estimated_budget":    round(budget_estimate, 2),
        "last_visit":          memory.last_visit,
    }
