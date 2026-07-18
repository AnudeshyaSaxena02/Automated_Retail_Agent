# ============================================================
# IDAM — Intelligent Automated Retail Store Backend
# app/ai/llm/base_client.py
#
# PURPOSE:
#   Abstract base class for all LLM provider clients.
#   Every provider (Groq, Gemini, OpenAI, etc.) must implement
#   this interface. This is the contract the rest of the app uses.
#
# DESIGN:
#   - One abstract method: complete(system, user) → str
#   - Forces consistent behaviour across all providers
#   - Swapping providers = changing LLM_PROVIDER in .env only
#
# FUTURE PHASES:
#   Phase 7 (RAG) will call the same complete() method
#   after injecting retrieved products into the user prompt.
#   No changes to this interface are expected.
# ============================================================

from abc import ABC, abstractmethod


class BaseLLMClient(ABC):
    """
    Abstract contract for all LLM provider clients.

    Any class that inherits from BaseLLMClient MUST implement
    the complete() method. This guarantees that llm_client.py
    (the factory) can treat all providers interchangeably.

    Usage (internal — called by llm_service.py):
        client = get_llm_client()          # returns Groq or Gemini
        response = client.complete(        # same call regardless of provider
            system="You are IDAM...",
            user="Suggest a laptop for programming",
        )
    """

    @abstractmethod
    def complete(self, system: str, user: str) -> str:
        """
        Send a chat completion request to the LLM provider.

        Args:
            system : The system prompt — sets the LLM's persona and context.
                     In Phase 6 this is the IDAM retail assistant persona.
                     In Phase 7 (RAG) it will include retrieved product context.
            user   : The user's message — the natural-language query.

        Returns:
            The LLM's response as a plain string.

        Raises:
            LLMAuthError       : Invalid or missing API key.
            LLMTimeoutError    : Request exceeded the configured timeout.
            LLMNetworkError    : Could not reach the provider's API.
            LLMEmptyResponse   : Provider returned an empty or null response.
        """
        ...

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """
        Human-readable provider name, e.g. 'Groq' or 'Gemini'.
        Used in log messages and error responses.
        """
        ...
