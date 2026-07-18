# ============================================================
# IDAM — Intelligent Automated Retail Store Backend
# app/api/recommendations.py
#
# PURPOSE:
#   FastAPI router for Phase 8 recommendation endpoints.
#   Intentionally thin — HTTP concerns only.
#   All business logic lives in recommendation_service.py.
#
# ENDPOINTS:
#   POST /recommendations/{customer_id}
#     — Generate personalised product recommendations for a customer.
# ============================================================

import logging

from fastapi import APIRouter, Depends, Path
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.schemas.recommendation import (
    RecommendationRequest,
    RecommendationResponse,
)
from app.services.recommendation_service import get_recommendations

logger = logging.getLogger(__name__)

router = APIRouter()


# ── POST /recommendations/{customer_id} ───────────────────────

@router.post(
    "/{customer_id}",
    response_model=RecommendationResponse,
    summary="Generate personalised product recommendations for a customer",
    description=(
        "Runs the full Phase 8 recommendation pipeline for the given customer:\n\n"
        "1. **Loads** the customer's memory, purchase history, and budget estimate.\n"
        "2. **Generates** a candidate pool using ChromaDB semantic search (query-driven) "
        "and SQLite category lookup (interest-driven).\n"
        "3. **Filters** out-of-stock and recently purchased products.\n"
        "4. **Scores** every candidate using a 5-factor weighted model:\n"
        "   - Customer Interest Score (35%)\n"
        "   - Semantic Similarity Score (25%)\n"
        "   - Budget Compatibility Score (20%)\n"
        "   - Purchase Frequency Score (10%)\n"
        "   - Product Popularity Score (10%)\n"
        "5. **Returns** the top-K ranked products with full score breakdowns.\n\n"
        "**Note:** The LLM is NOT called at this phase. Recommendations are "
        "deterministic and score-based only. LLM explanation comes in a future phase."
    ),
    responses={
        200: {
            "description": "Recommendations generated successfully",
            "model": RecommendationResponse,
        },
        404: {
            "description": "Customer not found or no memory profile available",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Customer 'CUST999' not found. "
                                  "Ensure the customer_id matches a valid customer in the system."
                    }
                }
            },
        },
        500: {
            "description": "Recommendation engine encountered an unexpected error",
        },
    },
)
def recommend_for_customer(
    customer_id: str = Path(
        ...,
        description="Customer's unique identifier (e.g. 'CUST001')",
        example="CUST001",
    ),
    request:     RecommendationRequest = RecommendationRequest(),
    db:          Session               = Depends(get_db),
):
    """
    Generate personalised product recommendations for `{customer_id}`.

    **How to use:**
    - Provide `customer_id` in the URL path (e.g. `/recommendations/CUST001`)
    - Optionally include a `query` in the request body to drive semantic search
      (e.g. `{"query": "I want something for my office setup"}`)
    - If no `query` is given, recommendations are entirely driven by the customer's
      purchase history and interest categories

    **Response fields:**
    - `estimated_budget` — Customer's estimated budget for the current period (INR)
    - `budget_period` — start of month / mid month / end of month
    - `recommended_products` — Ranked list with full score breakdowns per product
    - `reason` — Rule-based explanation of why each product was recommended

    **Scoring factors (with weights):**
    | Factor | Weight | Description |
    |---|---|---|
    | Interest | 35% | Category + brand + tag match vs. customer profile |
    | Semantic | 25% | ChromaDB cosine similarity to query |
    | Budget | 20% | How close the product price is to estimated budget |
    | Frequency | 10% | How often this category is purchased by this customer |
    | Popularity | 10% | Total orders across all customers |
    """
    logger.info(
        f"[Rec API] POST /recommendations/{customer_id} | "
        f"query={repr(request.query)} | top_k={request.top_k}"
    )

    return get_recommendations(
        db          = db,
        customer_id = customer_id,
        query       = request.query,
        top_k       = request.top_k,
    )
