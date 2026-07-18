# ============================================================
# app/schemas/customer.py
#
# Pydantic models for the Customer API.
#
# SCHEMAS:
#   CustomerResponse        — Basic customer profile
#   CustomerMemoryResponse  — Full AI memory (parsed JSON fields)
#   OrderItemResponse       — Single order with product details
#   CustomerOrdersResponse  — All orders for a customer
# ============================================================

import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator


# ── Helper ────────────────────────────────────────────────
def safe_json_list(v) -> list:
    if isinstance(v, str):
        try:
            return json.loads(v)
        except Exception:
            return []
    return v or []


def safe_json_dict(v) -> dict:
    if isinstance(v, str):
        try:
            return json.loads(v)
        except Exception:
            return {}
    return v or {}


# ── Customer ──────────────────────────────────────────────

class CustomerResponse(BaseModel):
    """Basic customer profile — returned by GET /customers/{customer_id}."""

    id: int
    customer_id: str
    name: str
    email: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class CustomerListResponse(BaseModel):
    """Wrapper for GET /customers."""
    total: int
    customers: List[CustomerResponse]


# ── Customer Memory ───────────────────────────────────────

class CustomerMemoryResponse(BaseModel):
    """
    Full AI memory for a customer.
    All JSON columns are returned as Python lists/dicts.
    Returned by GET /customers/{customer_id}/memory.

    This is the most important response schema for the AI modules.
    The recommendation engine reads this directly.
    """

    customer_id: str
    purchased_categories: List[str] = []
    preferred_brands: List[str] = []
    favorite_products: List[str] = []
    total_purchases: int
    total_spend: float

    # Dynamic budget averages — the core of budget learning
    avg_budget_start: float = Field(description="Avg spend on days 1-10 of month")
    avg_budget_mid: float   = Field(description="Avg spend on days 11-20 of month")
    avg_budget_end: float   = Field(description="Avg spend on days 21-31 of month")

    monthly_pattern: Dict[str, Any] = {}
    category_interests: List[str] = []
    visit_count: int
    last_visit: Optional[datetime]
    updated_at: Optional[datetime]

    # Computed field added by the service layer
    current_budget_estimate: Optional[float] = Field(
        None,
        description="Estimated budget based on today's date + spending history"
    )

    @field_validator("purchased_categories", "preferred_brands",
                     "favorite_products", "category_interests", mode="before")
    @classmethod
    def parse_lists(cls, v):
        return safe_json_list(v)

    @field_validator("monthly_pattern", mode="before")
    @classmethod
    def parse_dict(cls, v):
        return safe_json_dict(v)

    model_config = {"from_attributes": True}


# ── Orders ────────────────────────────────────────────────

class OrderItemResponse(BaseModel):
    """
    A single order row enriched with product name and category.
    Used in GET /customers/{customer_id}/orders.

    The recommendation engine uses order history to detect:
    - Preferred categories
    - Preferred brands
    - Time-of-month shopping patterns
    """

    id: int
    product_id: str
    product_name: Optional[str] = None      # Joined from products table
    product_category: Optional[str] = None  # Joined from products table
    product_brand: Optional[str] = None     # Joined from products table
    quantity: int
    price_paid: float
    purchased_at: datetime

    model_config = {"from_attributes": True}


class CustomerOrdersResponse(BaseModel):
    """All orders for a customer — returned by GET /customers/{customer_id}/orders."""
    customer_id: str
    customer_name: str
    total_orders: int
    total_spend: float
    orders: List[OrderItemResponse]
