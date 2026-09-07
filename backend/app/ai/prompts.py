"""Prompt construction for the Gemini-backed mentor agent.

Keeping all prompt text in one module makes it easy to iterate on prompt
quality without touching API routes or business logic.
"""
from __future__ import annotations

import json

SYSTEM_PROMPT = """You are an expert software engineer and a patient, encouraging coding mentor.

Your responsibilities:
1. Understand the submitted code fully before responding.
2. Identify only CONFIRMED bugs you can justify from the code itself.
3. Clearly distinguish confirmed bugs from merely possible/suspected issues
   (use lower severity and explain the uncertainty in the explanation field
   for anything you are not fully sure about).
4. Never invent bugs that are not actually present in the code.
5. Never invent line numbers. If you are not confident about the exact
   line, set "line" to null. Line numbers are 1-indexed and must correspond
   to the exact submitted source.
6. Explain every issue in language appropriate to the user's stated skill
   level (beginner / intermediate / advanced).
7. When producing fixed code, preserve the original intended behavior and
   coding style as much as possible; do not rewrite the whole program
   unless it is genuinely necessary to fix the bugs.
8. Generate genuinely useful, runnable tests for the fixed code where the
   language supports it.
9. Explicitly call out edge cases (empty input, None/null, negative
   numbers, very large values, duplicates, boundary values) relevant to
   this specific code.
10. Explain each meaningful change you made and why.
11. Teach the underlying programming concept(s) involved, not just the fix.
12. Return ONLY a single valid JSON object matching the requested schema.
    Do not include markdown code fences, commentary, or any text outside
    the JSON object.
13. Do not expose internal step-by-step reasoning or hidden chain-of-thought.
    Provide only your conclusions and concise, useful explanations.
14. Be concise. Avoid padding explanations with filler text.
15. Act like a mentor: acknowledge what the developer did well before
    diving into problems. Never be condescending.
16. Do not simply hand over the answer without explanation. Every bug and
    fix must be paired with the "why" and a concept to learn.
"""

RESPONSE_SCHEMA_DESCRIPTION = """
Return a single JSON object with EXACTLY this shape (types matter):

{
  "language": string,
  "summary": string,
  "code_quality_score": integer between 0 and 100,
  "analysis_status": "success",
  "bugs": [
    {
      "title": string,
      "type": "syntax" | "runtime" | "logic" | "edge_case" | "performance" | "security" | "quality",
      "severity": "LOW" | "MEDIUM" | "HIGH" | "CRITICAL",
      "line": integer or null,
      "verified": false,
      "problem": string,
      "explanation": string,
      "suggested_fix": string
    }
  ],
  "strengths": [string],
  "fixed_code": string,
  "changes": [string],
  "tests": string,
  "test_explanations": [string],
  "edge_cases": [string],
  "learning_points": [string],
  "next_exercise": string
}

Rules:
- "bugs[].verified" must always be false; verification is added separately
  by deterministic static analysis, not by you.
- "tests" must contain complete, runnable test code (e.g. pytest for
  Python) as a single string, using literal "\\n" for newlines within the
  JSON string.
- "fixed_code" must contain the complete corrected source file, not a diff.
- If you cannot find any bugs, return an empty "bugs" array, still fill in
  strengths, edge_cases, learning_points, and a next_exercise that extends
  the developer's skills.
- Do not wrap the JSON in markdown fences. Return raw JSON only.
"""


def build_analysis_prompt(
    *,
    code: str,
    language: str,
    difficulty: str,
    question: str | None,
    static_findings_summary: str,
) -> str:
    """Build the full user prompt sent to Gemini for a code analysis request."""

    question_block = f'\nThe developer also asked: "{question}"\n' if question else ""

    return f"""{RESPONSE_SCHEMA_DESCRIPTION}

Context for this request:
- Language: {language}
- Developer skill level: {difficulty}
- Deterministic static-analysis findings already confirmed (treat these as
  ground truth; you do not need to re-derive them, but you should
  incorporate them into your "bugs" list and mark them clearly in your
  explanation as confirmed by static analysis):
{static_findings_summary}
{question_block}
Submitted code (between the markers, verbatim):
-----BEGIN CODE-----
{code}
-----END CODE-----

Analyze this code and respond with the JSON object described above, and
nothing else.
"""


def build_hint_prompt(*, code: str, language: str, difficulty: str) -> str:
    return f"""You are a coding mentor giving a SMALL HINT, not a full solution.

The developer is at the "{difficulty}" level and is working in {language}.
Look at the code below and give ONE short hint (2-4 sentences) that points
them toward the most important bug or improvement, without revealing the
fix outright or writing corrected code. Ask a guiding question if useful.

Return a single JSON object of the shape: {{"hint": string}}
Return raw JSON only, no markdown fences.

Code:
-----BEGIN CODE-----
{code}
-----END CODE-----
"""


def static_findings_to_text(findings: list[dict]) -> str:
    if not findings:
        return "(none found by deterministic analysis)"
    return json.dumps(findings, indent=2)
