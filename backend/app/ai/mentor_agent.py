"""The AI Coding Mentor agent.

This module ties together prompt construction, the Gemini client, and
strict Pydantic validation of the model's structured output. It never
trusts the raw model output blindly: JSON is parsed defensively, validated
against `MentorAnalysis`, and a single bounded recovery attempt is made if
the first parse fails.
"""
from __future__ import annotations

import json
import logging
import re

from pydantic import ValidationError

from app.ai.gemini_client import (
    GeminiConfigError,
    GeminiRateLimitError,
    GeminiRequestError,
    get_gemini_client,
)
from app.ai.prompts import (
    SYSTEM_PROMPT,
    build_analysis_prompt,
    build_hint_prompt,
    static_findings_to_text,
)
from app.models.response_models import (
    AnalysisStatus,
    MentorAnalysis,
    StaticAnalysisResult,
)

logger = logging.getLogger("mentor.agent")


class MentorAgentError(Exception):
    """Raised when the mentor agent cannot produce a valid analysis."""


def _strip_code_fences(text: str) -> str:
    """Defensively strip markdown code fences if the model added them
    despite being asked not to."""
    stripped = text.strip()
    fence_match = re.match(r"^```(?:json)?\s*(.*)```$", stripped, re.DOTALL)
    if fence_match:
        return fence_match.group(1).strip()
    return stripped


def _parse_and_validate(raw_text: str) -> MentorAnalysis:
    cleaned = _strip_code_fences(raw_text)
    data = json.loads(cleaned)  # may raise json.JSONDecodeError
    return MentorAnalysis.model_validate(data)  # may raise ValidationError


def _fallback_analysis(language: str, reason: str) -> MentorAnalysis:
    """A safe, clearly-labelled degraded response used only when the AI
    output could not be validated even after a retry. This is never
    silently passed off as a full analysis: analysis_status is set to
    "partial" and the summary explains what happened.
    """
    return MentorAnalysis(
        language=language,
        summary=(
            "The AI mentor could not produce a fully structured analysis this "
            f"time ({reason}). Deterministic static-analysis results (if any) "
            "are still shown below. Please try again."
        ),
        code_quality_score=0,
        analysis_status=AnalysisStatus.PARTIAL,
        bugs=[],
        strengths=[],
        fixed_code="",
        changes=[],
        tests="",
        test_explanations=[],
        edge_cases=[],
        learning_points=[],
        next_exercise="",
    )


def run_analysis(
    *,
    code: str,
    language: str,
    difficulty: str,
    question: str | None,
    static_result: StaticAnalysisResult,
) -> MentorAnalysis:
    """Run the full AI analysis stage and return a validated MentorAnalysis.

    Raises MentorAgentError for configuration/rate-limit/request failures
    that the API layer should turn into HTTP error responses. Returns a
    "partial" MentorAnalysis (never raises) if Gemini responded but the
    output could not be validated even after one recovery attempt, so the
    user still gets deterministic static-analysis results.
    """
    static_findings_dicts = [f.model_dump() for f in static_result.findings]
    prompt = build_analysis_prompt(
        code=code,
        language=language,
        difficulty=difficulty,
        question=question,
        static_findings_summary=static_findings_to_text(static_findings_dicts),
    )

    client = get_gemini_client()

    try:
        raw_text = client.generate_json(system_prompt=SYSTEM_PROMPT, user_prompt=prompt)
    except (GeminiConfigError, GeminiRateLimitError, GeminiRequestError) as exc:
        raise MentorAgentError(str(exc)) from exc

    try:
        analysis = _parse_and_validate(raw_text)
    except (json.JSONDecodeError, ValidationError) as first_error:
        logger.warning("First Gemini response failed validation, retrying once: %s", first_error)
        try:
            retry_text = client.generate_json(
                system_prompt=SYSTEM_PROMPT,
                user_prompt=prompt
                + "\n\nIMPORTANT: Your previous response was not valid JSON matching the "
                "required schema. Return ONLY a single valid JSON object with no "
                "markdown fences and no extra text.",
            )
            analysis = _parse_and_validate(retry_text)
        except (GeminiConfigError, GeminiRateLimitError, GeminiRequestError) as exc:
            raise MentorAgentError(str(exc)) from exc
        except (json.JSONDecodeError, ValidationError) as second_error:
            logger.error("Gemini response failed validation twice: %s", second_error)
            return _fallback_analysis(language, "invalid AI response format")

    # Reconcile "verified" flags: any bug whose line matches a confirmed
    # static-analysis finding's line is marked verified=True. The AI is
    # never trusted to self-report verification.
    verified_lines = {f.line for f in static_result.findings if f.line is not None}
    for bug in analysis.bugs:
        if bug.line is not None and bug.line in verified_lines:
            bug.verified = True
        else:
            bug.verified = False

    return analysis


def run_hint(*, code: str, language: str, difficulty: str) -> str:
    prompt = build_hint_prompt(code=code, language=language, difficulty=difficulty)
    client = get_gemini_client()

    try:
        raw_text = client.generate_json(system_prompt=SYSTEM_PROMPT, user_prompt=prompt)
    except (GeminiConfigError, GeminiRateLimitError, GeminiRequestError) as exc:
        raise MentorAgentError(str(exc)) from exc

    try:
        cleaned = _strip_code_fences(raw_text)
        data = json.loads(cleaned)
        hint = data.get("hint")
        if not hint or not isinstance(hint, str):
            raise ValueError("missing 'hint' field")
        return hint
    except (json.JSONDecodeError, ValueError) as exc:
        logger.warning("Hint response failed validation: %s", exc)
        return "Take a closer look at how this function behaves with unusual or empty input."
