# ============================================================
# IDAM — Intelligent Automated Retail Store Backend
# app/ai/llm/groq_client.py
#
# PURPOSE:
#   Groq provider implementation of BaseLLMClient.
#   Uses the official 'groq' Python SDK.
#
# PROVIDER:
#   Groq Cloud — extremely fast inference via GroqChip.
#   Free tier: get an API key at https://console.groq.com
#
# MODEL (configured via .env):
#   GROQ_MODEL=llama-3.3-70b-versatile  (recommended default)
#   Other options: llama-3.1-8b-instant (faster, lighter),
#                  mixtral-8x7b-32768   (large context window)
#
# TIMEOUT:
#   Controlled by LLM_TIMEOUT in .env (default 30s).
#   Raises LLMTimeoutError on expiry so the service can
#   attempt the fallback provider automatically.
# ============================================================

import logging

import groq as groq_sdk

from app.ai.llm.base_client import BaseLLMClient
from app.ai.llm.exceptions import (
    LLMAuthError,
    LLMTimeoutError,
    LLMNetworkError,
    LLMEmptyResponse,
)
from app.config.settings import settings

logger = logging.getLogger(__name__)


class GroqClient(BaseLLMClient):
    """
    LLM client backed by Groq Cloud.

    Groq is the primary provider (LLM_PROVIDER=groq).
    If this client raises any LLMError, llm_client.py will
    automatically retry with GeminiClient.
    """

    def __init__(self) -> None:
        """
        Instantiate the Groq SDK client.

        The SDK is lazy — it does not make any network calls here.
        The first call happens in complete().
        """
        self._client = groq_sdk.Groq(api_key=settings.groq_api_key)
        self._model  = settings.groq_model
        self._timeout = settings.llm_timeout
        logger.debug(
            f"[GroqClient] Initialized. Model: {self._model} | Timeout: {self._timeout}s"
        )

    @property
    def provider_name(self) -> str:
        return "Groq"

    def complete(self, system: str, user: str) -> str:
        """
        Send a chat completion to Groq and return the response text.

        Args:
            system : System prompt (IDAM persona + optional context in Phase 7)
            user   : User's natural-language query

        Returns:
            Plain string response from the LLM

        Raises:
            LLMAuthError     : API key invalid or not set
            LLMTimeoutError  : Request exceeded LLM_TIMEOUT seconds
            LLMNetworkError  : Network-level failure reaching Groq
            LLMEmptyResponse : Groq responded but content was empty
        """
        logger.info(
            f"[GroqClient] Sending request to Groq. "
            f"Model: {self._model} | System: {len(system)} chars | User: {len(user)} chars"
        )

        try:
            chat_completion = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user",   "content": user},
                ],
                timeout=self._timeout,
            )

        except groq_sdk.AuthenticationError as exc:
            logger.error(f"[GroqClient] Authentication failed: {exc}")
            raise LLMAuthError(
                "Groq API key is invalid or not set. "
                "Update GROQ_API_KEY in your .env file."
            ) from exc

        except groq_sdk.APITimeoutError as exc:
            logger.error(f"[GroqClient] Request timed out after {self._timeout}s: {exc}")
            raise LLMTimeoutError(
                f"Groq request timed out after {self._timeout} seconds."
            ) from exc

        except groq_sdk.APIConnectionError as exc:
            logger.error(f"[GroqClient] Network error connecting to Groq: {exc}")
            raise LLMNetworkError(
                "Could not connect to Groq API. Check your internet connection."
            ) from exc

        except groq_sdk.RateLimitError as exc:
            # Rate limit = treat as temporary network issue for fallback logic
            logger.warning(f"[GroqClient] Rate limit hit: {exc}")
            raise LLMNetworkError(
                "Groq rate limit reached. Trying fallback provider."
            ) from exc

        except groq_sdk.APIStatusError as exc:
            # Catch-all for 4xx/5xx HTTP status errors from Groq
            logger.error(f"[GroqClient] Groq API status error {exc.status_code}: {exc.message}")
            if exc.status_code in (401, 403):
                raise LLMAuthError(f"Groq auth error ({exc.status_code}): {exc.message}") from exc
            raise LLMNetworkError(
                f"Groq returned HTTP {exc.status_code}: {exc.message}"
            ) from exc

        # ── Extract response text ────────────────────────────
        try:
            content = chat_completion.choices[0].message.content
        except (IndexError, AttributeError):
            content = None

        if not content or not content.strip():
            logger.warning("[GroqClient] Received empty response content from Groq.")
            raise LLMEmptyResponse("Groq returned an empty response.")

        logger.info(
            f"[GroqClient] Response received. "
            f"Length: {len(content)} chars | "
            f"Tokens used: {getattr(chat_completion.usage, 'total_tokens', 'N/A')}"
        )
        return content.strip()
