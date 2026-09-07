"""Optional, sandboxed execution of AI-generated pytest tests.

SECURITY: This is disabled by default (ENABLE_CODE_EXECUTION=false).
Arbitrary user-submitted code and AI-generated tests are never executed
inside the FastAPI process itself. When explicitly enabled by an operator,
execution happens in a separate subprocess with:
  * A hard timeout.
  * A fresh temporary working directory that is deleted afterwards.
  * No secrets/environment variables passed through.
  * The subprocess is only ever asked to run `python -m pytest`, never the
    raw submitted code as a shell string.

Even when enabled, this should only be run in an environment with proper
OS-level sandboxing (e.g. a locked-down, network-disabled container),
which this application does not itself provide. See README.md.
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

from app.config import get_settings

EXECUTION_TIMEOUT_SECONDS = 10


@dataclass
class TestExecutionResult:
    executed: bool
    passed: bool | None
    output: str


def run_generated_tests(fixed_code: str, tests: str) -> TestExecutionResult:
    """Attempt to run AI-generated pytest tests against the fixed code.

    Returns executed=False (with an explanatory message) unless the
    operator has explicitly enabled code execution via the
    ENABLE_CODE_EXECUTION environment variable.
    """
    settings = get_settings()
    if not settings.ENABLE_CODE_EXECUTION:
        return TestExecutionResult(
            executed=False,
            passed=None,
            output=(
                "Automatic test execution is disabled by default for security. "
                "Copy the generated tests and the fixed code into your own "
                "project to run them, or set ENABLE_CODE_EXECUTION=true in a "
                "properly sandboxed environment."
            ),
        )

    if not fixed_code.strip() or not tests.strip():
        return TestExecutionResult(executed=False, passed=None, output="No code or tests to run.")

    with tempfile.TemporaryDirectory(prefix="mentor_exec_") as tmp:
        tmp_path = Path(tmp)
        (tmp_path / "solution.py").write_text(fixed_code, encoding="utf-8")
        (tmp_path / "test_generated.py").write_text(
            "from solution import *\n\n" + tests, encoding="utf-8"
        )

        try:
            result = subprocess.run(  # noqa: S603 - fixed argv, no shell, sandboxed tmp dir
                [sys.executable, "-m", "pytest", "-q", str(tmp_path / "test_generated.py")],
                cwd=str(tmp_path),
                capture_output=True,
                text=True,
                timeout=EXECUTION_TIMEOUT_SECONDS,
                env={"PATH": "/usr/bin:/bin"},  # no inherited secrets/env vars
            )
        except subprocess.TimeoutExpired:
            return TestExecutionResult(
                executed=True,
                passed=False,
                output=f"Test execution timed out after {EXECUTION_TIMEOUT_SECONDS} seconds.",
            )

        combined_output = (result.stdout or "") + (result.stderr or "")
        return TestExecutionResult(
            executed=True,
            passed=result.returncode == 0,
            output=combined_output[-4000:],  # cap output size
        )
