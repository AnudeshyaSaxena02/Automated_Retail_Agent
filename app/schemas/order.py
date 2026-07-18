# ============================================================
# app/schemas/order.py
#
# Pydantic schemas for the Purchase API.
#
# SCHEMAS:
#   PurchaseRequest  — what the client sends
#   PurchaseResponse — what the API returns after a purchase
#   MemoryUpdateSummary — shows what the memory engine learned
# ============================================================

from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class PurchaseRequest(BaseModel):
    """
    Request body for POST /orders/purchase.

    No authentication — Customer ID is passed directly.
    The system trusts that the caller provides the correct customer_id.
    """
    customer_id: str = Field(..., example="CUST001", description="Customer making the purchase")
    product_id: str  = Field(..., example="PROD001", description="Product being purchased")
    quantity: int    = Field(default=1, ge=1, le=100, description="Number of units")


class MemoryUpdateSummary(BaseModel):
    """
    Summary of what the memory engine learned from this purchase.
    Included in PurchaseResponse so the caller can see the AI learning.
    """
    total_purchases:      int
    total_spend:          float
    purchased_categories: List[str]
    preferred_brands:     List[str]
    category_interests:   List[str]
    monthly_pattern:      Dict[str, Any]
    budget_period:        str   # "start of month" | "mid month" | "end of month"
    estimated_budget:     float # current estimated budget ceiling in INR


class PurchaseResponse(BaseModel):
    """
    Response returned after a successful purchase.

    Includes:
    - Order confirmation details
    - Updated memory summary (shows what the AI learned)
    """
    success:      bool = True
    message:      str
    order_id:     int
    customer_id:  str
    product_id:   str
    product_name: str
    quantity:     int
    price_paid:   float
    purchased_at: datetime
    memory_updated: MemoryUpdateSummary
