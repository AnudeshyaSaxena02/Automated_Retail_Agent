# ============================================================
# IDAM — Intelligent Automated Retail Store Backend
# app/ai/intent/router.py
#
# PURPOSE:
#   Workflow dispatcher. Maps a DetectedIntent to the correct
#   service pipeline and collects the data needed for the LLM.
#
# DESIGN:
#   - Pure dispatching layer — no business logic, no prompts
#   - Each intent handler calls existing services as-is
#   - Returns a RouteResult dataclass consumed by chat_service.py
#   - All failures are caught here and surfaced via RouteResult.error
#
# PRODUCT COMPARISON STRATEGY (per user spec):
#   1. Exact name match in SQLite (case-insensitive)
#   2. Fuzzy match in SQLite (LIKE %name%)
#   3. ChromaDB semantic search fallback
#
# HANDLER → SERVICE MAPPING:
#   PRODUCT_SEARCH     → search_service.semantic_search()
#   PRODUCT_DETAILS    → hybrid lookup + semantic_search()
#   RECOMMENDATION     → recommendation_service.get_recommendations()
#   PRODUCT_COMPARISON → hybrid lookup × 2 products
#   CUSTOMER_HISTORY   → customer_service.get_customer_memory() + orders
#   ORDER_HISTORY      → customer_service.get_customer_orders()
#   BUDGET_QUERY       → recommendation_service with budget as query
#   GENERAL_CHAT       → no service call (LLM-only)
# ============================================================

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.ai.intent.intent_detector import ChatIntent, DetectedIntent

logger = logging.getLogger(__name__)


# ── Route Result Dataclass ────────────────────────────────────

@dataclass
class RouteResult:
    """
    The output of the routing step.

    Carries everything chat_service needs to build the prompt
    and construct the ChatResponse — no further DB queries needed.

    Fields:
        intent          : The resolved intent string
        products        : Product dicts for the LLM prompt and response
                          Each dict has: product_id, name, category, brand,
                          price, stock, and optional similarity_score /
                          final_score / reason
        orders          : Order dicts for history intents
        memory_summary  : Customer memory dict from get_memory_summary()
        context_text    : Pre-formatted text summary for history intents
                          (not used for product intents — those go through
                          rag_context_builder via the prompt builder)
        budget_detected : Extracted budget amount (BUDGET_QUERY intent)
        error           : Error message if routing failed gracefully
    """
    intent:          str
    products:        List[Dict[str, Any]] = field(default_factory=list)
    orders:          List[Dict[str, Any]] = field(default_factory=list)
    memory_summary:  Dict[str, Any]       = field(default_factory=dict)
    context_text:    str                  = ""
    budget_detected: Optional[float]      = None
    error:           Optional[str]        = None


# ── Product Lookup (Hybrid Strategy) ─────────────────────────

def _find_product_by_name(
    db: Session,
    name: str,
    top_k: int = 1,
) -> List[Dict[str, Any]]:
    """
    Find a product using a 3-step hybrid strategy.

    Step 1: Exact case-insensitive match in SQLite
    Step 2: Fuzzy LIKE match in SQLite (partial name)
    Step 3: ChromaDB semantic search fallback

    Args:
        db    : SQLAlchemy session
        name  : Product name string to look up
        top_k : Max results to return (usually 1 for detail/comparison)

    Returns:
        List of product dicts (may be empty if nothing found at any step)
    """
    from app.database.models import Product
    from sqlalchemy import func

    # ── Step 1: Exact match (case-insensitive) ────────────────
    exact = (
        db.query(Product)
        .filter(func.lower(Product.name) == name.lower())
        .first()
    )
    if exact:
        logger.debug(f"[Router] Exact match found for '{name}': {exact.product_id}")
        return [_product_to_dict(exact)]

    # ── Step 2: Fuzzy LIKE match ──────────────────────────────
    fuzzy_results = (
        db.query(Product)
        .filter(Product.name.ilike(f"%{name}%"))
        .limit(top_k)
        .all()
    )
    if fuzzy_results:
        logger.debug(
            f"[Router] Fuzzy match found {len(fuzzy_results)} result(s) for '{name}'"
        )
        return [_product_to_dict(p) for p in fuzzy_results]

    # ── Step 3: Semantic search fallback ─────────────────────
    logger.debug(f"[Router] No DB match for '{name}' — falling back to semantic search")
    try:
        from app.services.search_service import semantic_search
        from app.config.settings import settings

        search_response = semantic_search(
            db        = db,
            query     = name,
            limit     = top_k,
            min_score = settings.similarity_threshold,
        )
        return [
            {
                "product_id":       r.product_id,
                "name":             r.name,
                "category":         r.category,
                "brand":            r.brand or "",
                "price":            r.price,
                "stock":            r.stock,
                "description":      r.description,
                "specifications":   r.specifications,
                "tags":             r.tags,
                "similarity_score": r.similarity_score,
            }
            for r in search_response.results
        ]
    except Exception as exc:
        logger.warning(f"[Router] Semantic search fallback failed for '{name}': {exc}")
        return []


def _product_to_dict(product) -> Dict[str, Any]:
    """Convert a Product ORM object to a plain dict for RouteResult."""
    import json

    def safe_json_list(v):
        try:
            return json.loads(v) if v else []
        except Exception:
            return []

    def safe_json_dict(v):
        try:
            return json.loads(v) if v else {}
        except Exception:
            return {}

    return {
        "product_id":     product.product_id,
        "name":           product.name,
        "category":       product.category,
        "brand":          product.brand or "",
        "price":          product.price,
        "stock":          product.stock,
        "description":    product.description,
        "specifications": safe_json_dict(product.specifications),
        "tags":           safe_json_list(product.tags),
        "similarity_score": None,
    }


# ── Individual Intent Handlers ────────────────────────────────

def _handle_product_search(
    detected: DetectedIntent,
    db: Session,
) -> RouteResult:
    """PRODUCT_SEARCH → semantic_search() → top products."""
    from app.services.search_service import semantic_search
    from app.config.settings import settings

    try:
        result = semantic_search(
            db        = db,
            query     = detected.raw_message,
            limit     = settings.rag_top_k,
            min_score = settings.similarity_threshold,
        )
        products = [
            {
                "product_id":       r.product_id,
                "name":             r.name,
                "category":         r.category,
                "brand":            r.brand or "",
                "price":            r.price,
                "stock":            r.stock,
                "description":      r.description,
                "specifications":   r.specifications,
                "tags":             r.tags,
                "similarity_score": r.similarity_score,
            }
            for r in result.results
        ]
        return RouteResult(
            intent   = detected.intent.value,
            products = products,
        )
    except Exception as exc:
        logger.warning(f"[Router] PRODUCT_SEARCH failed: {exc}")
        return RouteResult(intent=detected.intent.value, error=str(exc))


def _handle_product_details(
    detected: DetectedIntent,
    db: Session,
) -> RouteResult:
    """
    PRODUCT_DETAILS → hybrid product lookup → product dict.
    Uses the full raw message as the search query since the product
    name is embedded in natural language ("tell me about X").
    """
    try:
        products = _find_product_by_name(
            db   = db,
            name = detected.raw_message,
            top_k = 3,
        )
        return RouteResult(
            intent   = detected.intent.value,
            products = products,
        )
    except Exception as exc:
        logger.warning(f"[Router] PRODUCT_DETAILS failed: {exc}")
        return RouteResult(intent=detected.intent.value, error=str(exc))


def _handle_recommendation(
    detected: DetectedIntent,
    customer_id: str,
    db: Session,
    budget: Optional[float] = None,
) -> RouteResult:
    """
    RECOMMENDATION / BUDGET_QUERY → recommendation_service.get_recommendations().

    When a budget is provided (BUDGET_QUERY intent), the budget amount
    is included in the query string so the recommendation engine uses
    it for semantic candidate generation.
    """
    from app.services.recommendation_service import get_recommendations

    # Build the query: use the raw message, and prepend budget context if available
    query = detected.raw_message
    if budget:
        query = f"products under ₹{budget:,.0f} {query}"

    try:
        rec_response = get_recommendations(
            db          = db,
            customer_id = customer_id,
            query       = query,
        )
        products = [
            {
                "product_id":  item.product_id,
                "name":        item.name,
                "category":    item.category,
                "brand":       item.brand or "",
                "price":       item.price,
                "stock":       item.stock,
                "final_score": item.final_score,
                "reason":      item.reason,
            }
            for item in rec_response.recommended_products
        ]
        return RouteResult(
            intent          = detected.intent.value,
            products        = products,
            budget_detected = budget,
        )
    except Exception as exc:
        logger.warning(f"[Router] RECOMMENDATION failed for '{customer_id}': {exc}")
        return RouteResult(
            intent          = detected.intent.value,
            budget_detected = budget,
            error           = str(exc),
        )


def _handle_product_comparison(
    detected: DetectedIntent,
    db: Session,
) -> RouteResult:
    """
    PRODUCT_COMPARISON → hybrid lookup × 2 product names.

    Looks up each product independently using the 3-step hybrid
    strategy (exact → fuzzy → semantic).
    """
    names = detected.products_mentioned  # Already extracted by intent_detector

    if len(names) < 2:
        return RouteResult(
            intent = detected.intent.value,
            error  = "Could not extract two product names for comparison.",
        )

    all_products: List[Dict[str, Any]] = []

    for name in names:
        found = _find_product_by_name(db=db, name=name, top_k=1)
        if found:
            all_products.extend(found)
            logger.debug(f"[Router] Comparison: found '{found[0]['name']}' for query '{name}'")
        else:
            logger.warning(f"[Router] Comparison: no product found for '{name}'")
            # Add a placeholder so the LLM knows it couldn't find it
            all_products.append({
                "product_id": "NOT_FOUND",
                "name":       name,
                "category":   "Unknown",
                "brand":      "",
                "price":      0.0,
                "stock":      0,
                "error":      f"Product '{name}' was not found in the catalog.",
            })

    return RouteResult(
        intent   = detected.intent.value,
        products = all_products,
    )


def _handle_customer_history(
    detected: DetectedIntent,
    customer_id: str,
    db: Session,
) -> RouteResult:
    """CUSTOMER_HISTORY → memory summary + recent orders → context text."""
    from app.services.customer_service import get_customer_memory, get_customer_orders
    from app.ai.memory.memory_engine import get_memory_summary

    try:
        memory  = get_customer_memory(db, customer_id)
        summary = get_memory_summary(memory) if memory else {}
        orders_data = get_customer_orders(db, customer_id)
        orders  = orders_data.get("orders", []) if orders_data else []

        context_lines = [
            f"Customer Memory Summary:",
            f"  • Total purchases: {summary.get('total_purchases', 0)}",
            f"  • Total spend: ₹{summary.get('total_spend', 0):,.0f}",
            f"  • Purchased categories: {', '.join(summary.get('purchased_categories', [])) or 'None'}",
            f"  • Preferred brands: {', '.join(summary.get('preferred_brands', [])) or 'None'}",
            f"  • Category interests: {', '.join(summary.get('category_interests', [])) or 'None'}",
            f"  • Estimated budget ({summary.get('budget_period', '')}): ₹{summary.get('estimated_budget', 0):,.0f}",
        ]

        return RouteResult(
            intent         = detected.intent.value,
            orders         = orders,
            memory_summary = summary,
            context_text   = "\n".join(context_lines),
        )
    except Exception as exc:
        logger.warning(f"[Router] CUSTOMER_HISTORY failed for '{customer_id}': {exc}")
        return RouteResult(intent=detected.intent.value, error=str(exc))


def _handle_order_history(
    detected: DetectedIntent,
    customer_id: str,
    db: Session,
) -> RouteResult:
    """ORDER_HISTORY → recent orders → formatted context text."""
    from app.services.customer_service import get_customer_orders

    try:
        orders_data = get_customer_orders(db, customer_id)
        if not orders_data:
            return RouteResult(
                intent = detected.intent.value,
                error  = f"No orders found for customer '{customer_id}'.",
            )

        orders = orders_data.get("orders", [])
        total  = orders_data.get("total_spend", 0.0)

        # Format for the LLM prompt
        lines = [
            f"Order History for {orders_data.get('customer_name', customer_id)}:",
            f"  • Total orders: {len(orders)}",
            f"  • Total spend: ₹{total:,.0f}",
            "",
        ]
        for i, order in enumerate(orders[:10], start=1):  # Cap at 10 most recent
            lines.append(
                f"  {i}. {order['product_name']} "
                f"({order['product_category']}) — "
                f"₹{order['price_paid']:,.0f} × {order['quantity']} "
                f"on {order['purchased_at'].strftime('%d %b %Y') if hasattr(order['purchased_at'], 'strftime') else order['purchased_at']}"
            )

        return RouteResult(
            intent       = detected.intent.value,
            orders       = orders,
            context_text = "\n".join(lines),
        )
    except Exception as exc:
        logger.warning(f"[Router] ORDER_HISTORY failed for '{customer_id}': {exc}")
        return RouteResult(intent=detected.intent.value, error=str(exc))


def _handle_general_chat(
    detected: DetectedIntent,
) -> RouteResult:
    """GENERAL_CHAT → no service calls, LLM-only response."""
    return RouteResult(
        intent = detected.intent.value,
    )


# ── Main Route Function ───────────────────────────────────────

def route(
    detected:    DetectedIntent,
    customer_id: str,
    db:          Session,
) -> RouteResult:
    """
    Dispatch the detected intent to the correct service pipeline.

    This is the single public entry point called by chat_service.py.
    It selects the appropriate handler based on the intent and returns
    a RouteResult with all data needed to build the LLM prompt.

    No business logic lives here — this is pure dispatching.

    Args:
        detected    : DetectedIntent from intent_detector.detect_intent()
        customer_id : The customer's string ID (e.g. 'CUST001')
        db          : SQLAlchemy session

    Returns:
        RouteResult with products, orders, context_text, and/or error
    """
    intent = detected.intent

    logger.info(
        f"[Router] Routing intent={intent.value} | customer='{customer_id}' | "
        f"budget={detected.budget_mentioned} | "
        f"products_mentioned={detected.products_mentioned}"
    )

    if intent == ChatIntent.PRODUCT_SEARCH:
        return _handle_product_search(detected, db)

    elif intent == ChatIntent.PRODUCT_DETAILS:
        return _handle_product_details(detected, db)

    elif intent == ChatIntent.RECOMMENDATION:
        return _handle_recommendation(detected, customer_id, db)

    elif intent == ChatIntent.PRODUCT_COMPARISON:
        return _handle_product_comparison(detected, db)

    elif intent == ChatIntent.CUSTOMER_HISTORY:
        return _handle_customer_history(detected, customer_id, db)

    elif intent == ChatIntent.ORDER_HISTORY:
        return _handle_order_history(detected, customer_id, db)

    elif intent == ChatIntent.BUDGET_QUERY:
        return _handle_recommendation(
            detected    = detected,
            customer_id = customer_id,
            db          = db,
            budget      = detected.budget_mentioned,
        )

    else:  # GENERAL_CHAT
        return _handle_general_chat(detected)
