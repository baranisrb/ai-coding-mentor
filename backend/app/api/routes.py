"""API routes for the AI Coding Mentor Agent."""
from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Request

from app.ai.mentor_agent import MentorAgentError, run_hint
from app.config import get_settings
from app.models.request_models import AnalyzeRequest, HintRequest
from app.models.response_models import AnalyzeResponse, ErrorResponse, HintResponse
from app.services.analysis_service import analyze_code

logger = logging.getLogger("mentor.api")
router = APIRouter()


@router.get("/health")
async def health() -> dict:
    settings = get_settings()
    return {
        "status": "ok",
        "gemini_configured": settings.has_api_key,
        "gemini_model": settings.GEMINI_MODEL,
    }


def _validate_code_size(code: str) -> None:
    settings = get_settings()
    size = len(code.encode("utf-8"))
    if size > settings.MAX_CODE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=(
                f"Code is too large ({size} bytes). The maximum allowed size is "
                f"{settings.MAX_CODE_SIZE} bytes (~{settings.MAX_CODE_SIZE // 1000} KB)."
            ),
        )


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(request: AnalyzeRequest) -> AnalyzeResponse:
    _validate_code_size(request.code)

    try:
        return analyze_code(request)
    except MentorAgentError as exc:
        message = str(exc)
        if "GEMINI_API_KEY" in message:
            raise HTTPException(status_code=503, detail=(
                "The AI mentor is not configured on the server. "
                "An administrator needs to set GEMINI_API_KEY."
            )) from exc
        if "limit reached" in message.lower():
            raise HTTPException(status_code=429, detail=message) from exc
        logger.error("Mentor agent error: %s", message)
        raise HTTPException(
            status_code=502,
            detail="The AI mentor could not complete the analysis. Please try again.",
        ) from exc
    except Exception:  # noqa: BLE001
        logger.exception("Unexpected error during analysis")
        raise HTTPException(
            status_code=500,
            detail="An unexpected server error occurred. Please try again.",
        ) from None


@router.post("/analyze/python", response_model=AnalyzeResponse)
async def analyze_python_only(request: AnalyzeRequest) -> AnalyzeResponse:
    """Convenience alias that forces the Python analysis pipeline.

    Useful for clients that already know the code is Python and want to
    skip re-specifying the language, while still reusing full validation.
    """
    if request.language.value != "python":
        raise HTTPException(
            status_code=400,
            detail="This endpoint only accepts language='python'. Use /api/analyze for other languages.",
        )
    return await analyze(request)


@router.post("/hint", response_model=HintResponse)
async def hint(request: HintRequest) -> HintResponse:
    _validate_code_size(request.code)
    try:
        hint_text = run_hint(
            code=request.code,
            language=request.language.value,
            difficulty=request.difficulty.value,
        )
        return HintResponse(hint=hint_text, reveal_available=True)
    except MentorAgentError as exc:
        message = str(exc)
        if "limit reached" in message.lower():
            raise HTTPException(status_code=429, detail=message) from exc
        raise HTTPException(status_code=502, detail="Could not generate a hint right now.") from exc
