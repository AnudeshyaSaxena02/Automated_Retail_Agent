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


# ── Phase 9: Chat Prompt ──────────────────────────────────────
# Intent-aware, customer-personalised prompt builder.
# Called exclusively by chat_service.py.
# Zero changes to build_query_prompt() or build_rag_prompt().

# System prompt extensions for each intent
_CHAT_INTENT_INSTRUCTIONS: Dict[str, str] = {
    "product_search": (
        "TASK: The customer is searching for products. "
        "Use ONLY the catalog products listed below when responding. "
        "Highlight the top 2–3 matches, mention key specs, price, and stock status. "
        "Be specific and helpful."
    ),
    "product_details": (
        "TASK: The customer wants detailed information about a specific product. "
        "Use the product data below. Describe specs, use cases, pros, and value-for-money. "
        "Be thorough but concise."
    ),
    "recommendation": (
        "TASK: Generate a personalised product recommendation explanation. "
        "The products below have already been scored and ranked by our recommendation engine. "
        "Your job is to explain WHY the top products are a great fit for this customer, "
        "referencing their interests, preferred brands, and estimated budget. "
        "Be conversational and enthusiastic — not just a list."
    ),
    "product_comparison": (
        "TASK: Compare the two products listed below side by side. "
        "Cover: price difference, key specs, use cases, and which type of user each suits. "
        "Give a clear, honest recommendation at the end. "
        "If a product was not found in the catalog, acknowledge it directly."
    ),
    "customer_history": (
        "TASK: Summarise the customer's shopping history and profile in a friendly, "
        "conversational way. Include total purchases, spending, favourite categories, "
        "preferred brands, and current budget estimate. "
        "Make it feel personalised — address the customer by name if known."
    ),
    "order_history": (
        "TASK: Summarise the customer's recent orders in a clear, readable format. "
        "Mention the products, when they were purchased, and the total spend. "
        "Keep the tone warm and helpful."
    ),
    "budget_query": (
        "TASK: The customer has specified a budget. "
        "The products below have been filtered and ranked to fit within that budget. "
        "Explain the best options, why they represent good value, "
        "and which best fits the customer's interests. "
        "Always mention the budget clearly."
    ),
    "general_chat": (
        "TASK: Respond to the customer's message naturally and helpfully. "
        "If they are asking about products or shopping, guide them. "
        "If the question is unrelated to the store, politely redirect."
    ),
}


def _build_customer_context_section(customer_profile: Dict[str, Any]) -> str:
    """
    Format customer memory/profile data into a concise text block
    for injection into the system prompt.

    Used by build_chat_prompt() to always give the LLM customer context.
    """
    if not customer_profile:
        return ""

    lines = ["--- CUSTOMER PROFILE ---"]

    name = customer_profile.get("customer_name") or customer_profile.get("name", "")
    if name:
        lines.append(f"Customer Name: {name}")

    interests = customer_profile.get("category_interests", [])
    if interests:
        lines.append(f"Category Interests: {', '.join(interests)}")

    brands = customer_profile.get("preferred_brands", [])
    if brands:
        lines.append(f"Preferred Brands: {', '.join(brands)}")

    budget = customer_profile.get("estimated_budget") or customer_profile.get("budget_estimate", 0)
    period = customer_profile.get("budget_period", "")
    if budget and budget > 0:
        lines.append(f"Estimated Budget ({period}): ₹{budget:,.0f}")

    total = customer_profile.get("total_purchases", 0)
    if total:
        lines.append(f"Total Purchases: {total}")

    lines.append("--- END CUSTOMER PROFILE ---")
    return "\n".join(lines)


def _build_chat_product_section(products: List[Dict[str, Any]], intent: str) -> str:
    """
    Format the product list from RouteResult into a system-prompt-ready
    text section. Handles both search products and recommendation products.
    """
    if not products:
        return ""

    if intent == "product_comparison":
        lines = ["--- PRODUCTS TO COMPARE ---"]
    elif intent in ("recommendation", "budget_query"):
        lines = ["--- RECOMMENDED PRODUCTS (pre-scored and ranked) ---"]
    else:
        lines = ["--- AVAILABLE PRODUCTS IN CATALOG ---"]

    for idx, p in enumerate(products, start=1):
        # Handle not-found placeholder from comparison router
        if p.get("error"):
            lines.append(f"\n[Product {idx}] {p.get('name', 'Unknown')}")
            lines.append(f"  NOTE: {p['error']}")
            continue

        lines.append(f"\n[Product {idx}] {p.get('name', 'N/A')}")
        stock_label = "In Stock" if p.get("stock", 0) > 0 else "Out of Stock"
        lines.append(
            f"  Category: {p.get('category', 'N/A')} | "
            f"Brand: {p.get('brand') or 'N/A'} | "
            f"Price: ₹{p.get('price', 0):,.0f} | "
            f"Stock: {stock_label}"
        )

        desc = p.get("description")
        if desc:
            lines.append(f"  Description: {desc[:200]}{'...' if len(desc) > 200 else ''}")

        specs = p.get("specifications")
        if specs and isinstance(specs, dict):
            spec_str = ", ".join(f"{k}: {v}" for k, v in list(specs.items())[:6])
            lines.append(f"  Specs: {spec_str}")

        tags = p.get("tags")
        if tags and isinstance(tags, list):
            lines.append(f"  Tags: {', '.join(tags[:8])}")

        # Scores (recommendation intent)
        final_score = p.get("final_score")
        if final_score is not None:
            lines.append(f"  Recommendation Score: {final_score:.2f}")

        reason = p.get("reason")
        if reason:
            lines.append(f"  Reason: {reason}")

        # Score (search intent)
        sim_score = p.get("similarity_score")
        if sim_score is not None:
            lines.append(f"  Relevance Score: {sim_score:.2f}")

    lines.append("\n--- END OF PRODUCTS ---")
    return "\n".join(lines)


def build_chat_prompt(
    message: str,
    intent: str,
    customer_profile: Optional[Dict[str, Any]] = None,
    products: Optional[List[Dict[str, Any]]] = None,
    context_text: str = "",
    budget_detected: Optional[float] = None,
) -> Dict[str, str]:
    """
    Build an intent-aware, customer-personalised system prompt for Phase 9.

    Called exclusively by chat_service.py after the router has collected
    all relevant data. Composes the final system + user message pair that
    goes to the LLM via complete_with_fallback().

    Structure of the system prompt:
      1. IDAM base persona (shared, from _IDAM_SYSTEM_BASE)
      2. Customer profile section (if memory is available)
      3. Intent-specific task instruction
      4. Product section or history context (if data is available)
      5. Budget note (if detected)

    Args:
        message          : The original user message (becomes the user prompt)
        intent           : Intent string (e.g. 'recommendation')
        customer_profile : Dict from memory_engine.get_memory_summary() or
                           customer_profile_builder — provides personalisation context
        products         : List of product dicts from RouteResult (may be empty)
        context_text     : Pre-formatted text for history intents (from router.py)
        budget_detected  : Extracted INR budget amount (BUDGET_QUERY intent)

    Returns:
        Dict with 'system' and 'user' keys, matching the complete_with_fallback()
        interface used by all other LLM calls in the system.
    """
    products   = products   or []
    profile    = customer_profile or {}

    # ── Assemble system prompt sections ───────────────────────

    sections: List[str] = [_IDAM_SYSTEM_BASE]

    # Section 2: Customer profile
    customer_ctx = _build_customer_context_section(profile)
    if customer_ctx:
        sections.append(customer_ctx)

    # Section 3: Intent-specific task instruction
    task_instruction = _CHAT_INTENT_INSTRUCTIONS.get(
        intent,
        _CHAT_INTENT_INSTRUCTIONS["general_chat"],
    )
    sections.append(f"\n{task_instruction}")

    # Section 4: Products or history context
    if products:
        product_section = _build_chat_product_section(products, intent)
        if product_section:
            sections.append(product_section)
    elif context_text:
        sections.append(f"\n--- CUSTOMER DATA ---\n{context_text}\n--- END ---")

    # Section 5: Budget note
    if budget_detected and budget_detected > 0:
        sections.append(
            f"\nBUDGET NOTE: The customer has specified a budget of ₹{budget_detected:,.0f}. "
            "Focus only on products at or below this price."
        )

    system = "\n\n".join(sections)

    logger.info(
        f"[PromptBuilder] build_chat_prompt: intent={intent} | "
        f"products={len(products)} | profile={'yes' if profile else 'no'} | "
        f"budget={budget_detected}"
    )

    return {
        "system": system,
        "user":   message.strip(),
    }
