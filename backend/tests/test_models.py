import pytest
from pydantic import ValidationError

from app.models.request_models import AnalyzeRequest
from app.models.response_models import Bug, MentorAnalysis


def test_analyze_request_rejects_empty_code():
    with pytest.raises(ValidationError):
        AnalyzeRequest(code="   ", language="python", difficulty="beginner")


def test_analyze_request_rejects_invalid_language():
    with pytest.raises(ValidationError):
        AnalyzeRequest(code="print(1)", language="cobol", difficulty="beginner")


def test_analyze_request_defaults_difficulty_to_beginner():
    req = AnalyzeRequest(code="print(1)", language="python")
    assert req.difficulty.value == "beginner"


def test_mentor_analysis_rejects_out_of_range_score():
    with pytest.raises(ValidationError):
        MentorAnalysis(language="python", summary="x", code_quality_score=150)


def test_bug_requires_all_core_fields():
    bug = Bug(
        title="Division by zero",
        type="runtime",
        severity="HIGH",
        line=2,
        verified=True,
        problem="p",
        explanation="e",
        suggested_fix="f",
    )
    assert bug.line == 2
    assert bug.verified is True


def test_bug_line_can_be_null():
    bug = Bug(
        title="Possible issue",
        type="logic",
        severity="LOW",
        line=None,
        verified=False,
        problem="p",
        explanation="e",
        suggested_fix="f",
    )
    assert bug.line is None
