# ============================================================
# app/api/orders.py
#
# PURPOSE:
#   FastAPI router for the purchase endpoint.
#
# ENDPOINT:
#   POST /orders/purchase
#     — Records a purchase
#     — Triggers memory update
#     — Returns confirmation + what the AI learned
#
# WHY ONE ENDPOINT?
#   For this prototype, a single purchase endpoint is sufficient.
#   It handles the full pipeline. More order endpoints (order list,
#   cancel order, etc.) can be added later if needed.
# ============================================================

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.schemas.order import PurchaseRequest, PurchaseResponse
from app.services import order_service

router = APIRouter()


@router.post(
    "/purchase",
    response_model=PurchaseResponse,
    status_code=201,
    summary="Purchase a product (triggers memory update)",
)
def purchase_product(
    request: PurchaseRequest,
    db: Session = Depends(get_db),
):
    """
    Record a product purchase and update the customer's AI memory.

    **This is the core learning endpoint.**

    After every purchase:
    - A new Order record is saved
    - A BudgetHistory record is saved (for budget learning)
    - CustomerMemory is updated:
      - New category/brand added to preferences
      - Budget average recalculated (start / mid / end of month)
      - Monthly shopping pattern updated
      - Category interests expanded (never shrinks)

    The response includes a `memory_updated` field showing exactly
    what the AI learned from this purchase.

    **Example request:**
    ```json
    {
        "customer_id": "CUST001",
        "product_id": "PROD005",
        "quantity": 1
    }
    ```

    **To see the full effect:** Call `GET /customers/CUST001/memory`
    before and after this endpoint to observe the memory change.
    """
    try:
        result = order_service.process_purchase(db, request)
        return result
    except ValueError as e:
        # ValueError is raised for business logic errors:
        # - customer not found
        # - product not found
        # - insufficient stock
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Purchase failed due to an internal error: {str(e)}"
        )
