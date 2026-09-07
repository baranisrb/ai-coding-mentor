"""Service layer: orchestrates the full analyze pipeline.

USER -> API -> language detection/validation -> static analysis ->
Gemini AI analysis -> merged structured response.

Keeping this logic out of the FastAPI route makes it independently
testable and keeps `routes.py` thin.
"""
from __future__ import annotations

from app.ai.mentor_agent import run_analysis
from app.analyzers.python_analyzer import analyze_python
from app.models.request_models import AnalyzeRequest
from app.models.response_models import (
    AnalyzeResponse,
    StaticAnalysisResult,
)


def run_static_analysis(code: str, language: str) -> StaticAnalysisResult:
    """Dispatch to the correct deterministic analyzer for the language.

    Only Python has full static-analysis support in this version. Other
    languages get a minimal, honestly-labelled result (fully_supported is
    False) so the AI-only findings are clearly distinguished in the UI.
    """
    if language == "python":
        return analyze_python(code)

    return StaticAnalysisResult(
        language=language,
        syntax_valid=True,  # unknown; we do not claim to have checked it
        findings=[],
        fully_supported=False,
    )


def analyze_code(request: AnalyzeRequest) -> AnalyzeResponse:
    static_result = run_static_analysis(request.code, request.language.value)

    mentor_result = run_analysis(
        code=request.code,
        language=request.language.value,
        difficulty=request.difficulty.value,
        question=request.question,
        static_result=static_result,
    )

    return AnalyzeResponse(static_analysis=static_result, mentor=mentor_result)
