# ============================================================
# app/services/customer_service.py
#
# PURPOSE:
#   Business logic for customers, their memory, and orders.
#   API routes call these functions — no raw DB queries in routes.
#
# FUNCTIONS:
#   get_all_customers()          — List all customers
#   get_customer_by_id()         — Fetch one customer profile
#   get_customer_memory()        — Fetch customer's AI memory
#   get_customer_orders()        — Fetch all orders for a customer
#   get_current_budget_estimate()— Estimate budget based on today's date
# ============================================================

from datetime import datetime
from typing import Optional, List
from sqlalchemy.orm import Session, joinedload

from app.database.models import Customer, CustomerMemory, Order, Product


def get_all_customers(db: Session) -> List[Customer]:
    """Return all customers. Used by GET /customers."""
    return db.query(Customer).order_by(Customer.id).all()


def get_customer_by_id(db: Session, customer_id: str) -> Optional[Customer]:
    """
    Fetch a single customer by their customer_id string (e.g. 'CUST001').
    Returns None if not found — the router converts this to a 404.
    """
    return db.query(Customer).filter(Customer.customer_id == customer_id).first()


def get_customer_memory(
    db: Session, customer_id: str
) -> Optional[CustomerMemory]:
    """
    Fetch the AI memory row for a customer.

    This is the central data source for the recommendation engine.
    It contains:
    - Purchased categories and brands
    - Dynamic budget averages (start/mid/end of month)
    - Monthly shopping patterns
    - Expanding category interests

    Also computes 'current_budget_estimate' based on today's day-of-month
    and attaches it to the memory object as a dynamic attribute.
    """
    memory = (
        db.query(CustomerMemory)
        .filter(CustomerMemory.customer_id == customer_id)
        .first()
    )

    if memory:
        # Attach current budget estimate as a dynamic attribute.
        # The Pydantic schema picks this up via current_budget_estimate field.
        memory.current_budget_estimate = get_current_budget_estimate(memory)

    return memory


def get_current_budget_estimate(memory: CustomerMemory) -> float:
    """
    Estimate the customer's budget ceiling based on today's day-of-month
    and their historical spending averages.

    Budget periods:
      Days  1–10  → avg_budget_start  (typically highest — just got paid)
      Days 11–20  → avg_budget_mid    (moderate spending)
      Days 21–31  → avg_budget_end    (lowest — nearing next salary)

    Returns 0.0 if no history is available yet.

    This function is also used by the recommendation engine (Phase 8)
    to filter products within the customer's expected budget.
    """
    today = datetime.utcnow().day  # Day of current month (1–31)

    if today <= 10:
        estimate = memory.avg_budget_start
        period = "start of month"
    elif today <= 20:
        estimate = memory.avg_budget_mid
        period = "mid month"
    else:
        estimate = memory.avg_budget_end
        period = "end of month"

    # Store period label too (used in recommendation explanations)
    memory._budget_period = period
    return estimate


def get_customer_orders(
    db: Session, customer_id: str
) -> Optional[dict]:
    """
    Return all orders for a customer, enriched with product details.

    Joins the Order table with the Product table so each order row
    includes product_name, product_category, and product_brand.

    Used by:
    - GET /customers/{customer_id}/orders (Phase 3)
    - Memory engine (Phase 5) when rebuilding customer preferences
    - Recommendation engine (Phase 8) for purchase history context
    """
    customer = get_customer_by_id(db, customer_id)
    if not customer:
        return None

    # Join orders with products to get product details in one query
    rows = (
        db.query(Order, Product)
        .join(Product, Order.product_id == Product.product_id)
        .filter(Order.customer_id == customer_id)
        .order_by(Order.purchased_at.desc())
        .all()
    )

    orders = []
    total_spend = 0.0

    for order, product in rows:
        orders.append({
            "id": order.id,
            "product_id": order.product_id,
            "product_name": product.name,
            "product_category": product.category,
            "product_brand": product.brand,
            "quantity": order.quantity,
            "price_paid": order.price_paid,
            "purchased_at": order.purchased_at,
        })
        total_spend += order.price_paid

    return {
        "customer_id": customer_id,
        "customer_name": customer.name,
        "total_orders": len(orders),
        "total_spend": total_spend,
        "orders": orders,
    }
