"""
Code Quality Analyzer - Checks syntax, style, complexity, security
"""
import ast
import re
import os
from pathlib import Path
from datetime import datetime
from .models import QualityReport, QualityIssue, Severity


def analyze_quality(path: str, checks: list[str] | None = None) -> QualityReport:
    """Analyze code quality for a file or directory."""
    if checks is None or "all" in checks:
        checks = ["syntax", "style", "complexity", "security"]

    target = Path(path)
    if not target.exists():
        raise FileNotFoundError(f"Path not found: {path}")

    report = QualityReport(path=str(target))

    if target.is_file():
        _analyze_file(target, checks, report)
    elif target.is_dir():
        for py_file in target.rglob("*.py"):
            if "__pycache__" not in str(py_file) and ".venv" not in str(py_file):
                _analyze_file(py_file, checks, report)

    # Calculate overall score
    if report.issues:
        severity_weights = {
            Severity.INFO: 0.1,
            Severity.WARNING: 0.3,
            Severity.ERROR: 0.6,
            Severity.CRITICAL: 1.0,
        }
        total_weight = sum(severity_weights.get(i.severity, 0.1) for i in report.issues)
        # Score starts at 1.0, decreases with issues
        report.overall_score = max(0.0, 1.0 - (total_weight * 0.05))
    else:
        report.overall_score = 1.0

    return report


def _analyze_file(filepath: Path, checks: list[str], report: QualityReport):
    """Analyze a single Python file."""
    try:
        source = filepath.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return

    lines = source.splitlines()
    rel_path = str(filepath)

    # Metrics
    loc = len(lines)
    comment_lines = sum(1 for l in lines if l.strip().startswith("#"))
    blank_lines = sum(1 for l in lines if not l.strip())
    code_lines = loc - blank_lines
    comment_ratio = comment_lines / code_lines if code_lines > 0 else 0.0

    report.metrics = {
        "lines_of_code": loc,
        "comment_ratio": round(comment_ratio, 3),
        "cyclomatic_complexity": _calc_complexity(source),
        "duplication_percentage": _calc_duplication(lines),
    }

    # Syntax check
    if "syntax" in checks:
        try:
            ast.parse(source)
        except SyntaxError as e:
            report.issues.append(QualityIssue(
                type="syntax",
                severity=Severity.ERROR,
                file=rel_path,
                line=e.lineno or 0,
                message=f"Syntax error: {e.msg}",
                suggestion="Fix the syntax error before proceeding.",
            ))

    # Style checks
    if "style" in checks:
        _check_style(lines, rel_path, report)

    # Complexity checks
    if "complexity" in checks:
        _check_complexity(source, rel_path, report)

    # Security checks
    if "security" in checks:
        _check_security(source, rel_path, report)


def _check_style(lines: list[str], filepath: str, report: QualityReport):
    """Check code style issues."""
    for i, line in enumerate(lines, 1):
        # Line too long (>120 chars)
        if len(line) > 120:
            report.issues.append(QualityIssue(
                type="style",
                severity=Severity.WARNING,
                file=filepath,
                line=i,
                message=f"Line too long ({len(line)} > 120 chars)",
                suggestion="Break the line into multiple lines.",
            ))

        # Trailing whitespace
        if line != line.rstrip():
            report.issues.append(QualityIssue(
                type="style",
                severity=Severity.INFO,
                file=filepath,
                line=i,
                message="Trailing whitespace",
                suggestion="Remove trailing whitespace.",
            ))

        # TODO/FIXME without assignee
        if re.search(r"#\s*(TODO|FIXME)\s*$", line, re.IGNORECASE):
            report.issues.append(QualityIssue(
                type="style",
                severity=Severity.INFO,
                file=filepath,
                line=i,
                message="TODO/FIXME without assignee",
                suggestion="Add assignee: TODO(username): description",
            ))


def _check_complexity(source: str, filepath: str, report: QualityReport):
    """Check cyclomatic complexity of functions."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            complexity = _node_complexity(node)
            if complexity > 10:
                severity = Severity.ERROR if complexity > 20 else Severity.WARNING
                report.issues.append(QualityIssue(
                    type="complexity",
                    severity=severity,
                    file=filepath,
                    line=node.lineno,
                    message=f"Function '{node.name}' has cyclomatic complexity {complexity} (threshold: 10)",
                    suggestion="Refactor into smaller functions.",
                ))


def _check_security(source: str, filepath: str, report: QualityReport):
    """Check for common security issues."""
    security_patterns = [
        (r"eval\s*\(", "Use of eval() is dangerous", Severity.CRITICAL),
        (r"exec\s*\(", "Use of exec() is dangerous", Severity.CRITICAL),
        (r"subprocess\..*shell\s*=\s*True", "subprocess with shell=True is a security risk", Severity.ERROR),
        (r"os\.system\s*\(", "os.system() is unsafe, use subprocess instead", Severity.ERROR),
        (r"pickle\.loads?\s*\(", "pickle.loads can execute arbitrary code", Severity.ERROR),
        (r"yaml\.load\s*\(.*Loader\s*=\s*Loader", "yaml.load without SafeLoader is unsafe", Severity.WARNING),
        (r"password\s*=\s*['\"]", "Hardcoded password detected", Severity.CRITICAL),
        (r"secret\s*=\s*['\"]", "Hardcoded secret detected", Severity.CRITICAL),
        (r"api_key\s*=\s*['\"]", "Hardcoded API key detected", Severity.CRITICAL),
        (r"DEBUG\s*=\s*True", "DEBUG=True should not be in production", Severity.WARNING),
        (r"verify\s*=\s*False", "SSL verification disabled", Severity.ERROR),
    ]

    lines = source.splitlines()
    for i, line in enumerate(lines, 1):
        for pattern, message, severity in security_patterns:
            if re.search(pattern, line):
                report.issues.append(QualityIssue(
                    type="security",
                    severity=severity,
                    file=filepath,
                    line=i,
                    message=message,
                    suggestion="Review and fix the security issue.",
                ))


def _calc_complexity(source: str) -> int:
    """Calculate overall cyclomatic complexity."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return 0

    total = 0
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            total += _node_complexity(node)
    return total


def _node_complexity(node: ast.AST) -> int:
    """Calculate cyclomatic complexity of a single function node."""
    complexity = 1
    for child in ast.walk(node):
        if isinstance(child, (ast.If, ast.While, ast.For,
                               ast.ExceptHandler, ast.With,
                               ast.Assert, ast.comprehension)):
            complexity += 1
        elif isinstance(child, ast.BoolOp):
            complexity += len(child.values) - 1
    return complexity


def _calc_duplication(lines: list[str]) -> float:
    """Calculate code duplication percentage."""
    if len(lines) < 10:
        return 0.0

    # Look for duplicate blocks of 5+ lines
    block_size = 5
    blocks = {}
    for i in range(len(lines) - block_size + 1):
        block = tuple(lines[i:i + block_size])
        if all(l.strip() for l in block):  # Skip blocks with only blank lines
            blocks[block] = blocks.get(block, 0) + 1

    duplicate_lines = sum(
        (count - 1) * block_size
        for count in blocks.values()
        if count > 1
    )

    return round(duplicate_lines / len(lines) * 100, 2) if lines else 0.0
