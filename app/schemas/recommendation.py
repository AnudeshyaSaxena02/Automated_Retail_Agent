# ============================================================
# IDAM — Intelligent Automated Retail Store Backend
# app/schemas/recommendation.py
#
# PURPOSE:
#   Pydantic request and response models for the recommendation
#   endpoint (Phase 8).
#
# SCHEMAS:
#   RecommendationRequest    — body for POST /recommendations/{id}
#   RecommendedProductItem   — one scored product in the response
#   RecommendationResponse   — full response envelope
# ============================================================

from typing import List, Optional
from pydantic import BaseModel, Field


# ── POST /recommendations/{customer_id} — Request ────────────

class RecommendationRequest(BaseModel):
    """
    Optional request body for the recommendation endpoint.

    The query field accepts a natural-language intent string that
    drives semantic candidate retrieval from ChromaDB. If omitted,
    the engine falls back to interest-only candidate generation
    using the customer's stored category preferences.
    """

    query: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=500,
        description=(
            "Optional natural-language intent. "
            "Examples: 'I want something for my office setup', "
            "'Looking for a gaming accessory under ₹5000'. "
            "If not provided, recommendations are driven entirely "
            "by the customer's purchase history and interests."
        ),
        examples=["I want something useful for my office setup"],
    )

    top_k: Optional[int] = Field(
        default=None,
        ge=1,
        le=50,
        description=(
            "Number of recommendations to return. "
            "Defaults to RECOMMENDATION_TOP_K in settings (10). "
            "Override per-request here."
        ),
        examples=[10],
    )

    class Config:
        json_schema_extra = {
            "example": {
                "query": "I want something useful for my office setup",
            }
        }


# ── One recommended product — detailed scoring breakdown ──────

class RecommendedProductItem(BaseModel):
    """
    A single recommended product with full score breakdown.

    Every numeric score is in the range [0.0, 1.0].
    The final_score is the weighted combination of all factors.
    The reason field is a human-readable explanation generated
    by the scoring engine — not by an LLM.
    """

    rank: int = Field(..., description="Rank position (1 = highest score)")

    # ── Core product fields ───────────────────────────────────
    product_id: str   = Field(..., description="Unique product identifier, e.g. PROD001")
    name:       str   = Field(..., description="Product name")
    category:   str   = Field(..., description="Product category")
    brand:      str   = Field(default="", description="Product brand")
    price:      float = Field(..., description="Price in INR")
    stock:      int   = Field(default=0, description="Available stock units")

    # ── Composite score ───────────────────────────────────────
    final_score: float = Field(
        ..., ge=0.0, le=1.0,
        description="Weighted composite score (0.0–1.0). Higher is better.",
    )

    # ── Individual factor scores (all 0.0–1.0) ────────────────
    interest_score: float = Field(
        ..., ge=0.0, le=1.0,
        description=(
            "How well the product matches the customer's "
            "category interests, preferred brands, and tags. "
            "Weight: 35%."
        ),
    )
    semantic_score: float = Field(
        ..., ge=0.0, le=1.0,
        description=(
            "Cosine similarity between the query embedding "
            "and the product embedding in ChromaDB. "
            "Weight: 25%."
        ),
    )
    budget_score: float = Field(
        ..., ge=0.0, le=1.0,
        description=(
            "How well the product price fits the customer's "
            "estimated monthly budget. "
            "Weight: 20%."
        ),
    )
    frequency_score: float = Field(
        ..., ge=0.0, le=1.0,
        description=(
            "How often the customer shops in this product's category "
            "relative to their most-purchased category. "
            "Weight: 10%."
        ),
    )
    popularity_score: float = Field(
        ..., ge=0.0, le=1.0,
        description=(
            "Relative purchase count for this product across all "
            "customers in the database. "
            "Weight: 10%."
        ),
    )

    # ── Human-readable reason ─────────────────────────────────
    reason: str = Field(
        ...,
        description=(
            "Auto-generated explanation of why this product was recommended. "
            "Based entirely on scoring signals — no LLM involved at this phase."
        ),
    )

    class Config:
        json_schema_extra = {
            "example": {
                "rank":            1,
                "product_id":      "PROD008",
                "name":            "Logitech MX Master 3S",
                "category":        "Accessories",
                "brand":           "Logitech",
                "price":           8999.0,
                "stock":           100,
                "final_score":     0.8712,
                "interest_score":  0.9500,
                "semantic_score":  0.8200,
                "budget_score":    0.7900,
                "frequency_score": 0.6000,
                "popularity_score":0.4500,
                "reason": (
                    "Matches preferred category (Accessories) and preferred brand (Logitech). "
                    "Price fits estimated monthly budget. "
                    "Frequently purchased category."
                ),
            }
        }


# ── Full recommendation response ──────────────────────────────

class RecommendationResponse(BaseModel):
    """
    Full response for POST /recommendations/{customer_id}.

    Includes customer context (budget, period) alongside the ranked
    product list so the caller can display personalisation metadata
    next to the recommendations.
    """

    customer_id:   str   = Field(..., description="The customer's unique identifier")
    customer_name: str   = Field(..., description="The customer's display name")

    estimated_budget: float = Field(
        ...,
        description=(
            "The customer's estimated budget for the current period "
            "(start/mid/end of month) in INR. "
            "0.0 means no purchase history yet."
        ),
    )
    budget_period: str = Field(
        ...,
        description="Which period the budget estimate is for: 'start of month', 'mid month', or 'end of month'.",
    )

    query_used: Optional[str] = Field(
        default=None,
        description="The query string used for semantic candidate retrieval. Null if no query was provided.",
    )

    total_recommended: int = Field(
        ...,
        description="Number of products returned in recommended_products.",
    )

    recommended_products: List[RecommendedProductItem] = Field(
        default=[],
        description="Ranked list of recommended products, ordered by final_score descending.",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "customer_id":    "CUST001",
                "customer_name":  "Rahul Sharma",
                "estimated_budget": 58999.0,
                "budget_period":  "start of month",
                "query_used":     "I want something useful for my office setup",
                "total_recommended": 5,
                "recommended_products": [],
            }
        }
