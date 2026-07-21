# ============================================================
# IDAM — Intelligent Automated Retail Store Backend
# app/ai/intent/intent_detector.py
#
# PURPOSE:
#   Lightweight, rule-based intent classifier for the Phase 9
#   AI Shopping Assistant.
#
# DESIGN:
#   - Single public function: detect_intent(message) → DetectedIntent
#   - Uses keyword matching and regex patterns — no LLM calls
#   - Priority-ordered rules (first match wins)
#   - Returns a DetectedIntent dataclass with the detected intent,
#     confidence score, extracted budget amount, and any product
#     names identified for comparison
#
# EXTENSIBILITY:
#   To replace with LLM-based detection in the future, implement a
#   new function with the same signature and swap the import in
#   chat_service.py. Nothing else needs to change.
#
# INTENT PRIORITY ORDER (top = highest priority):
#   1. PRODUCT_COMPARISON — "compare X with Y", "X vs Y"
#   2. BUDGET_QUERY       — "₹60k", "under ₹60,000", "I have ₹10,000"
#   3. ORDER_HISTORY      — "my orders", "what did I buy", "recent purchase"
#   4. CUSTOMER_HISTORY   — "my profile", "my preferences", "my interests"
#   5. RECOMMENDATION     — "recommend", "suggest", "best for me"
#   6. PRODUCT_DETAILS    — "tell me about", "details of", "specs of"
#   7. PRODUCT_SEARCH     — product category keywords, "find", "show", "search"
#   8. GENERAL_CHAT       — fallback
# ============================================================

import re
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

logger = logging.getLogger(__name__)


# ── Intent Enum ───────────────────────────────────────────────

class ChatIntent(str, Enum):
    """
    All possible intents the shopping assistant can handle.

    Inherits from str so values can be serialised directly
    into the ChatResponse JSON without .value conversion.
    """
    PRODUCT_SEARCH     = "product_search"
    PRODUCT_DETAILS    = "product_details"
    RECOMMENDATION     = "recommendation"
    PRODUCT_COMPARISON = "product_comparison"
    CUSTOMER_HISTORY   = "customer_history"
    ORDER_HISTORY      = "order_history"
    BUDGET_QUERY       = "budget_query"
    GENERAL_CHAT       = "general_chat"


# ── Result Dataclass ──────────────────────────────────────────

@dataclass
class DetectedIntent:
    """
    The result of intent detection.

    Carries the classified intent alongside extracted metadata
    so the router does not need to re-parse the message.

    Fields:
        intent              : The detected ChatIntent enum value
        confidence          : 1.0 for direct keyword match, 0.85 for indirect
        budget_mentioned    : Extracted numeric INR amount (e.g. 60000.0)
                              None if no budget was mentioned
        products_mentioned  : List of product names extracted from the message
                              (used for PRODUCT_COMPARISON routing)
        raw_message         : The original, unmodified user message
    """
    intent:             ChatIntent
    confidence:         float
    budget_mentioned:   Optional[float]      = None
    products_mentioned: List[str]            = field(default_factory=list)
    raw_message:        str                  = ""


# ── Budget Extraction ─────────────────────────────────────────

# Matches formats: ₹60,000 | ₹60000 | Rs.60000 | rs 60000 | 60000 | 60k | 60K
# Also handles: "under 60k", "below ₹60,000", "within Rs. 60000"
_BUDGET_PATTERN = re.compile(
    r"""
    (?:                        # Optional prefix: under/below/within/upto/max
        (?:under|below|within|upto|up\s+to|max(?:imum)?|less\s+than)\s+
    )?
    (?:                        # Optional currency symbol/code
        ₹\s* | rs\.?\s* | inr\s*
    )?
    (                          # CAPTURE GROUP: the numeric amount
        \d{1,3}                # 1–3 leading digits
        (?:[,\s]\d{3})*        # optional comma-separated thousands
        (?:\.\d{1,2})?         # optional decimal
        [kK]?                  # optional 'k' / 'K' multiplier
    )
    (?:\s*(?:rupees?|inr))?    # optional trailing currency word
    """,
    re.VERBOSE | re.IGNORECASE,
)


def _extract_budget(message: str) -> Optional[float]:
    """
    Extract a numeric INR budget amount from the message.

    Normalises all common formats to a Python float:
      "60k"        → 60000.0
      "60K"        → 60000.0
      "₹60,000"    → 60000.0
      "60000"      → 60000.0
      "under 60k"  → 60000.0
      "Rs. 60,000" → 60000.0
      "1.5 lakh"   → (not captured — lakh support deferred)

    Returns None if no budget amount is found.
    """
    # Special case: "X lakh" → X * 100,000
    lakh_match = re.search(
        r"(\d+(?:\.\d+)?)\s*(?:lakh|lac)\b",
        message,
        re.IGNORECASE,
    )
    if lakh_match:
        try:
            return float(lakh_match.group(1)) * 100_000
        except ValueError:
            pass

    match = _BUDGET_PATTERN.search(message)
    if not match:
        return None

    raw = match.group(1).strip()

    # Remove commas and spaces within the number
    raw = raw.replace(",", "").replace(" ", "")

    # Handle k/K suffix
    if raw.lower().endswith("k"):
        try:
            return float(raw[:-1]) * 1_000
        except ValueError:
            return None

    try:
        return float(raw)
    except ValueError:
        return None


# ── Comparison Extraction ─────────────────────────────────────

# Splits "compare X with/vs/versus/and Y" into [X, Y]
_COMPARE_SEPARATORS = re.compile(
    r"\s+(?:vs\.?|versus|with|and|or)\s+",
    re.IGNORECASE,
)

# Strip leading intent verbs before extracting product names
_COMPARE_PREFIX = re.compile(
    r"^(?:compare|difference\s+between|which\s+is\s+better|)\s*",
    re.IGNORECASE,
)


def _extract_comparison_products(message: str) -> List[str]:
    """
    Extract two product name strings from a comparison query.

    Examples:
        "compare Lenovo IdeaPad with HP Pavilion" → ["Lenovo IdeaPad", "HP Pavilion"]
        "iPhone 15 vs Samsung Galaxy S24"          → ["iPhone 15", "Samsung Galaxy S24"]
        "difference between A and B"               → ["A", "B"]

    Returns an empty list if fewer than two names are found.
    """
    cleaned = _COMPARE_PREFIX.sub("", message.strip())
    parts = _COMPARE_SEPARATORS.split(cleaned, maxsplit=1)

    products = [p.strip().strip("?.,!") for p in parts if p.strip()]

    # Need exactly 2 names for a meaningful comparison
    if len(products) < 2:
        return []

    return products[:2]


# ── Intent Rules ──────────────────────────────────────────────

# Rule: (keywords/patterns to check, intent, confidence)
# Applied in priority order — FIRST match wins.

_COMPARISON_TRIGGERS = [
    "compare", "vs ", "versus", "difference between",
    "which is better", "which one is better", "better between",
]

_ORDER_HISTORY_TRIGGERS = [
    "my order", "my orders", "what did i buy", "what have i bought",
    "recent purchase", "recent order", "purchase history",
    "what i bought", "show my purchases", "my purchases",
]

_CUSTOMER_HISTORY_TRIGGERS = [
    "my profile", "my preferences", "my interests", "my history",
    "what do i like", "what are my interests", "my shopping history",
    "my favourite", "my favorite", "my spending",
]

_RECOMMENDATION_TRIGGERS = [
    "recommend", "suggestion", "suggest", "what should i buy",
    "what should i get", "best for me", "good for me",
    "something for my", "suitable for", "accessories for",
    "what would you recommend", "help me choose", "help me pick",
    "i need something", "looking for something",
]

_DETAILS_TRIGGERS = [
    "tell me about", "details of", "specs of", "specifications of",
    "describe", "what is the", "about the", "more about",
    "information about", "info about", "features of",
]

# Common product category keywords that signal a product search
_SEARCH_CATEGORY_KEYWORDS = [
    "laptop", "laptops", "phone", "phones", "mobile", "mobiles",
    "headphone", "headphones", "earphone", "earbuds", "tablet", "tablets",
    "monitor", "monitors", "keyboard", "mouse", "webcam", "speaker", "speakers",
    "smartwatch", "wearable", "printer", "camera", "gaming", "charger",
    "ssd", "hard drive", "ram", "processor", "graphics card", "gpu",
    "accessory", "accessories", "bag", "case", "stand", "hub",
]

_SEARCH_ACTION_KEYWORDS = [
    "find", "search", "show me", "show", "list", "get me",
    "i want", "i need", "looking for", "i am looking",
    "what are the best", "top", "cheap", "affordable", "budget",
    "good", "best",
]


def _msg_contains_any(message_lower: str, triggers: List[str]) -> bool:
    """Return True if the lowercased message contains any trigger phrase."""
    return any(trigger in message_lower for trigger in triggers)


# ── Main Detection Function ───────────────────────────────────

def detect_intent(message: str) -> DetectedIntent:
    """
    Classify the user's message into one of 8 shopping intents.

    This is the single public entry point. All logic is rule-based
    and runs in microseconds. No LLM calls are made.

    Priority order:
      1. PRODUCT_COMPARISON  — "compare X with Y"
      2. BUDGET_QUERY        — numeric budget amount detected
      3. ORDER_HISTORY       — "my orders", "what did I buy"
      4. CUSTOMER_HISTORY    — "my profile", "my preferences"
      5. RECOMMENDATION      — "recommend", "suggest"
      6. PRODUCT_DETAILS     — "tell me about X"
      7. PRODUCT_SEARCH      — category + action keywords
      8. GENERAL_CHAT        — fallback

    Args:
        message : Raw user message string (any case)

    Returns:
        DetectedIntent with intent, confidence, and extracted metadata
    """
    if not message or not message.strip():
        return DetectedIntent(
            intent=ChatIntent.GENERAL_CHAT,
            confidence=1.0,
            raw_message=message or "",
        )

    msg_lower = message.lower().strip()

    # ── Rule 1: PRODUCT_COMPARISON ────────────────────────────
    if _msg_contains_any(msg_lower, _COMPARISON_TRIGGERS):
        products = _extract_comparison_products(message)
        if products:  # Only classify as comparison if we found 2 names
            logger.debug(
                f"[IntentDetector] PRODUCT_COMPARISON detected | "
                f"products={products}"
            )
            return DetectedIntent(
                intent=ChatIntent.PRODUCT_COMPARISON,
                confidence=1.0,
                products_mentioned=products,
                raw_message=message,
            )

    # ── Rule 2: BUDGET_QUERY ──────────────────────────────────
    # Check for currency signals to avoid false-positives on plain numbers
    has_currency_signal = any(
        signal in msg_lower
        for signal in ["₹", "rs", "rupee", "inr", " k", "k ", "lakh", "lac"]
    ) or re.search(r"\d{4,}", msg_lower)  # bare 4+ digit number also triggers

    if has_currency_signal:
        budget = _extract_budget(message)
        if budget and budget > 0:
            logger.debug(
                f"[IntentDetector] BUDGET_QUERY detected | budget=₹{budget:,.0f}"
            )
            return DetectedIntent(
                intent=ChatIntent.BUDGET_QUERY,
                confidence=1.0,
                budget_mentioned=budget,
                raw_message=message,
            )

    # ── Rule 3: ORDER_HISTORY ─────────────────────────────────
    if _msg_contains_any(msg_lower, _ORDER_HISTORY_TRIGGERS):
        logger.debug("[IntentDetector] ORDER_HISTORY detected")
        return DetectedIntent(
            intent=ChatIntent.ORDER_HISTORY,
            confidence=1.0,
            raw_message=message,
        )

    # ── Rule 4: CUSTOMER_HISTORY ──────────────────────────────
    if _msg_contains_any(msg_lower, _CUSTOMER_HISTORY_TRIGGERS):
        logger.debug("[IntentDetector] CUSTOMER_HISTORY detected")
        return DetectedIntent(
            intent=ChatIntent.CUSTOMER_HISTORY,
            confidence=1.0,
            raw_message=message,
        )

    # ── Rule 5: RECOMMENDATION ───────────────────────────────
    if _msg_contains_any(msg_lower, _RECOMMENDATION_TRIGGERS):
        logger.debug("[IntentDetector] RECOMMENDATION detected")
        return DetectedIntent(
            intent=ChatIntent.RECOMMENDATION,
            confidence=1.0,
            raw_message=message,
        )

    # ── Rule 6: PRODUCT_DETAILS ──────────────────────────────
    if _msg_contains_any(msg_lower, _DETAILS_TRIGGERS):
        logger.debug("[IntentDetector] PRODUCT_DETAILS detected")
        return DetectedIntent(
            intent=ChatIntent.PRODUCT_DETAILS,
            confidence=0.85,
            raw_message=message,
        )

    # ── Rule 7: PRODUCT_SEARCH ────────────────────────────────
    # Triggered by: category keywords OR (action keywords + product signal)
    has_category    = _msg_contains_any(msg_lower, _SEARCH_CATEGORY_KEYWORDS)
    has_action      = _msg_contains_any(msg_lower, _SEARCH_ACTION_KEYWORDS)

    if has_category or has_action:
        logger.debug(
            f"[IntentDetector] PRODUCT_SEARCH detected | "
            f"category_kw={has_category} | action_kw={has_action}"
        )
        return DetectedIntent(
            intent=ChatIntent.PRODUCT_SEARCH,
            confidence=0.85,
            raw_message=message,
        )

    # ── Rule 8: GENERAL_CHAT (fallback) ───────────────────────
    logger.debug("[IntentDetector] GENERAL_CHAT (fallback)")
    return DetectedIntent(
        intent=ChatIntent.GENERAL_CHAT,
        confidence=0.7,
        raw_message=message,
    )
