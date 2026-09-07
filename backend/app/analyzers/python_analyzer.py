"""Deterministic static analysis for Python source code.

This module never calls any AI model. It only uses Python's built-in
`ast`/`compile` machinery plus a handful of conservative, well-understood
structural checks. Anything reported here is safe to mark as
``verified: true`` because it is not a language-model guess.
"""
from __future__ import annotations

import ast

from app.models.response_models import Severity, StaticAnalysisFinding, StaticAnalysisResult


def _line_of(node: ast.AST | None) -> int | None:
    return getattr(node, "lineno", None) if node is not None else None


class _UndefinedNameChecker(ast.NodeVisitor):
    """A best-effort, intentionally conservative undefined-name checker.

    This is NOT a full data-flow analysis (that is out of scope for a
    deterministic pre-check). It only flags names that are used at module
    level or inside a function without ever being assigned, imported,
    passed as a parameter, or being a Python builtin. False negatives are
    expected and acceptable; false positives are avoided by being
    conservative (e.g. comprehensions, globals, and closures are handled
    loosely and skipped when ambiguous).
    """

    def __init__(self) -> None:
        self.builtins = set(dir(__builtins__)) if isinstance(__builtins__, dict) else set(dir(__builtins__))
        self.findings: list[StaticAnalysisFinding] = []

    def check(self, tree: ast.Module) -> list[StaticAnalysisFinding]:
        defined: set[str] = set(self.builtins)
        # Collect all module-level assignments, function/class defs, and imports
        # first, since Python allows forward references within a module body
        # in many practical cases (e.g. functions calling functions defined
        # later at the top level).
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                defined.add(node.name)
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    defined.update(self._names_in_target(target))
            elif isinstance(node, (ast.AnnAssign, ast.AugAssign)):
                defined.update(self._names_in_target(node.target))
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                for alias in node.names:
                    defined.add((alias.asname or alias.name).split(".")[0])
            elif isinstance(node, ast.arg):
                defined.add(node.arg)
            elif isinstance(node, ast.Global):
                defined.update(node.names)
            elif isinstance(node, (ast.For, ast.comprehension)):
                target = getattr(node, "target", None)
                if target is not None:
                    defined.update(self._names_in_target(target))
            elif isinstance(node, ast.With):
                for item in node.items:
                    if item.optional_vars is not None:
                        defined.update(self._names_in_target(item.optional_vars))
            elif isinstance(node, ast.ExceptHandler) and node.name:
                defined.add(node.name)
            elif isinstance(node, ast.Lambda):
                for arg in node.args.args + node.args.kwonlyargs:
                    defined.add(arg.arg)

        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                if node.id not in defined and not node.id.startswith("_"):
                    self.findings.append(
                        StaticAnalysisFinding(
                            title=f"Possibly undefined name '{node.id}'",
                            severity=Severity.MEDIUM,
                            line=_line_of(node),
                            message=(
                                f"'{node.id}' is used but no assignment, import, parameter, "
                                "or definition for it was found anywhere in the module. "
                                "This may be a typo, or it may be a name defined dynamically "
                                "(in which case this warning can be ignored)."
                            ),
                        )
                    )
        return self.findings

    @staticmethod
    def _names_in_target(target: ast.AST) -> set[str]:
        names: set[str] = set()
        for node in ast.walk(target):
            if isinstance(node, ast.Name):
                names.add(node.id)
            elif isinstance(node, ast.Starred):
                names.update(_UndefinedNameChecker._names_in_target(node.value))
        return names


def _check_empty_input_handling(tree: ast.Module) -> list[StaticAnalysisFinding]:
    """Flag function definitions whose body divides/indexes a parameter
    without any visible guard, which is a common source of empty-input bugs
    (e.g. ZeroDivisionError on an empty list passed to len()).

    This is intentionally narrow and only flags the most common pattern:
    `sum(x) / len(x)`-style expressions using a bare division where the
    divisor is a call to len() on a function parameter, with no prior
    `if`/`try` guard referencing that parameter in the function body.
    """
    findings: list[StaticAnalysisFinding] = []

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        param_names = {a.arg for a in node.args.args}
        has_guard = any(
            isinstance(n, (ast.If, ast.Try)) for n in ast.walk(node)
        )
        for sub in ast.walk(node):
            if isinstance(sub, ast.BinOp) and isinstance(sub.op, ast.Div):
                divisor = sub.right
                divides_by_len_of_param = (
                    isinstance(divisor, ast.Call)
                    and isinstance(divisor.func, ast.Name)
                    and divisor.func.id == "len"
                    and divisor.args
                    and isinstance(divisor.args[0], ast.Name)
                    and divisor.args[0].id in param_names
                )
                if divides_by_len_of_param and not has_guard:
                    findings.append(
                        StaticAnalysisFinding(
                            title="Possible division by zero on empty input",
                            severity=Severity.HIGH,
                            line=_line_of(sub),
                            message=(
                                "This division uses len() of a function parameter as the "
                                "divisor with no surrounding if/try guard. If the argument "
                                "can be an empty sequence, this will raise ZeroDivisionError."
                            ),
                        )
                    )
    return findings


def analyze_python(code: str) -> StaticAnalysisResult:
    """Run deterministic static analysis on a Python source string.

    Always returns a StaticAnalysisResult. If the code has a syntax error,
    `syntax_valid` is False and the single relevant finding contains the
    real, non-invented line number reported by the Python parser.
    """
    findings: list[StaticAnalysisFinding] = []

    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        findings.append(
            StaticAnalysisFinding(
                title="SyntaxError",
                severity=Severity.CRITICAL,
                line=exc.lineno,
                message=str(exc.msg),
            )
        )
        return StaticAnalysisResult(
            language="python",
            syntax_valid=False,
            findings=findings,
            fully_supported=True,
        )
    except ValueError as exc:
        # Rare: e.g. null bytes in source.
        findings.append(
            StaticAnalysisFinding(
                title="Invalid source",
                severity=Severity.CRITICAL,
                line=None,
                message=str(exc),
            )
        )
        return StaticAnalysisResult(
            language="python",
            syntax_valid=False,
            findings=findings,
            fully_supported=True,
        )

    try:
        compile(code, "<submitted_code>", "exec")
    except (SyntaxError, ValueError) as exc:
        findings.append(
            StaticAnalysisFinding(
                title="Compilation error",
                severity=Severity.CRITICAL,
                line=getattr(exc, "lineno", None),
                message=str(exc),
            )
        )
        return StaticAnalysisResult(
            language="python",
            syntax_valid=False,
            findings=findings,
            fully_supported=True,
        )

    checker = _UndefinedNameChecker()
    findings.extend(checker.check(tree))
    findings.extend(_check_empty_input_handling(tree))

    return StaticAnalysisResult(
        language="python",
        syntax_valid=True,
        findings=findings,
        fully_supported=True,
    )
