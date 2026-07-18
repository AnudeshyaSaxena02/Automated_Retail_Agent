# ============================================================
# app/services/order_service.py
#
# PURPOSE:
#   Orchestrates the complete purchase flow.
#
# PURCHASE FLOW:
#   1. Validate customer exists
#   2. Validate product exists + has stock
#   3. Save Order row to database
#   4. Save BudgetHistory row (raw spend data for analytics)
#   5. Call memory_engine.update_memory() → updates CustomerMemory
#   6. Return purchase confirmation with memory update summary
#
# WHY THIS ORDER MATTERS:
#   Steps 3–5 must all succeed together.
#   If memory update fails, the order is still saved (order is
#   the source of truth). Memory can be rebuilt from orders.
# ============================================================

from datetime import datetime
from sqlalchemy.orm import Session

from app.database.models import Customer, Product, Order, BudgetHistory
from app.schemas.order import PurchaseRequest, PurchaseResponse, MemoryUpdateSummary
from app.ai.memory.memory_engine import update_memory, get_memory_summary


def _week_of_month(dt: datetime) -> int:
    """Return week number within the month (1–5)."""
    return (dt.day - 1) // 7 + 1


def process_purchase(db: Session, request: PurchaseRequest) -> PurchaseResponse:
    """
    Execute a complete purchase transaction.

    This is the most important service function in Phase 4.
    Every call to this function triggers memory learning.

    Args:
        db      : Active database session
        request : PurchaseRequest with customer_id, product_id, quantity

    Returns:
        PurchaseResponse — order confirmation + memory update summary

    Raises:
        ValueError : If customer or product not found, or no stock
    """

    # ── Step 1: Validate customer ──────────────────────────
    customer = (
        db.query(Customer)
        .filter(Customer.customer_id == request.customer_id)
        .first()
    )
    if not customer:
        raise ValueError(f"Customer '{request.customer_id}' not found.")

    # ── Step 2: Validate product ───────────────────────────
    product = (
        db.query(Product)
        .filter(Product.product_id == request.product_id)
        .first()
    )
    if not product:
        raise ValueError(f"Product '{request.product_id}' not found.")

    if product.stock < request.quantity:
        raise ValueError(
            f"Insufficient stock. Requested {request.quantity}, "
            f"available {product.stock}."
        )

    # ── Step 3: Save the Order ─────────────────────────────
    total_price = product.price * request.quantity
    purchase_time = datetime.utcnow()

    order = Order(
        customer_id  = request.customer_id,
        product_id   = request.product_id,
        quantity     = request.quantity,
        price_paid   = total_price,
        purchased_at = purchase_time,
    )
    db.add(order)
    db.flush()  # flush to get order.id without full commit yet

    # ── Step 4: Save BudgetHistory row ────────────────────
    # Stores raw spend data for computing budget averages
    budget_record = BudgetHistory(
        customer_id  = request.customer_id,
        amount       = total_price,
        day_of_month = purchase_time.day,
        week_of_month= _week_of_month(purchase_time),
        month        = purchase_time.month,
        year         = purchase_time.year,
        purchased_at = purchase_time,
    )
    db.add(budget_record)

    # ── Step 5: Reduce product stock ──────────────────────
    product.stock = max(0, product.stock - request.quantity)

    # Commit order + budget + stock change together
    db.commit()
    db.refresh(order)

    # ── Step 6: Update Customer Memory ────────────────────
    # This is where the AI learning happens.
    # memory_engine reads the existing memory, updates all fields,
    # and saves it back to the database.
    updated_memory = update_memory(
        db          = db,
        customer_id = request.customer_id,
        product     = product,
        order       = order,
    )

    # ── Step 7: Build response ─────────────────────────────
    memory_summary = get_memory_summary(updated_memory)

    return PurchaseResponse(
        success      = True,
        message      = (
            f"Purchase successful! Memory updated. "
            f"Estimated budget for {memory_summary['budget_period']}: "
            f"INR {memory_summary['estimated_budget']:,.0f}"
        ),
        order_id     = order.id,
        customer_id  = request.customer_id,
        product_id   = request.product_id,
        product_name = product.name,
        quantity     = request.quantity,
        price_paid   = total_price,
        purchased_at = purchase_time,
        memory_updated = MemoryUpdateSummary(**memory_summary),
    )
