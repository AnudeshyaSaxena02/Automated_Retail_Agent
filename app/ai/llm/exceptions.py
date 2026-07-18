# ============================================================
# IDAM — Intelligent Automated Retail Store Backend
# app/ai/llm/exceptions.py
#
# PURPOSE:
#   Defines typed exceptions for all LLM error cases.
#   Using specific exception classes (instead of bare Exception)
#   lets the service layer catch errors precisely and return
#   the correct HTTP status code for each failure mode.
#
# ERROR MAP (used in llm_service.py):
#   LLMAuthError      → HTTP 401  (bad API key)
#   LLMTimeoutError   → HTTP 504  (request took too long)
#   LLMNetworkError   → HTTP 502  (provider unreachable)
#   LLMEmptyResponse  → HTTP 502  (provider returned nothing)
#   LLMProviderError  → HTTP 500  (unknown provider in .env)
# ============================================================


class LLMError(Exception):
    """Base class for all LLM-related errors."""
    pass


class LLMAuthError(LLMError):
    """
    Raised when the API key is invalid, revoked, or missing.
    Maps to HTTP 401 Unauthorized.

    Example: GROQ_API_KEY is still 'your_groq_api_key_here' in .env
    """
    pass


class LLMTimeoutError(LLMError):
    """
    Raised when the LLM provider does not respond within LLM_TIMEOUT seconds.
    Maps to HTTP 504 Gateway Timeout.

    Example: Provider is under heavy load, request stalls.
    """
    pass


class LLMNetworkError(LLMError):
    """
    Raised when the network connection to the LLM provider fails.
    Maps to HTTP 502 Bad Gateway.

    Example: No internet, DNS failure, provider outage.
    """
    pass


class LLMEmptyResponse(LLMError):
    """
    Raised when the provider responds successfully but the content is empty.
    Maps to HTTP 502 Bad Gateway.

    Example: Provider returns a message with no text content.
    """
    pass


class LLMProviderError(LLMError):
    """
    Raised when LLM_PROVIDER in .env contains an unrecognised value.
    Maps to HTTP 500 Internal Server Error.

    Example: LLM_PROVIDER=openai (not yet implemented).
    """
    pass
