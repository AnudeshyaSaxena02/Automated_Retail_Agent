# ============================================================
# IDAM — Intelligent Automated Retail Store Backend
# app/services/llm_service.py
#
# PURPOSE:
#   Orchestrates all LLM request pipelines.
#   This is the only file the API router talks to for LLM calls.
#
# FUNCTIONS:
#   handle_query()     — Phase 6: query → LLM (no catalog lookup)
#   handle_rag_query() — Phase 7: query → search → context → LLM
#
# ERROR HANDLING:
#   All LLM exceptions are caught here and re-raised as
#   HTTPException with the correct status code. The router
#   stays thin — it does not contain any exception logic.
#
# HTTP ERROR MAP:
#   LLMAuthError      → 401
#   LLMTimeoutError   → 504
#   LLMNetworkError   → 502
#   LLMEmptyResponse  → 502
#   LLMProviderError  → 500
#   Unexpected error  → 500
# ============================================================

import logging
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.ai.llm.llm_client import complete_with_fallback
from app.ai.llm.exceptions import (
    LLMAuthError,
    LLMTimeoutError,
    LLMNetworkError,
    LLMEmptyResponse,
    LLMProviderError,
)
from app.ai.prompts.prompt_builder import build_query_prompt, build_rag_prompt
from app.ai.rag.rag_context_builder import build_context
from app.config.settings import settings
from app.schemas.llm import LLMQueryResponse, RAGQueryResponse, RAGProductItem

logger = logging.getLogger(__name__)


# ── Shared error handler ──────────────────────────────────────

def _call_llm(system: str, user: str):
    """
    Call the LLM with auto-fallback and map all errors to HTTPExceptions.
    Used by both handle_query() and handle_rag_query().

    Returns:
        (response_text: str, provider_name: str)

    Raises:
        HTTPException with appropriate status code
    """
    try:
        return complete_with_fallback(system=system, user=user)

    except LLMAuthError as exc:
        logger.error(f"[LLMService] Authentication failed on all providers: {exc}")
        raise HTTPException(
            status_code=401,
            detail=(
                "LLM authentication failed. "
                "Check that GROQ_API_KEY and GEMINI_API_KEY are set correctly in .env."
            ),
        ) from exc

    except LLMTimeoutError as exc:
        logger.error(f"[LLMService] Timeout on all providers: {exc}")
        raise HTTPException(status_code=504, detail=str(exc)) from exc

    except LLMEmptyResponse as exc:
        logger.error(f"[LLMService] Empty response from all providers: {exc}")
        raise HTTPException(
            status_code=502,
            detail="The LLM returned an empty response. Please try again.",
        ) from exc

    except LLMNetworkError as exc:
        logger.error(f"[LLMService] Network failure on all providers: {exc}")
        raise HTTPException(
            status_code=502,
            detail=(
                "Could not reach the LLM provider. "
                "Both Groq and Gemini are currently unreachable. "
                "Check your internet connection."
            ),
        ) from exc

    except LLMProviderError as exc:
        logger.error(f"[LLMService] Provider configuration error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    except Exception as exc:
        logger.exception(f"[LLMService] Unexpected error during LLM call: {exc}")
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred: {str(exc)}",
        ) from exc


# ── Phase 6: LLM-only query ──────────────────────────────────

def handle_query(query: str) -> LLMQueryResponse:
    """
    Handle a natural-language query without catalog retrieval.

    Phase 6 pipeline:
      query → prompt builder → LLM (with auto-fallback) → response

    This function is NOT modified in Phase 7 — the /llm/query endpoint
    continues to work exactly as before.

    Args:
        query : Raw natural-language query string.

    Returns:
        LLMQueryResponse with the LLM's answer and the provider name.
    """
    logger.info(
        f"[LLMService] handle_query: '{query[:80]}'" + ("..." if len(query) > 80 else "")
    )

    prompt = build_query_prompt(query)
    response_text, provider_used = _call_llm(
        system=prompt["system"],
        user=prompt["user"],
    )

    logger.info(
        f"[LLMService] Query handled. Provider: {provider_used} | "
        f"Response: {len(response_text)} chars"
    )

    return LLMQueryResponse(
        response=response_text,
        provider=provider_used,
    )


# ── Phase 7: RAG query ────────────────────────────────────────

def handle_rag_query(
    query: str,
    db: Session,
    top_k: Optional[int] = None,
    min_score: Optional[float] = None,
) -> RAGQueryResponse:
    """
    Handle a RAG-enriched query: retrieve relevant products, inject into LLM.

    Phase 7 pipeline:
      query
        → semantic_search() [ChromaDB + embedding]
        → rag_context_builder.build_context() [format + reviews]
        → prompt_builder.build_rag_prompt() [inject into system prompt]
        → LLM (with auto-fallback)
        → RAGQueryResponse

    Graceful fallback:
      If 0 products are retrieved, falls back to LLM-only mode.
      The response still succeeds; rag_used=False indicates the fallback.

    Args:
        query     : Natural-language query string.
        db        : SQLAlchemy session (needed for semantic search + reviews).
        top_k     : Number of products to retrieve (default: settings.rag_top_k).
        min_score : Minimum similarity score (default: settings.similarity_threshold).

    Returns:
        RAGQueryResponse with response, provider, rag_used, and products list.
    """
    # Resolve defaults from settings
    effective_top_k     = top_k     if top_k     is not None else settings.rag_top_k
    effective_min_score = min_score if min_score is not None else settings.similarity_threshold

    logger.info(
        f"[LLMService] handle_rag_query: '{query[:80]}' | "
        f"top_k={effective_top_k} | min_score={effective_min_score}"
    )

    # ── Step 1: Semantic search ───────────────────────────────
    # Import here to avoid circular import at module load time.
    from app.services.search_service import semantic_search

    rag_used = False
    retrieved_products = []

    try:
        search_response = semantic_search(
            db        = db,
            query     = query,
            limit     = effective_top_k,
            min_score = effective_min_score,
        )
        retrieved_products = search_response.results
        logger.info(
            f"[LLMService] Semantic search returned {len(retrieved_products)} products."
        )
    except Exception as exc:
        # ChromaDB not ready or embedding error — fall back to LLM-only
        logger.warning(
            f"[LLMService] Semantic search failed: {exc}. "
            "Falling back to LLM-only mode."
        )
        retrieved_products = []

    # ── Step 2: Build RAG context ─────────────────────────────
    if retrieved_products:
        context = build_context(
            query    = query,
            products = retrieved_products,
            db       = db,
            include_reviews = True,
        )
        rag_used = True
    else:
        context = {}
        logger.info("[LLMService] No products retrieved — using LLM fallback (no RAG context).")

    # ── Step 3: Build prompt ──────────────────────────────────
    prompt = build_rag_prompt(
        query   = query,
        context = context,
    )

    # ── Step 4: Call LLM ──────────────────────────────────────
    response_text, provider_used = _call_llm(
        system = prompt["system"],
        user   = prompt["user"],
    )

    # ── Step 5: Build response ────────────────────────────────
    # Convert retrieved products to the RAGProductItem schema
    rag_product_items = [
        RAGProductItem(
            rank             = p.rank,
            product_id       = p.product_id,
            name             = p.name,
            category         = p.category,
            brand            = p.brand or "",
            price            = p.price,
            stock            = p.stock,
            similarity_score = p.similarity_score,
        )
        for p in retrieved_products
    ]

    logger.info(
        f"[LLMService] RAG query handled. "
        f"Provider: {provider_used} | rag_used: {rag_used} | "
        f"Products: {len(rag_product_items)} | Response: {len(response_text)} chars"
    )

    return RAGQueryResponse(
        response           = response_text,
        provider           = provider_used,
        rag_used           = rag_used,
        products_retrieved = len(rag_product_items),
        products           = rag_product_items,
    )
