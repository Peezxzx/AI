"""
Code Quality Control - Automated code analysis and quality control
"""

import ast
import os
import re
import subprocess
import json
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, asdict
from enum import Enum
import tempfile
import shutil
import asyncio
from pathlib import Path


class QualityMetric(Enum):
    """Code quality metrics"""
    CODE_COVERAGE = "code_coverage"
    COMPLEXITY = "complexity"
    DUPLICATION = "duplication"
    SECURITY = "security"
    PERFORMANCE = "performance"
    MAINTAINABILITY = "maintainability"
    RELIABILITY = "reliability"


class Severity(Enum):
    """Issue severity levels"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class Language(Enum):
    """Supported programming languages"""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    JAVA = "java"
    C_PLUS_PLUS = "c++"
    GO = "go"
    RUST = "rust"


@dataclass
class CodeIssue:
    """Code issue data structure"""
    file_path: str
    line_number: int
    column_number: int
    rule_id: str
    severity: Severity
    message: str
    category: str
    correction_suggestion: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "file_path": self.file_path,
            "line_number": self.line_number,
            "column_number": self.column_number,
            "rule_id": self.rule_id,
            "severity": self.severity.name,
            "message": self.message,
            "category": self.category,
            "correction_suggestion": self.correction_suggestion
        }


@dataclass
class QualityReport:
    """Code quality report"""
    file_path: str
    language: Language
    total_lines: int
    executable_lines: int
    issues: List[CodeIssue]
    metrics: Dict[str, float]
    score: float
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "file_path": self.file_path,
            "language": self.language.value,
            "total_lines": self.total_lines,
            "executable_lines": self.executable_lines,
            "issues": [issue.to_dict() for issue in self.issues],
            "metrics": self.metrics,
            "score": self.score,
            "timestamp": self.timestamp.isoformat()
        }


class ComplexityAnalyzer:
    """Code complexity analyzer"""
    
    def __init__(self):
        self.complexity_thresholds = {
            "low": 10,
            "medium": 20,
            "high": 30,
            "very_high": 50
        }
    
    def analyze_complexity(self, code: str, file_path: str) -> List[CodeIssue]:
        """Analyze code complexity"""
        issues = []
        
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                complexity = self._calculate_node_complexity(node)
                
                if complexity > self.complexity_thresholds["high"]:
                    issue = CodeIssue(
                        file_path=file_path,
                        line_number=node.lineno,
                        column_number=getattr(node, 'col_offset', 0),
                        rule_id="HIGH_COMPLEXITY",
                        severity=Severity.MEDIUM,
                        message=f"High complexity detected: {complexity}",
                        category="complexity",
                        correction_suggestion="Consider breaking down this function into smaller, more focused functions"
                    )
                    issues.append(issue)
        
        except SyntaxError as e:
            issue = CodeIssue(
                file_path=file_path,
                line_number=e.lineno,
                column_number=e.offset or 0,
                rule_id="SYNTAX_ERROR",
                severity=Severity.CRITICAL,
                message=f"Syntax error: {e.msg}",
                category="syntax",
                correction_suggestion="Fix the syntax error before proceeding"
            )
            issues.append(issue)
        
        return issues
    
    def _calculate_node_complexity(self, node: ast.AST) -> int:
        """Calculate complexity for a AST node"""
        complexity = 1  # Base complexity
        
        if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor)):
            complexity += 1
        elif isinstance(node, ast.ExceptHandler):
            complexity += 1
        elif isinstance(node, ast.BoolOp):
            complexity += len(node.values) - 1
        elif isinstance(node, ast.comprehension):
            complexity += 1
        
        # Recursively calculate complexity for child nodes
        for child in ast.iter_child_nodes(node):
            complexity += self._calculate_node_complexity(child)
        
        return complexity


class SecurityAnalyzer:
    """Security vulnerability analyzer"""
    
    def __init__(self):
        self.security_patterns = {
            "sql_injection": r"(SELECT|INSERT|UPDATE|DELETE).*\+.*\b(user|input|request)",
            "xss": r"innerHTML|outerHTML|document\.write",
            "hardcoded_password": r"(password|pwd|pass)\s*=\s*[\"'][^\"']{8,}[\"']",
            "hardcoded_secret": r"(secret|key|token)\s*=\s*[\"'][^\"']{16,}[\"']",
            "eval_usage": r"\beval\s*\(",
            "exec_usage": r"\bexec\s*\(",
            "pickle_usage": r"\bpickle\.",
            "shell_command": r"subprocess\.call|subprocess\.run|subprocess\.Popen|os\.system",
            "file_traversal": r"\.\.\.\/|\.\.\\",
            "insecure_random": r"random\.randint|random\.random",
            "deprecated_function": r"(urllib2|httplib|ConfigParser|cPickle)"
        }
    
    def analyze_security(self, code: str, file_path: str) -> List[CodeIssue]:
        """Analyze security vulnerabilities"""
        issues = []
        
        for pattern_name, pattern in self.security_patterns.items():
            matches = re.finditer(pattern, code, re.IGNORECASE | re.MULTILINE)
            
            for match in matches:
                line_number = code[:match.start()].count('\n') + 1
                column_number = match.start() - code.rfind('\n', 0, match.start())
                
                severity = self._get_severity_for_pattern(pattern_name)
                
                issue = CodeIssue(
                    file_path=file_path,
                    line_number=line_number,
                    column_number=column_number,
                    rule_id=f"SECURITY_{pattern_name.upper()}",
                    severity=severity,
                    message=f"Potential security vulnerability: {pattern_name}",
                    category="security",
                    correction_suggestion=self._get_correction_suggestion(pattern_name)
                )
                issues.append(issue)
        
        return issues
    
    def _get_severity_for_pattern(self, pattern_name: str) -> Severity:
        """Get severity level for security pattern"""
        high_severity = ["sql_injection", "xss", "hardcoded_password", "hardcoded_secret"]
        medium_severity = ["eval_usage", "exec_usage", "pickle_usage"]
        
        if pattern_name in high_severity:
            return Severity.HIGH
        elif pattern_name in medium_severity:
            return Severity.MEDIUM
        else:
            return Severity.LOW
    
    def _get_correction_suggestion(self, pattern_name: str) -> str:
        """Get correction suggestion for security pattern"""
        suggestions = {
            "sql_injection": "Use parameterized queries or ORM instead of string concatenation",
            "xss": "Use proper output encoding and avoid direct DOM manipulation",
            "hardcoded_password": "Use environment variables or secure configuration management",
            "hardcoded_secret": "Use environment variables or secure configuration management",
            "eval_usage": "Use safer alternatives like ast.literal_eval or proper parsing",
            "exec_usage": "Use safer alternatives or implement proper input validation",
            "pickle_usage": "Use safer serialization formats like JSON",
            "shell_command": "Use proper subprocess with proper argument escaping",
            "file_traversal": "Use proper path validation and sanitization",
            "insecure_random": "Use cryptographically secure random generator",
            "deprecated_function": "Use modern alternatives and update dependencies"
        }
        
        return suggestions.get(pattern_name, "Review and fix this security concern")


class PerformanceAnalyzer:
    """Performance issue analyzer"""
    
    def __init__(self):
        self.performance_patterns = {
            "nested_loops": r"for\s+.*\s+in\s+.*:\s*for\s+",
            "inefficient_string": r"\+\s*=\s*.*\b(string|list|dict)",
            "redundant_computation": r"(len|sum|max|min)\s*\(\s*[^)]+\s*\)\s*\*\s*\d+",
            "memory_leak": r"global\s+\w+\s*=\s*\[.*\]",
            "inefficient_dict": r"dict\.keys\(\)\s*in\s*",
            "repeated_function_calls": r"(\w+)\s*\([^)]*\)\s*==\s*\1\s*\("
        }
    
    def analyze_performance(self, code: str, file_path: str) -> List[CodeIssue]:
        """Analyze performance issues"""
        issues = []
        
        for pattern_name, pattern in self.performance_patterns.items():
            matches = re.finditer(pattern, code, re.IGNORECASE | re.MULTILINE)
            
            for match in matches:
                line_number = code[:match.start()].count('\n') + 1
                column_number = match.start() - code.rfind('\n', 0, match.start())
                
                issue = CodeIssue(
                    file_path=file_path,
                    line_number=line_number,
                    column_number=column_number,
                    rule_id=f"PERF_{pattern_name.upper()}",
                    severity=Severity.MEDIUM,
                    message=f"Performance issue: {pattern_name}",
                    category="performance",
                    correction_suggestion=self._get_performance_suggestion(pattern_name)
                )
                issues.append(issue)
        
        return issues
    
    def _get_performance_suggestion(self, pattern_name: str) -> str:
        """Get performance improvement suggestion"""
        suggestions = {
            "nested_loops": "Consider using list comprehensions, vectorized operations, or algorithmic optimizations",
            "inefficient_string": "Use string joins, list comprehensions, or more efficient data structures",
            "redundant_computation": "Cache results or precompute values to avoid redundant calculations",
            "memory_leak": "Use proper cleanup, context managers, or weak references",
            "inefficient_dict": "Use 'in dict' instead of 'in dict.keys()' for better performance",
            "repeated_function_calls": "Cache function results or restructure the logic"
        }
        
        return suggestions.get(pattern_name, "Review and optimize this code for better performance")


class CodeStyleAnalyzer:
    """Code style and maintainability analyzer"""
    
    def __init__(self):
        self.style_rules = {
            "line_length": r"^\s*[^\n]{120,}",
            "trailing_whitespace": r"\s+$",
            "missing_docstring": r"^def\s+\w+\s*\([^)]*\)\s*:",
            "unused_import": r"^import\s+\w+.*$",
            "camel_case": r"^[a-z_][a-z0-9_]*$",  # snake_case check
            "magic_numbers": r"\b(0[xX]?[0-9a-fA-F]+|\d+)\b(?!\s*[a-zA-Z_])"
        }
    
    def analyze_style(self, code: str, file_path: str) -> List[CodeIssue]:
        """Analyze code style and maintainability"""
        issues = []
        lines = code.split('\n')
        
        for i, line in enumerate(lines, 1):
            # Line length check
            if re.search(self.style_rules["line_length"], line):
                issue = CodeIssue(
                    file_path=file_path,
                    line_number=i,
                    column_number=120,
                    rule_id="LINE_LENGTH",
                    severity=Severity.LOW,
                    message="Line exceeds recommended length (120 characters)",
                    category="style",
                    correction_suggestion="Break long lines into multiple lines or shorten the line"
                )
                issues.append(issue)
            
            # Trailing whitespace
            if re.search(self.style_rules["trailing_whitespace"], line):
                issue = CodeIssue(
                    file_path=file_path,
                    line_number=i,
                    column_number=len(line),
                    rule_id="TRAILING_WHITESPACE",
                    severity=Severity.LOW,
                    message="Line has trailing whitespace",
                    category="style",
                    correction_suggestion="Remove trailing whitespace"
                )
                issues.append(issue)
            
            # Function without docstring
            if re.search(self.style_rules["missing_docstring"], line):
                # Check if next line contains docstring
                if i + 1 < len(lines) and not lines[i + 1].strip().startswith('"""') and not lines[i + 1].strip().startswith("'''"):
                    issue = CodeIssue(
                        file_path=file_path,
                        line_number=i,
                        column_number=0,
                        rule_id="MISSING_DOCSTRING",
                        severity=Severity.LOW,
                        message="Function missing docstring",
                        category="style",
                        correction_suggestion="Add docstring to document the function's purpose and parameters"
                    )
                    issues.append(issue)
        
        return issues


class CodeQualityAnalyzer:
    """Main code quality analyzer"""
    
    def __init__(self):
        self.complexity_analyzer = ComplexityAnalyzer()
        self.security_analyzer = SecurityAnalyzer()
        self.performance_analyzer = PerformanceAnalyzer()
        self.style_analyzer = CodeStyleAnalyzer()
        
        self.supported_languages = [Language.PYTHON, Language.JAVASCRIPT, Language.TYPESCRIPT]
    
    def analyze_file(self, file_path: str) -> Optional[QualityReport]:
        """Analyze a single file for code quality"""
        try:
            # Determine language
            language = self._detect_language(file_path)
            if language not in self.supported_languages:
                return None
            
            # Read file
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
            
            # Count lines
            total_lines = len(code.split('\n'))
            executable_lines = len([line for line in code.split('\n') if line.strip() and not line.strip().startswith('#')])
            
            # Analyze code
            all_issues = []
            
            # Complexity analysis
            complexity_issues = self.complexity_analyzer.analyze_complexity(code, file_path)
            all_issues.extend(complexity_issues)
            
            # Security analysis
            security_issues = self.security_analyzer.analyze_security(code, file_path)
            all_issues.extend(security_issues)
            
            # Performance analysis
            performance_issues = self.performance_analyzer.analyze_performance(code, file_path)
            all_issues.extend(performance_issues)
            
            # Style analysis
            style_issues = self.style_analyzer.analyze_style(code, file_path)
            all_issues.extend(style_issues)
            
            # Calculate metrics
            metrics = self._calculate_metrics(all_issues, total_lines, executable_lines)
            
            # Calculate overall score
            score = self._calculate_quality_score(all_issues, total_lines)
            
            # Create report
            report = QualityReport(
                file_path=file_path,
                language=language,
                total_lines=total_lines,
                executable_lines=executable_lines,
                issues=all_issues,
                metrics=metrics,
                score=score,
                timestamp=datetime.now(timezone.utc)
            )
            
            return report
        
        except Exception as e:
            print(f"Error analyzing file {file_path}: {e}")
            return None
    
    def analyze_directory(self, directory_path: str, extensions: List[str] = None) -> List[QualityReport]:
        """Analyze all files in a directory"""
        if extensions is None:
            extensions = ['.py', '.js', '.ts', '.java', '.cpp', '.go', '.rs']
        
        reports = []
        
        for root, dirs, files in os.walk(directory_path):
            for file in files:
                if any(file.endswith(ext) for ext in extensions):
                    file_path = os.path.join(root, file)
                    report = self.analyze_file(file_path)
                    if report:
                        reports.append(report)
        
        return reports
    
    def _detect_language(self, file_path: str) -> Language:
        """Detect programming language from file extension"""
        extension = os.path.splitext(file_path)[1].lower()
        
        language_map = {
            '.py': Language.PYTHON,
            '.js': Language.JAVASCRIPT,
            '.ts': Language.TYPESCRIPT,
            '.java': Language.JAVA,
            '.cpp': Language.C_PLUS_PLUS,
            '.cc': Language.C_PLUS_PLUS,
            '.cxx': Language.C_PLUS_PLUS,
            '.c++': Language.C_PLUS_PLUS,
            '.go': Language.GO,
            '.rs': Language.RUST
        }
        
        return language_map.get(extension, Language.PYTHON)
    
    def _calculate_metrics(self, issues: List[CodeIssue], total_lines: int, executable_lines: int) -> Dict[str, float]:
        """Calculate quality metrics"""
        if total_lines == 0:
            return {}
        
        # Count issues by severity
        severity_counts = {severity.name: 0 for severity in Severity}
        for issue in issues:
            severity_counts[issue.severity.name] += 1
        
        # Count issues by category
        category_counts = {}
        for issue in issues:
            category = issue.category
            category_counts[category] = category_counts.get(category, 0) + 1
        
        # Calculate density metrics
        issues_per_100_lines = (len(issues) / total_lines) * 100
        critical_issues_ratio = severity_counts['CRITICAL'] / len(issues) if issues else 0
        
        return {
            "total_issues": len(issues),
            "issues_per_100_lines": issues_per_100_lines,
            "critical_issues_ratio": critical_issues_ratio,
            "high_issues_count": severity_counts['HIGH'],
            "medium_issues_count": severity_counts['MEDIUM'],
            "low_issues_count": severity_counts['LOW'],
            "category_distribution": category_counts,
            "maintainability_index": max(0, 100 - (issues_per_100_lines * 2)),
            "security_score": max(0, 100 - (severity_counts['HIGH'] + severity_counts['CRITICAL']) * 10)
        }
    
    def _calculate_quality_score(self, issues: List[CodeIssue], total_lines: int) -> float:
        """Calculate overall quality score (0-100)"""
        if total_lines == 0:
            return 100.0
        
        # Base score
        score = 100.0
        
        # Deduct points for issues
        for issue in issues:
            if issue.severity == Severity.CRITICAL:
                score -= 10.0
            elif issue.severity == Severity.HIGH:
                score -= 5.0
            elif issue.severity == Severity.MEDIUM:
                score -= 2.0
            else:  # LOW
                score -= 1.0
        
        # Ensure score is within bounds
        return max(0, min(100, score))
    
    def get_trends(self, reports: List[QualityReport]) -> Dict[str, Any]:
        """Get quality trends from multiple reports"""
        if not reports:
            return {}
        
        # Calculate aggregate metrics
        total_files = len(reports)
        average_score = sum(report.score for report in reports) / total_files
        total_issues = sum(len(report.issues) for report in reports)
        
        # Find worst files
        worst_files = sorted(reports, key=lambda r: r.score)[:5]
        
        # Find common issues
        issue_frequency = {}
        for report in reports:
            for issue in report.issues:
                rule_id = issue.rule_id
                issue_frequency[rule_id] = issue_frequency.get(rule_id, 0) + 1
        
        common_issues = sorted(issue_frequency.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            "total_files": total_files,
            "average_score": average_score,
            "total_issues": total_issues,
            "issues_per_file": total_issues / total_files,
            "worst_files": [report.file_path for report in worst_files],
            "common_issues": common_issues,
            "language_distribution": self._get_language_distribution(reports)
        }
    
    def _get_language_distribution(self, reports: List[QualityReport]) -> Dict[str, int]:
        """Get distribution of languages in reports"""
        distribution = {}
        for report in reports:
            lang = report.language.value
            distribution[lang] = distribution.get(lang, 0) + 1
        return distribution


class CodeQualityController:
    """Controller for code quality operations"""
    
    def __init__(self):
        self.analyzer = CodeQualityAnalyzer()
        self.quality_thresholds = {
            "excellent": 90,
            "good": 75,
            "acceptable": 60,
            "poor": 0
        }
    
    def analyze_project(self, project_path: str, output_format: str = "json") -> Dict[str, Any]:
        """Analyze entire project for code quality"""
        reports = self.analyzer.analyze_directory(project_path)
        
        # Generate trends
        trends = self.analyzer.get_trends(reports)
        
        # Generate summary
        summary = {
            "project_path": project_path,
            "analysis_timestamp": datetime.now(timezone.utc).isoformat(),
            "total_files_analyzed": len(reports),
            "average_quality_score": trends.get("average_score", 0),
            "quality_grade": self._get_quality_grade(trends.get("average_score", 0)),
            "total_issues": trends.get("total_issues", 0),
            "critical_issues": sum(1 for report in reports for issue in report.issues if issue.severity == Severity.CRITICAL),
            "high_issues": sum(1 for report in reports for issue in report.issues if issue.severity == Severity.HIGH),
            "recommendations": self._generate_recommendations(trends, reports)
        }
        
        if output_format == "json":
            return {
                "summary": summary,
                "trends": trends,
                "reports": [report.to_dict() for report in reports]
            }
        else:
            return self._generate_text_report(summary, trends, reports)
    
    def _get_quality_grade(self, score: float) -> str:
        """Get quality grade based on score"""
        if score >= self.quality_thresholds["excellent"]:
            return "Excellent"
        elif score >= self.quality_thresholds["good"]:
            return "Good"
        elif score >= self.quality_thresholds["acceptable"]:
            return "Acceptable"
        else:
            return "Poor"
    
    def _generate_recommendations(self, trends: Dict[str, Any], reports: List[QualityReport]) -> List[str]:
        """Generate improvement recommendations"""
        recommendations = []
        
        # Overall quality recommendations
        if trends.get("average_score", 0) < 75:
            recommendations.append("Overall code quality needs improvement. Focus on critical and high-severity issues first.")
        
        # Issue-specific recommendations
        if trends.get("critical_issues", 0) > 0:
            recommendations.append(f"Address {trends['critical_issues']} critical issues immediately as they may cause security or functionality problems.")
        
        if trends.get("high_issues", 0) > 0:
            recommendations.append(f"Resolve {trends['high_issues']} high-severity issues to improve code reliability and maintainability.")
        
        # Security recommendations
        security_issues = sum(1 for report in reports for issue in report.issues if issue.category == "security")
        if security_issues > 0:
            recommendations.append(f"Found {security_issues} security issues. These should be addressed as soon as possible.")
        
        # Performance recommendations
        performance_issues = sum(1 for report in reports for issue in report.issues if issue.category == "performance")
        if performance_issues > 0:
            recommendations.append(f"Found {performance_issues} performance issues. Consider optimizing these areas.")
        
        return recommendations
    
    def _generate_text_report(self, summary: Dict[str, Any], trends: Dict[str, Any], reports: List[QualityReport]) -> str:
        """Generate human-readable text report"""
        report_lines = []
        
        report_lines.append("=" * 60)
        report_lines.append("CODE QUALITY ANALYSIS REPORT")
        report_lines.append("=" * 60)
        report_lines.append(f"Project: {summary['project_path']}")
        report_lines.append(f"Analysis Date: {summary['analysis_timestamp']}")
        report_lines.append(f"Total Files Analyzed: {summary['total_files_analyzed']}")
        report_lines.append(f"Average Quality Score: {summary['average_quality_score']:.1f}/100")
        report_lines.append(f"Quality Grade: {summary['quality_grade']}")
        report_lines.append(f"Total Issues: {summary['total_issues']}")
        report_lines.append(f"Critical Issues: {summary['critical_issues']}")
        report_lines.append(f"High Issues: {summary['high_issues']}")
        report_lines.append("")
        
        # Recommendations
        report_lines.append("RECOMMENDATIONS:")
        report_lines.append("-" * 30)
        for i, rec in enumerate(summary['recommendations'], 1):
            report_lines.append(f"{i}. {rec}")
        report_lines.append("")
        
        # Common issues
        if trends.get("common_issues"):
            report_lines.append("COMMON ISSUES:")
            report_lines.append("-" * 30)
            for rule_id, count in trends["common_issues"][:5]:
                report_lines.append(f"- {rule_id}: {count} occurrences")
            report_lines.append("")
        
        # Worst files
        if trends.get("worst_files"):
            report_lines.append("FILES NEEDING MOST ATTENTION:")
            report_lines.append("-" * 30)
            for file_path in trends["worst_files"][:3]:
                report_lines.append(f"- {file_path}")
            report_lines.append("")
        
        return "\n".join(report_lines)