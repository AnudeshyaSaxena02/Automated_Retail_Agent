# ============================================================
# app/api/customers.py
#
# PURPOSE:
#   FastAPI router for all customer-related endpoints.
#   Routes delegate all logic to customer_service.py.
#
# ENDPOINTS:
#   GET /customers                          — List all customers
#   GET /customers/{customer_id}            — Get customer profile
#   GET /customers/{customer_id}/memory     — Get full AI memory
#   GET /customers/{customer_id}/orders     — Get order history
# ============================================================

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.schemas.customer import (
    CustomerResponse, CustomerListResponse,
    CustomerMemoryResponse, CustomerOrdersResponse,
)
from app.services import customer_service

router = APIRouter()


@router.get("", response_model=CustomerListResponse, summary="List all customers")
def list_customers(db: Session = Depends(get_db)):
    """
    Return all registered customers.

    Useful for:
    - Admin overview
    - Picking a Customer ID for demo testing
    - Future multi-customer analytics
    """
    customers = customer_service.get_all_customers(db)
    return {"total": len(customers), "customers": customers}


@router.get("/{customer_id}", response_model=CustomerResponse, summary="Get customer profile")
def get_customer(customer_id: str, db: Session = Depends(get_db)):
    """
    Get basic profile for a customer by their Customer ID.

    Example: /customers/CUST001
    """
    customer = customer_service.get_customer_by_id(db, customer_id)
    if not customer:
        raise HTTPException(
            status_code=404,
            detail=f"Customer '{customer_id}' not found."
        )
    return customer


@router.get("/{customer_id}/memory", response_model=CustomerMemoryResponse, summary="Get customer AI memory")
def get_customer_memory(customer_id: str, db: Session = Depends(get_db)):
    """
    Get the full evolving AI memory for a customer.

    Returns:
    - Purchase categories, brands, and favorite products
    - Dynamic budget averages: start / mid / end of month
    - Monthly shopping pattern (which categories per week)
    - Expanding interest list (grows with every new category purchased)
    - Current budget estimate based on today's date

    This is the data the recommendation engine reads in Phase 8.

    Example: /customers/CUST001/memory
    """
    # Verify customer exists first
    customer = customer_service.get_customer_by_id(db, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail=f"Customer '{customer_id}' not found.")

    memory = customer_service.get_customer_memory(db, customer_id)
    if not memory:
        raise HTTPException(
            status_code=404,
            detail=f"No memory record found for customer '{customer_id}'. "
                   "Memory is created after the first purchase."
        )
    return memory


@router.get("/{customer_id}/orders", response_model=CustomerOrdersResponse, summary="Get customer order history")
def get_customer_orders(customer_id: str, db: Session = Depends(get_db)):
    """
    Get full purchase history for a customer, enriched with product details.

    Each order includes:
    - Product name, category, and brand
    - Price paid at time of purchase
    - Purchase timestamp (used for time-of-month pattern analysis)

    Used by:
    - Frontend order history display
    - Recommendation engine (Phase 8) for context building
    - Memory engine (Phase 5) when recalculating preferences

    Example: /customers/CUST001/orders
    """
    result = customer_service.get_customer_orders(db, customer_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"Customer '{customer_id}' not found.")
    return result
