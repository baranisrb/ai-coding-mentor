"""Application-wide logging configuration.

Ensures no secrets (e.g. GEMINI_API_KEY) are ever logged, and gives every
request a predictable log format.
"""
from __future__ import annotations

import logging


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    # Quiet down noisy third-party loggers that could otherwise print
    # request bodies/headers.
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("google").setLevel(logging.WARNING)
