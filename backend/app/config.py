"""
Centralized application configuration.

All configuration is read from environment variables (via a .env file in
local development). Nothing here is hard-coded so that the AI provider,
model, ports, and limits can be changed without touching source code.
"""
from __future__ import annotations

import os
from functools import lru_cache

from dotenv import load_dotenv

# Load a .env file if present. In production, real environment variables
# take precedence and this is a no-op if no .env file exists.
load_dotenv()


def _get_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _get_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    try:
        return int(value)
    except ValueError:
        return default


class Settings:
    """Application settings loaded once and cached."""

    # --- AI provider configuration -----------------------------------
    # Only Google Gemini's free-tier developer API is supported. The key
    # and model are both configurable via environment variables so the
    # model can be swapped later (e.g. when a newer free-tier model is
    # released) without any code changes.
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "").strip()
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-1.5-flash").strip()

    # --- Server configuration ------------------------------------------
    BACKEND_HOST: str = os.getenv("BACKEND_HOST", "0.0.0.0")
    BACKEND_PORT: int = _get_int("BACKEND_PORT", 8000)
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:5173")

    # --- Limits ----------------------------------------------------------
    MAX_CODE_SIZE: int = _get_int("MAX_CODE_SIZE", 100_000)  # bytes (~100 KB)
    MAX_REQUEST_SIZE: int = _get_int("MAX_REQUEST_SIZE", 200_000)  # bytes

    # --- Gemini call behaviour ------------------------------------------
    GEMINI_TIMEOUT_SECONDS: int = _get_int("GEMINI_TIMEOUT_SECONDS", 45)
    GEMINI_MAX_RETRIES: int = _get_int("GEMINI_MAX_RETRIES", 2)

    # --- Feature flags -----------------------------------------------------
    # Arbitrary user-submitted code is never executed by default. This is a
    # deliberate security decision documented in the README. It can be
    # enabled by an operator who has set up proper sandboxing (e.g. a
    # locked-down, network-disabled Docker container) but the code path is
    # not wired into the API in this version.
    ENABLE_CODE_EXECUTION: bool = _get_bool("ENABLE_CODE_EXECUTION", False)

    SUPPORTED_LANGUAGES = ("python", "javascript", "typescript", "java", "cpp", "c")

    @property
    def has_api_key(self) -> bool:
        return bool(self.GEMINI_API_KEY)


@lru_cache
def get_settings() -> Settings:
    return Settings()
