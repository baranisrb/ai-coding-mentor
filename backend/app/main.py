"""FastAPI application entrypoint for the AI Coding Mentor Agent."""
from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.api.routes import router
from app.config import get_settings
from app.utils.logging_config import configure_logging

configure_logging()
logger = logging.getLogger("mentor.main")

settings = get_settings()

app = FastAPI(
    title="AI Coding Mentor Agent",
    description=(
        "An AI-powered coding mentor that reads submitted code, finds bugs, "
        "explains them, suggests fixes, generates tests, and teaches "
        "underlying concepts. Powered by the Google Gemini free-tier API."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@app.middleware("http")
async def limit_request_size(request: Request, call_next):
    content_length = request.headers.get("content-length")
    if content_length is not None and int(content_length) > settings.MAX_REQUEST_SIZE:
        return JSONResponse(
            status_code=413,
            content={"error": "Request too large", "detail": "The request body exceeds the allowed size."},
        )
    return await call_next(request)


@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    logger.warning("Validation error: %s", exc)
    return JSONResponse(
        status_code=422,
        content={"error": "Invalid request", "detail": "The request data did not match the expected format."},
    )


@app.get("/")
async def root() -> dict:
    return {
        "name": "AI Coding Mentor Agent",
        "docs": "/docs",
        "health": "/api/health",
    }


app.include_router(router, prefix="/api")


if not settings.has_api_key:
    logger.warning(
        "GEMINI_API_KEY is not set. /api/analyze and /api/hint will return 503 "
        "until it is configured in .env."
    )
