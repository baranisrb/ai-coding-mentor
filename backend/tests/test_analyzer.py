from app.analyzers.python_analyzer import analyze_python


def test_valid_code_has_no_syntax_error():
    code = "def add(a, b):\n    return a + b\n"
    result = analyze_python(code)
    assert result.syntax_valid is True
    assert result.fully_supported is True


def test_syntax_error_detected_with_real_line_number():
    code = "def greet(name)\n    print('Hello', name)\n"
    result = analyze_python(code)
    assert result.syntax_valid is False
    assert len(result.findings) == 1
    assert result.findings[0].title == "SyntaxError"
    assert result.findings[0].line == 1


def test_missing_colon_detected():
    code = "def add(a, b)\n    return a + b\n"
    result = analyze_python(code)
    assert result.syntax_valid is False
    assert result.findings[0].line is not None


def test_division_by_zero_on_empty_list_flagged():
    code = (
        "def calculate_average(numbers):\n"
        "    return sum(numbers) / len(numbers)\n"
    )
    result = analyze_python(code)
    assert result.syntax_valid is True
    titles = [f.title for f in result.findings]
    assert any("division by zero" in t.lower() for t in titles)


def test_guarded_division_not_flagged():
    code = (
        "def calculate_average(numbers):\n"
        "    if not numbers:\n"
        "        return 0\n"
        "    return sum(numbers) / len(numbers)\n"
    )
    result = analyze_python(code)
    titles = [f.title for f in result.findings]
    assert not any("division by zero" in t.lower() for t in titles)


def test_undefined_name_flagged():
    code = "def show():\n    print(undefined_variable)\n"
    result = analyze_python(code)
    titles = [f.title for f in result.findings]
    assert any("undefined name" in t.lower() for t in titles)


def test_never_invents_line_numbers_for_undefined_names():
    code = "def show():\n    print(undefined_variable)\n"
    result = analyze_python(code)
    for finding in result.findings:
        # Every finding must either have a real int line or explicitly None.
        assert finding.line is None or isinstance(finding.line, int)
