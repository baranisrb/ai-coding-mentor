"""Thin wrapper around the official Google Gemini Python SDK.

This is the ONLY module that talks to the Gemini API. It is responsible
for:
  * Building the client from environment configuration.
  * Enforcing a request timeout.
  * A small, bounded retry strategy with exponential backoff for
    transient failures (429 rate limits, 5xx errors).
  * Translating SDK-specific exceptions into a small set of well-defined
    exceptions the rest of the app can handle without knowing about the
    Gemini SDK.

The Gemini API key is read once from settings and is NEVER logged, never
returned in any response, and never sent to the frontend.
"""
from __future__ import annotations

import logging
import time

import google.generativeai as genai
from google.api_core import exceptions as google_exceptions

from app.config import get_settings

logger = logging.getLogger("mentor.gemini")


class GeminiConfigError(Exception):
    """Raised when the Gemini client cannot be configured (e.g. no API key)."""


class GeminiRateLimitError(Exception):
    """Raised when the free-tier rate limit has been hit and retries are exhausted."""


class GeminiRequestError(Exception):
    """Raised for any other Gemini API failure (network, invalid response, etc.)."""


class GeminiClient:
    def __init__(self) -> None:
        self._settings = get_settings()
        self._configured = False

    def _ensure_configured(self) -> None:
        if self._configured:
            return
        if not self._settings.has_api_key:
            raise GeminiConfigError(
                "GEMINI_API_KEY is not set. Create a free key at Google AI Studio "
                "and add it to your .env file."
            )
        genai.configure(api_key=self._settings.GEMINI_API_KEY)
        self._configured = True

    def generate_json(self, *, system_prompt: str, user_prompt: str) -> str:
        """Call Gemini and return the raw text response (expected to be JSON).

        Applies a small bounded retry with exponential backoff for rate
        limits and transient server errors. Raises GeminiRateLimitError or
        GeminiRequestError on failure so callers can produce a friendly
        message without leaking SDK internals.
        """
        self._ensure_configured()

        model = genai.GenerativeModel(
            model_name=self._settings.GEMINI_MODEL,
            system_instruction=system_prompt,
            generation_config={
                "response_mime_type": "application/json",
                "temperature": 0.3,
            },
        )

        max_retries = self._settings.GEMINI_MAX_RETRIES
        last_error: Exception | None = None

        for attempt in range(max_retries + 1):
            try:
                response = model.generate_content(
                    user_prompt,
                    request_options={"timeout": self._settings.GEMINI_TIMEOUT_SECONDS},
                )
                text = getattr(response, "text", None)
                if not text:
                    raise GeminiRequestError("Gemini returned an empty response.")
                return text
            except google_exceptions.ResourceExhausted as exc:
                last_error = exc
                logger.warning("Gemini rate limit hit (attempt %s/%s)", attempt + 1, max_retries + 1)
                if attempt < max_retries:
                    time.sleep(2**attempt)
                    continue
                raise GeminiRateLimitError(
                    "Free AI API limit reached. Please wait and try again."
                ) from exc
            except google_exceptions.DeadlineExceeded as exc:
                last_error = exc
                logger.warning("Gemini request timed out (attempt %s/%s)", attempt + 1, max_retries + 1)
                if attempt < max_retries:
                    time.sleep(2**attempt)
                    continue
                raise GeminiRequestError("The AI request timed out. Please try again.") from exc
            except google_exceptions.GoogleAPIError as exc:
                last_error = exc
                status = getattr(exc, "code", None)
                if status is not None and 500 <= int(status) < 600 and attempt < max_retries:
                    logger.warning("Gemini server error, retrying (attempt %s/%s)", attempt + 1, max_retries + 1)
                    time.sleep(2**attempt)
                    continue
                raise GeminiRequestError(f"The AI service returned an error: {exc.__class__.__name__}") from exc
            except Exception as exc:  # noqa: BLE001 - translate any SDK surprise into our own type
                last_error = exc
                logger.exception("Unexpected error calling Gemini")
                raise GeminiRequestError("An unexpected error occurred while contacting the AI service.") from exc

        # Should not be reachable, but keeps type checkers happy.
        raise GeminiRequestError("The AI request failed for an unknown reason.") from last_error


_client: GeminiClient | None = None


def get_gemini_client() -> GeminiClient:
    global _client
    if _client is None:
        _client = GeminiClient()
    return _client
