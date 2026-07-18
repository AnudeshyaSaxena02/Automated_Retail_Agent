# ============================================================
# IDAM — Intelligent Automated Retail Store Backend
# app/ai/llm/gemini_client.py
#
# PURPOSE:
#   Google Gemini provider implementation of BaseLLMClient.
#   Used as the automatic fallback when Groq fails.
#
# PROVIDER:
#   Google AI Studio — free tier via the modern google-genai SDK.
#   Get a free API key at: https://aistudio.google.com
#
# SDK:
#   Uses google-genai (google.genai) — the current, maintained SDK.
#   NOT google.generativeai, which is deprecated.
#
# MODEL (configured via .env):
#   GEMINI_MODEL=gemini-1.5-flash  (recommended — fast + free)
#   Other options: gemini-2.0-flash, gemini-1.5-pro
#
# ROLE IN AUTO-FALLBACK:
#   Only instantiated when Groq raises an LLMError.
#   Receives the exact same (system, user) arguments.
# ============================================================

import logging

from google import genai
from google.genai import errors as genai_errors
from google.genai import types as genai_types

from app.ai.llm.base_client import BaseLLMClient
from app.ai.llm.exceptions import (
    LLMAuthError,
    LLMTimeoutError,
    LLMNetworkError,
    LLMEmptyResponse,
)
from app.config.settings import settings

logger = logging.getLogger(__name__)


class GeminiClient(BaseLLMClient):
    """
    LLM client backed by Google Gemini (google-genai SDK).

    Acts as the automatic fallback provider when Groq is unavailable.
    """

    def __init__(self) -> None:
        """
        Instantiate the google-genai client with the API key from settings.
        """
        self._client     = genai.Client(api_key=settings.gemini_api_key)
        self._model_name = settings.gemini_model
        self._timeout    = settings.llm_timeout

        logger.debug(
            f"[GeminiClient] Initialized. Model: {self._model_name} | Timeout: {self._timeout}s"
        )

    @property
    def provider_name(self) -> str:
        return "Gemini"

    def complete(self, system: str, user: str) -> str:
        """
        Send a chat completion to Gemini and return the response text.

        Uses the google-genai SDK's generate_content() with a system
        instruction and a user turn.

        Args:
            system : System prompt (IDAM persona + optional RAG context)
            user   : User's natural-language query

        Returns:
            Plain string response from the LLM

        Raises:
            LLMAuthError     : API key invalid
            LLMTimeoutError  : Request exceeded LLM_TIMEOUT seconds
            LLMNetworkError  : Network-level failure
            LLMEmptyResponse : Gemini responded but content was empty / blocked
        """
        logger.info(
            f"[GeminiClient] Sending request to Gemini. "
            f"Model: {self._model_name} | Prompt chars: {len(system) + len(user)}"
        )

        # Build the config with system instruction
        config = genai_types.GenerateContentConfig(
            system_instruction=system,
            # Apply lenient safety settings for retail product discussions
            safety_settings=[
                genai_types.SafetySetting(
                    category="HARM_CATEGORY_HARASSMENT",
                    threshold="BLOCK_ONLY_HIGH",
                ),
                genai_types.SafetySetting(
                    category="HARM_CATEGORY_HATE_SPEECH",
                    threshold="BLOCK_ONLY_HIGH",
                ),
                genai_types.SafetySetting(
                    category="HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    threshold="BLOCK_ONLY_HIGH",
                ),
                genai_types.SafetySetting(
                    category="HARM_CATEGORY_DANGEROUS_CONTENT",
                    threshold="BLOCK_ONLY_HIGH",
                ),
            ],
        )

        try:
            response = self._client.models.generate_content(
                model=self._model_name,
                contents=user,
                config=config,
            )

        except genai_errors.ClientError as exc:
            # 4xx errors — most commonly auth failures
            msg = str(exc).lower()
            if "api key" in msg or "invalid" in msg or "unauthorized" in msg or "403" in msg or "401" in msg:
                logger.error(f"[GeminiClient] Authentication failed: {exc}")
                raise LLMAuthError(
                    "Gemini API key is invalid or not set. "
                    "Update GEMINI_API_KEY in your .env file."
                ) from exc
            logger.error(f"[GeminiClient] Client error: {exc}")
            raise LLMNetworkError(f"Gemini API client error: {str(exc)}") from exc

        except genai_errors.ServerError as exc:
            logger.error(f"[GeminiClient] Gemini server error: {exc}")
            raise LLMNetworkError(
                "Gemini API server error. Please try again later."
            ) from exc

        except TimeoutError as exc:
            logger.error(f"[GeminiClient] Request timed out after {self._timeout}s")
            raise LLMTimeoutError(
                f"Gemini request timed out after {self._timeout} seconds."
            ) from exc

        except Exception as exc:
            # Broad catch for connection errors, DNS failures, etc.
            exc_type = type(exc).__name__
            logger.error(f"[GeminiClient] Unexpected error ({exc_type}): {exc}")
            raise LLMNetworkError(
                f"Could not connect to Gemini API: {str(exc)}"
            ) from exc

        # ── Extract response text ────────────────────────────
        try:
            content = response.text
        except (AttributeError, ValueError):
            content = None

        # Check for blocked / empty responses
        if not content or not content.strip():
            # Inspect the finish reason if available
            finish_reason = None
            try:
                finish_reason = response.candidates[0].finish_reason
            except (AttributeError, IndexError):
                pass

            if finish_reason and str(finish_reason) not in ("STOP", "1"):
                logger.warning(
                    f"[GeminiClient] Response blocked or stopped early. "
                    f"Finish reason: {finish_reason}"
                )
                raise LLMEmptyResponse(
                    f"Gemini response was blocked (finish_reason={finish_reason}). "
                    "Try rephrasing your query."
                )

            logger.warning("[GeminiClient] Received empty response content from Gemini.")
            raise LLMEmptyResponse("Gemini returned an empty response.")

        logger.info(
            f"[GeminiClient] Response received. Length: {len(content)} chars"
        )
        return content.strip()
