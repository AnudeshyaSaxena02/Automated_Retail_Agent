# ============================================================
# IDAM — Intelligent Automated Retail Store Backend
# app/schemas/llm.py
#
# PURPOSE:
#   Pydantic request and response models for the LLM endpoints.
#
# SCHEMAS:
#   LLMQueryRequest    — body for POST /llm/query  (Phase 6)
#   LLMQueryResponse   — response from POST /llm/query  (Phase 6)
#   RAGQueryRequest    — body for POST /llm/rag-query  (Phase 7)
#   RAGQueryResponse   — response from POST /llm/rag-query  (Phase 7)
#   RAGProductItem     — one product entry in the RAG response
#   LLMErrorResponse   — standardised error body (used in docs)
# ============================================================

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# ── POST /llm/query — Request (Phase 6) ──────────────────────

class LLMQueryRequest(BaseModel):
    """
    Request body for POST /llm/query (Phase 6 — LLM-only, no RAG).
    """

    query: str = Field(
        ...,
        min_length=2,
        max_length=2000,
        description=(
            "Natural-language query to send to the LLM. "
            "Examples: 'Suggest a laptop for programming', "
            "'What is the best wireless headphone under ₹5000?'"
        ),
        examples=["Suggest a laptop for programming"],
    )

    customer_id: Optional[str] = Field(
        default=None,
        description="[Phase 8+] Customer ID for personalised responses.",
        examples=["CUST001"],
    )

    class Config:
        json_schema_extra = {
            "example": {"query": "Suggest a laptop for programming"}
        }


# ── POST /llm/query — Response (Phase 6) ─────────────────────

class LLMQueryResponse(BaseModel):
    """
    Response body for POST /llm/query.
    """

    response: str = Field(
        ...,
        description="The LLM's conversational response to the query.",
    )

    provider: str = Field(
        ...,
        description="LLM provider that generated this response ('Groq' or 'Gemini').",
        examples=["Groq"],
    )

    class Config:
        json_schema_extra = {
            "example": {
                "response": (
                    "For programming, you'll want a laptop with a fast multi-core processor, "
                    "at least 16GB of RAM, and an SSD for quick compile times."
                ),
                "provider": "Groq"
            }
        }


# ── POST /llm/rag-query — Request (Phase 7) ──────────────────

class RAGQueryRequest(BaseModel):
    """
    Request body for POST /llm/rag-query (Phase 7 — RAG-enriched).

    The system will:
    1. Embed the query and search ChromaDB for relevant products
    2. Inject the retrieved products into the LLM system prompt
    3. Return a grounded, catalog-accurate response
    """

    query: str = Field(
        ...,
        min_length=2,
        max_length=2000,
        description=(
            "Natural-language product query. "
            "The system will search the catalog for relevant products "
            "and inject them into the LLM context before answering."
        ),
        examples=["I need a laptop for machine learning"],
    )

    top_k: Optional[int] = Field(
        default=None,
        ge=1,
        le=20,
        description=(
            "Number of products to retrieve from the catalog (1–20). "
            "Defaults to RAG_TOP_K in .env (5). "
            "More products = richer context but longer response."
        ),
        examples=[5],
    )

    min_score: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description=(
            "Minimum semantic similarity score for retrieved products (0.0–1.0). "
            "Defaults to SIMILARITY_THRESHOLD in .env (0.3). "
            "Raise to 0.5 for stricter matching."
        ),
        examples=[0.3],
    )

    customer_id: Optional[str] = Field(
        default=None,
        description="[Phase 8] Customer ID for personalised responses.",
        examples=["CUST001"],
    )

    class Config:
        json_schema_extra = {
            "example": {
                "query":   "I need a laptop for machine learning",
                "top_k":   5,
                "min_score": 0.3,
            }
        }


# ── RAG Response — embedded product item ─────────────────────

class RAGProductItem(BaseModel):
    """
    One product that was retrieved from ChromaDB and shown to the LLM.
    Included in RAGQueryResponse.products for transparency.
    """

    rank: int = Field(..., description="Retrieval rank (1 = most relevant)")
    product_id: str = Field(..., description="Product identifier, e.g. PROD001")
    name: str = Field(..., description="Product name")
    category: str = Field(..., description="Product category")
    brand: str = Field(default="", description="Product brand")
    price: float = Field(..., description="Price in INR")
    stock: int = Field(default=0, description="Available stock units")
    similarity_score: float = Field(
        ..., ge=0.0, le=1.0,
        description="Semantic similarity score (0.0–1.0)"
    )


# ── POST /llm/rag-query — Response (Phase 7) ─────────────────

class RAGQueryResponse(BaseModel):
    """
    Response body for POST /llm/rag-query.

    Includes the LLM's grounded response PLUS metadata about
    which products were retrieved and whether RAG was used.
    This lets the frontend display both the AI response and
    the matching product cards simultaneously.
    """

    response: str = Field(
        ...,
        description="The LLM's response, grounded in real catalog products.",
    )

    provider: str = Field(
        ...,
        description="LLM provider used ('Groq' or 'Gemini').",
        examples=["Groq"],
    )

    rag_used: bool = Field(
        ...,
        description=(
            "True if real catalog products were injected into the prompt. "
            "False if no matching products were found and the LLM answered "
            "from general knowledge (graceful fallback)."
        ),
    )

    products_retrieved: int = Field(
        ...,
        description="Number of products retrieved from ChromaDB.",
    )

    products: List[RAGProductItem] = Field(
        default=[],
        description=(
            "The products that were retrieved and shown to the LLM. "
            "Useful for rendering product cards alongside the LLM response."
        ),
    )

    class Config:
        json_schema_extra = {
            "example": {
                "response": (
                    "Based on our catalog, the Lenovo IdeaPad Slim 5 (₹58,999) is an excellent "
                    "choice for machine learning. It features an Intel i5 13th Gen processor, "
                    "16GB RAM, and 512GB SSD — more than enough for PyTorch and TensorFlow workloads."
                ),
                "provider":           "Groq",
                "rag_used":           True,
                "products_retrieved": 3,
                "products": [
                    {
                        "rank": 1,
                        "product_id": "PROD001",
                        "name": "Lenovo IdeaPad Slim 5",
                        "category": "Laptops",
                        "brand": "Lenovo",
                        "price": 58999.0,
                        "stock": 100,
                        "similarity_score": 0.87,
                    }
                ],
            }
        }


# ── Standardised error schema ─────────────────────────────────

class LLMErrorResponse(BaseModel):
    """
    Standardised error body returned by the LLM endpoints.
    """

    detail: str = Field(
        ...,
        description="Human-readable error message explaining what went wrong.",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "detail": "Groq API key is invalid. Update GROQ_API_KEY in your .env file."
            }
        }
