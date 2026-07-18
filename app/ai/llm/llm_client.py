# ============================================================
# IDAM — Intelligent Automated Retail Store Backend
# app/ai/llm/llm_client.py
#
# PURPOSE:
#   Factory and auto-fallback orchestrator for LLM providers.
#   This is the ONLY file the service layer talks to for LLM calls.
#   No other file should import GroqClient or GeminiClient directly.
#
# AUTO-FALLBACK FLOW:
#   1. Try primary provider (LLM_PROVIDER in .env, default: "groq")
#   2. If it raises any LLMError → log warning, try fallback provider
#   3. If fallback also fails → re-raise the fallback's error
#
# PROVIDER SELECTION:
#   LLM_PROVIDER=groq    → primary: Groq,   fallback: Gemini
#   LLM_PROVIDER=gemini  → primary: Gemini, fallback: Groq
#
# ADDING A NEW PROVIDER (future — e.g. OpenAI):
#   1. Create OpenAIClient(BaseLLMClient) in openai_client.py
#   2. Add "openai" to _PROVIDER_MAP below
#   3. Set LLM_PROVIDER=openai in .env
#   Done — zero other changes required.
# ============================================================

import logging
from typing import Tuple

from app.ai.llm.base_client import BaseLLMClient
from app.ai.llm.exceptions import LLMError, LLMProviderError
from app.config.settings import settings

logger = logging.getLogger(__name__)

# ── Lazy imports inside the factory ─────────────────────────
# We import the concrete clients only when they are needed.
# This avoids importing SDK packages that aren't installed
# (e.g. if a developer only has Groq installed, not Gemini).


def _build_groq() -> BaseLLMClient:
    from app.ai.llm.groq_client import GroqClient
    return GroqClient()


def _build_gemini() -> BaseLLMClient:
    from app.ai.llm.gemini_client import GeminiClient
    return GeminiClient()


# Registry of all supported providers
# key   : value of LLM_PROVIDER in .env (lowercase)
# value : zero-arg factory function that returns the client instance
_PROVIDER_MAP = {
    "groq":   _build_groq,
    "gemini": _build_gemini,
}

# Fallback order — if primary fails, use the next provider in this list
_FALLBACK_ORDER = ["groq", "gemini"]


def _get_ordered_providers(primary: str) -> Tuple[str, str | None]:
    """
    Return (primary_provider_name, fallback_provider_name | None).

    If the primary is in the fallback order, the fallback is the
    next provider in that list. If only one provider is configured,
    fallback is None.

    Examples:
        _get_ordered_providers("groq")   → ("groq",   "gemini")
        _get_ordered_providers("gemini") → ("gemini", "groq")
        _get_ordered_providers("openai") → ("openai", None)
    """
    if primary not in _PROVIDER_MAP:
        raise LLMProviderError(
            f"Unknown LLM_PROVIDER '{primary}'. "
            f"Supported values: {', '.join(_PROVIDER_MAP.keys())}. "
            "Update LLM_PROVIDER in your .env file."
        )

    others = [p for p in _FALLBACK_ORDER if p != primary and p in _PROVIDER_MAP]
    fallback = others[0] if others else None
    return primary, fallback


def complete_with_fallback(system: str, user: str) -> Tuple[str, str]:
    """
    Send a chat completion request, automatically falling back to the
    secondary provider if the primary fails.

    This is the single entry point called by llm_service.py.
    It hides all provider selection and retry logic from the service.

    Args:
        system : System prompt string
        user   : User query string

    Returns:
        Tuple of (response_text, provider_name_used)
        The provider_name_used is included so the service can log
        whether the primary or fallback served the request.

    Raises:
        LLMProviderError  : LLM_PROVIDER in .env is not recognised
        LLMError          : Both primary AND fallback failed (re-raises fallback error)
    """
    primary_name, fallback_name = _get_ordered_providers(
        settings.llm_provider.lower().strip()
    )

    # ── Attempt primary provider ──────────────────────────────
    logger.info(f"[LLMClient] Attempting primary provider: {primary_name}")
    try:
        client   = _PROVIDER_MAP[primary_name]()
        response = client.complete(system=system, user=user)
        logger.info(f"[LLMClient] Primary provider '{primary_name}' succeeded.")
        return response, primary_name

    except LLMError as primary_exc:
        if fallback_name is None:
            # No fallback configured — surface the error immediately
            logger.error(
                f"[LLMClient] Primary provider '{primary_name}' failed and no fallback is configured. "
                f"Error: {primary_exc}"
            )
            raise

        logger.warning(
            f"[LLMClient] Primary provider '{primary_name}' failed: {primary_exc}. "
            f"Falling back to '{fallback_name}'..."
        )

    # ── Attempt fallback provider ─────────────────────────────
    logger.info(f"[LLMClient] Attempting fallback provider: {fallback_name}")
    try:
        fallback_client   = _PROVIDER_MAP[fallback_name]()
        fallback_response = fallback_client.complete(system=system, user=user)
        logger.info(
            f"[LLMClient] Fallback provider '{fallback_name}' succeeded. "
            f"(Primary '{primary_name}' was unavailable.)"
        )
        return fallback_response, fallback_name

    except LLMError as fallback_exc:
        logger.error(
            f"[LLMClient] Fallback provider '{fallback_name}' also failed: {fallback_exc}. "
            "Both providers are unavailable."
        )
        raise  # Re-raise the fallback's error — service handles HTTP mapping
