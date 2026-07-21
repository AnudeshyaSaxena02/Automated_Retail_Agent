# ============================================================
# IDAM — Intelligent Automated Retail Store Backend
# app/schemas/chat.py
#
# PURPOSE:
#   Pydantic request and response models for the Phase 9
#   AI Shopping Assistant endpoint.
#
# SCHEMAS:
#   ChatRequest      — body for POST /chat/{customer_id}
#   ChatProductItem  — one product in the chat response
#   ChatResponse     — full structured response envelope
#
# DESIGN:
#   ChatProductItem is a superset of both RAGProductItem and
#   RecommendedProductItem. Fields like final_score and reason
#   are Optional so it works for both search and recommendation
#   results without requiring separate schemas.
# ============================================================

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# ── POST /chat/{customer_id} — Request ───────────────────────

class ChatRequest(BaseModel):
    """
    Request body for the AI Shopping Assistant chat endpoint.

    A single natural-language message from the customer.
    The system automatically detects intent and routes to the
    appropriate service pipeline.
    """

    message: str = Field(
        ...,
        min_length=2,
        max_length=1000,
        description=(
            "Natural-language message from the customer. "
            "Examples: 'I need a laptop for AI under ₹60,000', "
            "'What have I purchased recently?', "
            "'Compare Lenovo IdeaPad Slim 5 with HP Pavilion x360'."
        ),
        examples=["I need a laptop for AI under ₹60,000"],
    )

    class Config:
        json_schema_extra = {
            "example": {
                "message": "I need a laptop for AI under ₹60,000"
            }
        }


# ── One product in the chat response ─────────────────────────

class ChatProductItem(BaseModel):
    """
    A single product included in the chat response.

    Used for both semantic search results and recommendation
    engine results. Optional fields are populated only when
    the product came from the recommendation engine.
    """

    product_id: str = Field(..., description="Unique product identifier, e.g. PROD001")
    name:       str = Field(..., description="Product display name")
    category:   str = Field(..., description="Product category")
    brand:      str = Field(default="", description="Product brand")
    price:      float = Field(..., description="Price in INR")
    stock:      int   = Field(default=0, description="Available stock units")

    # Populated for semantic search results
    similarity_score: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Cosine similarity score from ChromaDB (search results only)",
    )

    # Populated for recommendation engine results
    final_score: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Weighted recommendation score (recommendation results only)",
    )

    reason: Optional[str] = Field(
        default=None,
        description="Auto-generated reason this product was recommended (recommendation results only)",
    )


# ── Full chat response ────────────────────────────────────────

class ChatResponse(BaseModel):
    """
    Structured response from the AI Shopping Assistant.

    Every response includes:
    - The detected intent (for transparency / frontend routing)
    - The LLM's conversational answer
    - A product list (empty for history/general intents)
    - Metadata for additional context

    This is a single-turn response — no session state is maintained
    between calls. Customer memory (purchase history, budget, interests)
    is loaded fresh from the database on every request.
    """

    customer_id: str = Field(
        ...,
        description="The customer's unique identifier",
    )

    intent: str = Field(
        ...,
        description=(
            "The detected intent label. One of: product_search, product_details, "
            "recommendation, product_comparison, customer_history, "
            "order_history, budget_query, general_chat."
        ),
        examples=["recommendation"],
    )

    provider: str = Field(
        ...,
        description="LLM provider that generated the response ('groq' or 'gemini').",
        examples=["groq"],
    )

    response: str = Field(
        ...,
        description="The LLM's conversational response to the customer's message.",
    )

    products: List[ChatProductItem] = Field(
        default=[],
        description=(
            "Products included in the response. "
            "Empty for order_history, customer_history, and general_chat intents. "
            "Populated for search, recommendation, comparison, and budget intents."
        ),
    )

    metadata: Dict[str, Any] = Field(
        default={},
        description=(
            "Additional context about the response. May include: "
            "'budget_detected' (float), 'intent_confidence' (float), "
            "'rag_used' (bool), 'total_products' (int)."
        ),
    )

    class Config:
        json_schema_extra = {
            "example": {
                "customer_id": "CUST001",
                "intent":      "recommendation",
                "provider":    "groq",
                "response": (
                    "Based on your purchase history and ₹60,000 budget, I recommend "
                    "the Lenovo IdeaPad Slim 5 — it's a fantastic AI/ML laptop with "
                    "an Intel i5 13th Gen, 16GB RAM, and matches your Lenovo preference."
                ),
                "products": [
                    {
                        "product_id":  "PROD001",
                        "name":        "Lenovo IdeaPad Slim 5",
                        "category":    "Laptops",
                        "brand":       "Lenovo",
                        "price":       58999.0,
                        "stock":       100,
                        "final_score": 0.87,
                        "reason":      "Matches preferred brand (Lenovo) and budget.",
                    }
                ],
                "metadata": {
                    "budget_detected":    60000.0,
                    "intent_confidence":  1.0,
                    "total_products":     1,
                },
            }
        }
