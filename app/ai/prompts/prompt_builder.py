# ============================================================
# IDAM — Intelligent Automated Retail Store Backend
# app/ai/prompts/prompt_builder.py
#
# PURPOSE:
#   Central registry for all prompts used by the IDAM backend.
#   No prompt text ever lives inside an API route or service file.
#   Every prompt is defined and assembled here.
#
# DESIGN PHILOSOPHY:
#   Prompts are constructed from structured arguments, not f-strings
#   scattered across the codebase. This makes them easy to:
#     - Review and improve in one place
#     - Extend for future phases without touching any other file
#     - Unit-test independently of the API
#
# CURRENT FUNCTIONS:
#   build_query_prompt(query)               → Phase 6 (LLM-only)
#   build_rag_prompt(query, context, ...)   → Phase 7 (RAG)
#
# PHASE 8 EXTENSIONS (ready to add, no refactoring needed):
#   Pass customer_profile to build_rag_prompt() to enable
#   fully personalised recommendations.
#
# PROMPT RETURN FORMAT:
#   All builder functions return a dict with two keys:
#     "system" — the system instruction (LLM persona + context)
#     "user"   — the user's message
#   This maps directly to the complete(system, user) interface.
# ============================================================

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ── IDAM System Persona (shared base) ───────────────────────
# This is the core identity injected into every LLM request.

_IDAM_SYSTEM_BASE = """You are IDAM, an intelligent AI shopping assistant for a modern retail store.

Your role:
- Help customers discover, compare, and choose products.
- Give specific, honest, and helpful product advice.
- Focus on practical benefits — not just specs.
- Ask clarifying questions when the customer's need is unclear.
- Keep responses conversational, clear, and concise (2–4 paragraphs max).

Rules:
- Never invent product names, prices, or specifications.
- If you are uncertain, say so and offer to help narrow down options.
- Do not discuss topics unrelated to shopping, products, or the retail store.

Language: English. Tone: Helpful, friendly, professional."""


# ── Phase 6: Basic Query Prompt ──────────────────────────────

def build_query_prompt(query: str) -> Dict[str, str]:
    """
    Build a basic prompt for a natural-language product query.

    Phase 6 entry point — no product data, no customer profile,
    no history. The LLM draws on its general training knowledge.

    In Phase 7, the RAG endpoint uses build_rag_prompt() instead.
    This function is kept for the /llm/query endpoint (still valid).

    Args:
        query : The user's raw natural-language query.

    Returns:
        Dict with "system" and "user" keys.
    """
    if not query or not query.strip():
        query = "Hello, what can you help me with?"

    logger.debug(f"[PromptBuilder] Building phase-6 query prompt.")

    return {
        "system": _IDAM_SYSTEM_BASE,
        "user":   query.strip(),
    }


# ── Phase 7: RAG Prompt ──────────────────────────────────────

# System prompt template for RAG — references real catalog data.
# Keeps grounding instructions separate from the base persona.
_RAG_SYSTEM_TEMPLATE = """{base_persona}

IMPORTANT — CATALOG CONTEXT:
You have been given real product data from the store's catalog below.
Use ONLY the products listed below when making recommendations.
Do NOT suggest products that are not in the provided list.
You MAY mention that a product is out of stock if stock is 0.
Always mention the product name and price when recommending.
If none of the products match the customer's request well, say so honestly and suggest what to look for.

{product_section}"""

_RAG_NO_RESULTS_SYSTEM = """{base_persona}

NOTE:
No products were found in the catalog matching this query.
Answer based on your general product knowledge, but make it clear
that you cannot confirm specific availability or pricing at this time.
Suggest the customer try a different search or browse the catalog."""


def build_rag_prompt(
    query: str,
    context: Optional[Dict[str, Any]] = None,
    customer_profile: Optional[Dict[str, Any]] = None,
    conversation_history: Optional[List[Dict[str, str]]] = None,
) -> Dict[str, str]:
    """
    Build a RAG-enriched prompt with real catalog product context.

    Phase 7 entry point. Uses the context dict produced by
    rag_context_builder.build_context() to inject real products
    into the system prompt before calling the LLM.

    Args:
        query                : User's natural-language query
        context              : Dict from rag_context_builder.build_context()
                               Keys: "products", "total_retrieved", "query"
        customer_profile     : [Phase 8] Customer memory dict.
                               Currently unused — accepted for forward compat.
        conversation_history : [Phase 8+] Previous turns.
                               Currently unused — accepted for forward compat.

    Returns:
        Dict with "system" and "user" keys, same format as build_query_prompt().
    """
    if not query or not query.strip():
        query = "Hello, what can you help me with?"

    # ── Case 1: No context provided or no products retrieved ──
    # Falls back to a graceful no-results system prompt.
    products = []
    if context:
        products = context.get("products", [])

    if not products:
        logger.info("[PromptBuilder] Building RAG prompt with NO products (fallback mode).")
        system = _RAG_NO_RESULTS_SYSTEM.format(base_persona=_IDAM_SYSTEM_BASE)
        return {
            "system": system,
            "user":   query.strip(),
        }

    # ── Case 2: Products retrieved — build grounded prompt ───
    logger.info(
        f"[PromptBuilder] Building RAG prompt with {len(products)} products."
    )

    product_section = _build_product_section(products)

    system = _RAG_SYSTEM_TEMPLATE.format(
        base_persona    = _IDAM_SYSTEM_BASE,
        product_section = product_section,
    )

    # The user message is the clean query — no injection here.
    # All context lives in the system prompt.
    return {
        "system": system,
        "user":   query.strip(),
    }


def _build_product_section(products: List[Dict[str, Any]]) -> str:
    """
    Format the list of products into a readable section for the system prompt.

    Each product block comes from rag_context_builder._format_product_block().
    Reviews (if available) are appended under each product block.

    Args:
        products : List of product context dicts from rag_context_builder

    Returns:
        Multi-line string — the CATALOG CONTEXT section of the system prompt
    """
    lines = ["--- AVAILABLE PRODUCTS IN CATALOG ---"]

    for product in products:
        # The pre-formatted text block from rag_context_builder
        lines.append("")
        lines.append(product["text_block"])

        # Append reviews if available (adds social proof context)
        reviews: List[str] = product.get("reviews", [])
        if reviews:
            lines.append("Customer Reviews:")
            for review_text in reviews:
                # Truncate very long reviews to keep the prompt compact
                truncated = review_text[:300] + "..." if len(review_text) > 300 else review_text
                lines.append(f'  • "{truncated}"')

    lines.append("")
    lines.append("--- END OF CATALOG CONTEXT ---")

    return "\n".join(lines)
