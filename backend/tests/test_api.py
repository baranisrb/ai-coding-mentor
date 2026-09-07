import json

import pytest
from fastapi.testclient import TestClient

from app.ai.gemini_client import GeminiRateLimitError
import app.ai.mentor_agent as mentor_agent
from app.main import app

client = TestClient(app)

VALID_GEMINI_JSON = json.dumps(
    {
        "language": "python",
        "summary": "The function divides by len() without guarding against an empty list.",
        "code_quality_score": 70,
        "analysis_status": "success",
        "bugs": [
            {
                "title": "Division by zero on empty input",
                "type": "runtime",
                "severity": "HIGH",
                "line": 2,
                "verified": False,
                "problem": "sum(numbers) / len(numbers) fails when numbers is empty.",
                "explanation": "len([]) is 0, and dividing by zero raises ZeroDivisionError.",
                "suggested_fix": "Return 0 or raise a clear error when the list is empty.",
            }
        ],
        "strengths": ["Clear function name", "Simple, readable structure"],
        "fixed_code": "def calculate_average(numbers):\n    if not numbers:\n        return 0\n    return sum(numbers) / len(numbers)\n",
        "changes": ["Added a guard for empty input"],
        "tests": "def test_normal():\n    assert calculate_average([2, 4]) == 3\n\ndef test_empty():\n    assert calculate_average([]) == 0\n",
        "test_explanations": ["Covers the normal case", "Covers the empty-list edge case"],
        "edge_cases": ["Empty list", "Negative numbers"],
        "learning_points": ["Always validate input before dividing"],
        "next_exercise": "Modify the function to also handle a list containing non-numeric values.",
    }
)


def test_analyze_missing_code_returns_422():
    response = client.post(
        "/api/analyze",
        json={"code": "", "language": "python", "difficulty": "beginner"},
    )
    assert response.status_code == 422


def test_analyze_unsupported_language_returns_422():
    response = client.post(
        "/api/analyze",
        json={"code": "print(1)", "language": "cobol", "difficulty": "beginner"},
    )
    assert response.status_code == 422


def test_analyze_python_only_rejects_other_languages():
    response = client.post(
        "/api/analyze/python",
        json={"code": "console.log(1)", "language": "javascript", "difficulty": "beginner"},
    )
    assert response.status_code == 400


def test_analyze_success_with_mocked_gemini(monkeypatch):
    monkeypatch.setattr(
        mentor_agent,
        "get_gemini_client",
        lambda: type("FakeClient", (), {"generate_json": staticmethod(lambda **_: VALID_GEMINI_JSON)})(),
    )

    code = "def calculate_average(numbers):\n    return sum(numbers) / len(numbers)\n"
    response = client.post(
        "/api/analyze",
        json={"code": code, "language": "python", "difficulty": "beginner"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["mentor"]["analysis_status"] == "success"
    assert body["static_analysis"]["syntax_valid"] is True
    # The static analyzer independently found the same line -> should be verified.
    bug_lines = {b["line"]: b["verified"] for b in body["mentor"]["bugs"]}
    assert bug_lines.get(2) is True


def test_analyze_syntax_error_short_circuits_static_analysis(monkeypatch):
    monkeypatch.setattr(
        mentor_agent,
        "get_gemini_client",
        lambda: type("FakeClient", (), {"generate_json": staticmethod(lambda **_: VALID_GEMINI_JSON)})(),
    )
    code = "def greet(name)\n    print('hi', name)\n"
    response = client.post(
        "/api/analyze",
        json={"code": code, "language": "python", "difficulty": "beginner"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["static_analysis"]["syntax_valid"] is False
    assert body["static_analysis"]["findings"][0]["title"] == "SyntaxError"


def test_analyze_rate_limit_returns_429(monkeypatch):
    def raise_rate_limit(**_):
        raise GeminiRateLimitError("Free AI API limit reached. Please wait and try again.")

    monkeypatch.setattr(
        mentor_agent,
        "get_gemini_client",
        lambda: type("FakeClient", (), {"generate_json": staticmethod(raise_rate_limit)})(),
    )
    response = client.post(
        "/api/analyze",
        json={"code": "print(1)", "language": "python", "difficulty": "beginner"},
    )
    assert response.status_code == 429


def test_analyze_invalid_ai_json_falls_back_gracefully(monkeypatch):
    monkeypatch.setattr(
        mentor_agent,
        "get_gemini_client",
        lambda: type("FakeClient", (), {"generate_json": staticmethod(lambda **_: "not valid json")})(),
    )
    response = client.post(
        "/api/analyze",
        json={"code": "print(1)", "language": "python", "difficulty": "beginner"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["mentor"]["analysis_status"] == "partial"


def test_hint_endpoint_success(monkeypatch):
    monkeypatch.setattr(
        mentor_agent,
        "get_gemini_client",
        lambda: type(
            "FakeClient",
            (),
            {"generate_json": staticmethod(lambda **_: json.dumps({"hint": "Think about what happens with an empty list."}))},
        )(),
    )
    response = client.post(
        "/api/hint",
        json={"code": "print(1)", "language": "python", "difficulty": "beginner"},
    )
    assert response.status_code == 200
    assert "hint" in response.json()
