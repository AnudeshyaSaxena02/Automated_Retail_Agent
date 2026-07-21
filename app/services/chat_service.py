# ============================================================
# IDAM — Intelligent Automated Retail Store Backend
# app/services/chat_service.py
#
# PURPOSE:
#   Central brain of the Phase 9 AI Shopping Assistant.
#   The only file the chat API router calls.
#
# PIPELINE:
#   1. Validate customer exists
#   2. Detect intent (intent_detector.detect_intent)
#   3. Load customer memory (customer_service.get_customer_memory)
#   4. Route to service pipeline (intent_router.route)
#   5. Build intent-aware prompt (prompt_builder.build_chat_prompt)
#   6. Call LLM (llm_client.complete_with_fallback)
#   7. Return ChatResponse
#
# LLM ROLE:
#   The LLM is NEVER given business logic.
#   All scoring, retrieval, and filtering is done by Python services.
#   The LLM only explains, summarises, and generates conversational text.
#
# ERROR HANDLING:
#   - Unknown customer     → graceful ChatResponse with helpful message
#   - No products found    → LLM answers from general knowledge
#   - LLM unavailable      → HTTPException(502) from _call_llm()
#   - Routing failure      → graceful fallback to GENERAL_CHAT
#   - DB failure           → propagates as HTTPException(500)
# ============================================================

import logging
from typing import Any, Dict, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.ai.intent.intent_detector import detect_intent, ChatIntent
from app.ai.intent.router import route
from app.ai.llm.llm_client import complete_with_fallback
from app.ai.llm.exceptions import (
    LLMAuthError,
    LLMTimeoutError,
    LLMNetworkError,
    LLMEmptyResponse,
    LLMProviderError,
)
from app.ai.prompts.prompt_builder import build_chat_prompt
from app.schemas.chat import ChatProductItem, ChatResponse
from app.services.customer_service import get_customer_by_id, get_customer_memory
from app.ai.memory.memory_engine import get_memory_summary

logger = logging.getLogger(__name__)


# ── LLM call with error mapping ───────────────────────────────
# Mirrors the pattern in llm_service._call_llm() — same error
# hierarchy, same HTTP status codes. No duplicate logic; the
# mapping is per-service by design (chat errors ≠ raw LLM errors).

def _call_llm(system: str, user: str):
    """
    Invoke the LLM with auto-fallback. Maps LLM exceptions to HTTPExceptions.

    Returns:
        (response_text: str, provider_name: str)

    Raises:
        HTTPException with the correct status code
    """
    try:
        return complete_with_fallback(system=system, user=user)

    except LLMAuthError as exc:
        logger.error(f"[ChatService] LLM auth failed: {exc}")
        raise HTTPException(
            status_code=401,
            detail=(
                "LLM authentication failed. "
                "Check GROQ_API_KEY and GEMINI_API_KEY in .env."
            ),
        ) from exc

    except LLMTimeoutError as exc:
        logger.error(f"[ChatService] LLM timeout: {exc}")
        raise HTTPException(status_code=504, detail=str(exc)) from exc

    except LLMEmptyResponse as exc:
        logger.error(f"[ChatService] LLM empty response: {exc}")
        raise HTTPException(
            status_code=502,
            detail="The LLM returned an empty response. Please try again.",
        ) from exc

    except LLMNetworkError as exc:
        logger.error(f"[ChatService] LLM network error: {exc}")
        raise HTTPException(
            status_code=502,
            detail=(
                "Could not reach the LLM provider. "
                "Both Groq and Gemini are currently unreachable."
            ),
        ) from exc

    except LLMProviderError as exc:
        logger.error(f"[ChatService] LLM provider error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    except Exception as exc:
        logger.exception(f"[ChatService] Unexpected LLM error: {exc}")
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred: {str(exc)}",
        ) from exc


# ── Schema helpers ────────────────────────────────────────────

def _products_to_schema(products: list) -> list:
    """
    Convert the raw product dicts from RouteResult into ChatProductItem
    schema objects, skipping any NOT_FOUND placeholders.
    """
    items = []
    for p in products:
        if p.get("product_id") == "NOT_FOUND":
            continue  # Placeholder from comparison — not a real product
        try:
            items.append(
                ChatProductItem(
                    product_id       = p["product_id"],
                    name             = p["name"],
                    category         = p.get("category", ""),
                    brand            = p.get("brand", ""),
                    price            = p.get("price", 0.0),
                    stock            = p.get("stock", 0),
                    similarity_score = p.get("similarity_score"),
                    final_score      = p.get("final_score"),
                    reason           = p.get("reason"),
                )
            )
        except Exception as exc:
            logger.warning(f"[ChatService] Could not map product to schema: {exc} | data={p}")
    return items


# ── Main orchestrator ─────────────────────────────────────────

def handle_chat(
    db:          Session,
    customer_id: str,
    message:     str,
) -> ChatResponse:
    """
    Handle one turn of the AI Shopping Assistant conversation.

    This is a single-turn handler: each call is fully self-contained.
    Customer memory is loaded from the database on every call.
    No conversation history is stored between calls.

    Pipeline:
      validate customer → detect intent → load memory →
      route to service → build prompt → call LLM → return ChatResponse

    Args:
        db          : Active SQLAlchemy session (injected by FastAPI)
        customer_id : Customer's string ID, e.g. 'CUST001'
        message     : The customer's natural-language message

    Returns:
        ChatResponse — always succeeds; errors produce a friendly message

    Raises:
        HTTPException(401/502/504/500) — only if LLM is unavailable
    """
    logger.info(
        f"[ChatService] handle_chat: customer='{customer_id}' | "
        f"message='{message[:80]}'" + ("..." if len(message) > 80 else "")
    )

    # ── Step 1: Validate customer ─────────────────────────────
    customer = get_customer_by_id(db, customer_id)
    if not customer:
        logger.warning(f"[ChatService] Customer '{customer_id}' not found.")
        # Graceful response — don't raise HTTPException, return friendly message
        # The LLM still handles general chat for unknown customers
        prompt = build_chat_prompt(
            message = message,
            intent  = ChatIntent.GENERAL_CHAT.value,
        )
        response_text, provider = _call_llm(
            system = prompt["system"],
            user   = (
                f"The customer '{customer_id}' was not found in our system. "
                "Please respond as IDAM and let them know their account wasn't found, "
                f"and ask them to verify their customer ID. Their original message: {message}"
            ),
        )
        return ChatResponse(
            customer_id = customer_id,
            intent      = ChatIntent.GENERAL_CHAT.value,
            provider    = provider,
            response    = response_text,
            products    = [],
            metadata    = {"error": "customer_not_found"},
        )

    # ── Step 2: Detect intent ─────────────────────────────────
    detected = detect_intent(message)
    logger.info(
        f"[ChatService] Intent detected: {detected.intent.value} "
        f"(confidence={detected.confidence:.2f}) | "
        f"budget={detected.budget_mentioned} | "
        f"products_mentioned={detected.products_mentioned}"
    )

    # ── Step 3: Load customer memory ──────────────────────────
    # Always load memory — it provides personalisation context to the LLM
    # regardless of intent. Uses existing customer_service (no duplication).
    memory_summary: Dict[str, Any] = {}
    try:
        memory = get_customer_memory(db, customer_id)
        if memory:
            memory_summary = get_memory_summary(memory)
            # Attach customer name for the prompt builder
            memory_summary["customer_name"] = customer.name
    except Exception as exc:
        logger.warning(
            f"[ChatService] Could not load memory for '{customer_id}': {exc}. "
            "Proceeding without customer profile."
        )

    # ── Step 4: Route to service pipeline ────────────────────
    try:
        route_result = route(
            detected    = detected,
            customer_id = customer_id,
            db          = db,
        )
    except Exception as exc:
        # Routing completely failed — fall back to GENERAL_CHAT
        logger.warning(
            f"[ChatService] Routing failed for intent '{detected.intent.value}': {exc}. "
            "Falling back to GENERAL_CHAT."
        )
        route_result = type("FallbackRoute", (), {
            "intent":          ChatIntent.GENERAL_CHAT.value,
            "products":        [],
            "orders":          [],
            "memory_summary":  memory_summary,
            "context_text":    "",
            "budget_detected": detected.budget_mentioned,
            "error":           str(exc),
        })()

    # Log routing result
    logger.info(
        f"[ChatService] Route result: intent={route_result.intent} | "
        f"products={len(route_result.products)} | "
        f"orders={len(route_result.orders)} | "
        f"error={route_result.error}"
    )

    # ── Step 5: Handle graceful empty state ───────────────────
    # If routing returned an error but there's no data, we still proceed
    # to the LLM — it will respond from general knowledge.
    effective_intent = route_result.intent

    # If routing failed and we have no products, downgrade to GENERAL_CHAT
    # so the LLM doesn't receive misleading instructions.
    if route_result.error and not route_result.products and not route_result.context_text:
        logger.info(
            f"[ChatService] No data returned by router — using GENERAL_CHAT fallback."
        )
        effective_intent = ChatIntent.GENERAL_CHAT.value

    # ── Step 6: Build prompt ──────────────────────────────────
    prompt = build_chat_prompt(
        message          = message,
        intent           = effective_intent,
        customer_profile = memory_summary,
        products         = route_result.products,
        context_text     = route_result.context_text,
        budget_detected  = route_result.budget_detected or detected.budget_mentioned,
    )

    # ── Step 7: Call LLM ──────────────────────────────────────
    response_text, provider_used = _call_llm(
        system = prompt["system"],
        user   = prompt["user"],
    )

    # ── Step 8: Build and return response ─────────────────────
    product_items = _products_to_schema(route_result.products)

    metadata: Dict[str, Any] = {
        "intent_confidence": detected.confidence,
        "total_products":    len(product_items),
    }
    if detected.budget_mentioned:
        metadata["budget_detected"] = detected.budget_mentioned
    if route_result.error:
        metadata["routing_note"] = route_result.error

    logger.info(
        f"[ChatService] Response ready. "
        f"Intent={effective_intent} | Provider={provider_used} | "
        f"Products={len(product_items)} | Response={len(response_text)} chars"
    )

    return ChatResponse(
        customer_id = customer_id,
        intent      = effective_intent,
        provider    = provider_used,
        response    = response_text,
        products    = product_items,
        metadata    = metadata,
    )
