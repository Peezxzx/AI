"""
Automated Testing Framework - Comprehensive testing system for AI agents and code
"""

import os
import sys
import subprocess
import json
import asyncio
import tempfile
import shutil
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
import importlib.util
import inspect
from pathlib import Path
import traceback
import ast


class TestStatus(Enum):
    """Test status"""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


class TestType(Enum):
    """Test types"""
    UNIT = "unit"
    INTEGRATION = "integration"
    E2E = "e2e"
    PERFORMANCE = "performance"
    SECURITY = "security"
    LOAD = "load"


@dataclass
class TestCase:
    """Test case data structure"""
    test_id: str
    name: str
    test_type: TestType
    description: str
    setup_code: str
    test_code: str
    teardown_code: str
    tags: List[str]
    timeout: int = 30
    expected_result: Optional[Any] = None
    status: TestStatus = TestStatus.PENDING
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration: Optional[float] = None
    error_message: Optional[str] = None
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    result: Optional[Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "test_id": self.test_id,
            "name": self.name,
            "test_type": self.test_type.value,
            "description": self.description,
            "setup_code": self.setup_code,
            "test_code": self.test_code,
            "teardown_code": self.teardown_code,
            "tags": self.tags,
            "timeout": self.timeout,
            "expected_result": self.expected_result,
            "status": self.status.value,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration": self.duration,
            "error_message": self.error_message,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "result": self.result
        }


@dataclass
class TestSuite:
    """Test suite data structure"""
    suite_id: str
    name: str
    description: str
    test_cases: List[TestCase]
    setup_suite_code: str
    teardown_suite_code: str
    tags: List[str]
    status: TestStatus = TestStatus.PENDING
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration: Optional[float] = None
    summary: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "suite_id": self.suite_id,
            "name": self.name,
            "description": self.description,
            "test_cases": [test.to_dict() for test in self.test_cases],
            "setup_suite_code": self.setup_suite_code,
            "teardown_suite_code": self.teardown_suite_code,
            "tags": self.tags,
            "status": self.status.value,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration": self.duration,
            "summary": self.summary
        }


@dataclass
class TestReport:
    """Test execution report"""
    report_id: str
    project_name: str
    suite_name: str
    total_tests: int
    passed_tests: int
    failed_tests: int
    skipped_tests: int
    error_tests: int
    duration: float
    start_time: datetime
    end_time: datetime
    suites: List[TestSuite]
    environment: Dict[str, Any]
    coverage: Optional[Dict[str, Any]] = None
    artifacts: List[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "report_id": self.report_id,
            "project_name": self.project_name,
            "suite_name": self.suite_name,
            "total_tests": self.total_tests,
            "passed_tests": self.passed_tests,
            "failed_tests": self.failed_tests,
            "skipped_tests": self.skipped_tests,
            "error_tests": self.error_tests,
            "duration": self.duration,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "suites": [suite.to_dict() for suite in self.suites],
            "environment": self.environment,
            "coverage": self.coverage,
            "artifacts": self.artifacts or []
        }


class TestExecutor:
    """Test execution engine"""
    
    def __init__(self, workspace_path: str = "/tmp/test_workspace"):
        self.workspace_path = workspace_path
        self.test_reports: Dict[str, TestReport] = {}
        
        # Ensure workspace exists
        os.makedirs(workspace_path, exist_ok=True)
    
    async def execute_test_case(self, test_case: TestCase) -> TestCase:
        """Execute a single test case"""
        test_case.status = TestStatus.RUNNING
        test_case.start_time = datetime.now(timezone.utc)
        
        try:
            # Create test directory
            test_dir = os.path.join(self.workspace_path, test_case.test_id)
            os.makedirs(test_dir, exist_ok=True)
            
            # Setup environment
            test_globals = {
                "__file__": os.path.join(test_dir, "test_case.py"),
                "__name__": "__main__",
                "test_case": test_case
            }
            
            # Execute setup code
            if test_case.setup_code:
                exec(test_case.setup_code, test_globals)
            
            # Execute test code with timeout
            try:
                exec(test_case.test_code, test_globals)
                test_case.result = test_globals.get("result")
                test_case.status = TestStatus.PASSED
            except Exception as e:
                test_case.error_message = str(e)
                test_case.status = TestStatus.FAILED
                test_case.stderr = traceback.format_exc()
            
            # Execute teardown code
            if test_case.teardown_code:
                try:
                    exec(test_case.teardown_code, test_globals)
                except Exception as e:
                    test_case.error_message = f"Teardown failed: {str(e)}"
                    test_case.stderr = traceback.format_exc()
            
        except Exception as e:
            test_case.status = TestStatus.ERROR
            test_case.error_message = str(e)
            test_case.stderr = traceback.format_exc()
        
        finally:
            test_case.end_time = datetime.now(timezone.utc)
            if test_case.start_time:
                test_case.duration = (test_case.end_time - test_case.start_time).total_seconds()
        
        return test_case
    
    async def execute_test_suite(self, test_suite: TestSuite) -> TestSuite:
        """Execute a test suite"""
        test_suite.status = TestStatus.RUNNING
        test_suite.start_time = datetime.now(timezone.utc)
        
        try:
            # Create suite directory
            suite_dir = os.path.join(self.workspace_path, test_suite.suite_id)
            os.makedirs(suite_dir, exist_ok=True)
            
            # Setup environment
            suite_globals = {
                "__file__": os.path.join(suite_dir, "test_suite.py"),
                "__name__": "__main__",
                "test_suite": test_suite
            }
            
            # Execute suite setup code
            if test_suite.setup_suite_code:
                exec(test_suite.setup_suite_code, suite_globals)
            
            # Execute test cases
            results = []
            for test_case in test_suite.test_cases:
                result = await self.execute_test_case(test_case)
                results.append(result)
            
            test_suite.test_cases = results
            
            # Execute suite teardown code
            if test_suite.teardown_suite_code:
                try:
                    exec(test_suite.teardown_suite_code, suite_globals)
                except Exception as e:
                    print(f"Suite teardown failed: {str(e)}")
            
            # Generate summary
            test_suite.summary = self._generate_suite_summary(test_suite)
            
        except Exception as e:
            test_suite.status = TestStatus.ERROR
            test_suite.error_message = str(e)
        
        finally:
            test_suite.end_time = datetime.now(timezone.utc)
            if test_suite.start_time:
                test_suite.duration = (test_suite.end_time - test_suite.start_time).total_seconds()
        
        return test_suite
    
    def _generate_suite_summary(self, test_suite: TestSuite) -> Dict[str, Any]:
        """Generate test suite summary"""
        total_tests = len(test_suite.test_cases)
        passed_tests = sum(1 for test in test_suite.test_cases if test.status == TestStatus.PASSED)
        failed_tests = sum(1 for test in test_suite.test_cases if test.status == TestStatus.FAILED)
        error_tests = sum(1 for test in test_suite.test_cases if test.status == TestStatus.ERROR)
        skipped_tests = sum(1 for test in test_suite.test_cases if test.status == TestStatus.SKIPPED)
        
        # Group by test type
        type_counts = {}
        for test in test_suite.test_cases:
            test_type = test.test_type.value
            type_counts[test_type] = type_counts.get(test_type, 0) + 1
        
        # Group by status
        status_counts = {}
        for test in test_suite.test_cases:
            status = test.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Calculate success rate
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        return {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "error_tests": error_tests,
            "skipped_tests": skipped_tests,
            "success_rate": success_rate,
            "type_distribution": type_counts,
            "status_distribution": status_counts,
            "average_duration": sum(test.duration or 0 for test in test_suite.test_cases) / total_tests if total_tests > 0 else 0
        }
    
    async def execute_test_report(self, project_name: str, suite_name: str,
                                test_suites: List[TestSuite]) -> TestReport:
        """Execute test suites and generate report"""
        # Generate report ID
        report_id = f"report_{project_name}_{suite_name}_{int(datetime.now(timezone.utc).timestamp())}"
        
        # Create test report
        test_report = TestReport(
            report_id=report_id,
            project_name=project_name,
            suite_name=suite_name,
            total_tests=sum(len(suite.test_cases) for suite in test_suites),
            passed_tests=0,
            failed_tests=0,
            skipped_tests=0,
            error_tests=0,
            duration=0,
            start_time=datetime.now(timezone.utc),
            end_time=datetime.now(timezone.utc),
            suites=test_suites,
            environment=self._get_environment_info(),
            coverage=None,
            artifacts=[]
        )
        
        # Execute test suites
        results = []
        for test_suite in test_suites:
            result = await self.execute_test_suite(test_suite)
            results.append(result)
        
        test_report.suites = results
        
        # Calculate summary
        test_report = self._calculate_report_summary(test_report)
        
        # Store report
        self.test_reports[report_id] = test_report
        
        return test_report
    
    def _get_environment_info(self) -> Dict[str, Any]:
        """Get environment information"""
        return {
            "python_version": sys.version,
            "platform": sys.platform,
            "architecture": os.uname(),
            "environment_variables": dict(os.environ),
            "working_directory": os.getcwd(),
            "test_workspace": self.workspace_path
        }
    
    def _calculate_report_summary(self, test_report: TestReport) -> TestReport:
        """Calculate test report summary"""
        total_tests = test_report.total_tests
        passed_tests = sum(1 for suite in test_report.suites 
                          for test in suite.test_cases if test.status == TestStatus.PASSED)
        failed_tests = sum(1 for suite in test_report.suites 
                          for test in suite.test_cases if test.status == TestStatus.FAILED)
        error_tests = sum(1 for suite in test_report.suites 
                         for test in suite.test_cases if test.status == TestStatus.ERROR)
        skipped_tests = sum(1 for suite in test_report.suites 
                           for test in suite.test_cases if test.status == TestStatus.SKIPPED)
        
        test_report.passed_tests = passed_tests
        test_report.failed_tests = failed_tests
        test_report.error_tests = error_tests
        test_report.skipped_tests = skipped_tests
        
        # Calculate duration
        if test_report.suites:
            test_report.duration = sum(suite.duration or 0 for suite in test_report.suites)
        
        # Calculate coverage (simplified)
        test_report.coverage = self._calculate_coverage(test_report)
        
        return test_report
    
    def _calculate_coverage(self, test_report: TestReport) -> Dict[str, Any]:
        """Calculate test coverage (simplified)"""
        # In real implementation, this would use coverage.py or similar
        return {
            "lines_covered": 0,
            "lines_total": 0,
            "coverage_percentage": 0,
            "branches_covered": 0,
            "branches_total": 0,
            "functions_covered": 0,
            "functions_total": 0
        }
    
    def get_test_report(self, report_id: str) -> Optional[TestReport]:
        """Get test report by ID"""
        return self.test_reports.get(report_id)
    
    def get_test_reports_by_project(self, project_name: str) -> List[TestReport]:
        """Get test reports by project"""
        return [report for report in self.test_reports.values() 
                if report.project_name == project_name]


class TestFramework:
    """Main testing framework"""
    
    def __init__(self, workspace_path: str = "/tmp/test_workspace"):
        self.executor = TestExecutor(workspace_path)
        self.test_discovery = TestDiscovery()
    
    def discover_tests_from_directory(self, directory_path: str) -> List[TestSuite]:
        """Discover tests from directory"""
        return self.test_discovery.discover_tests_from_directory(directory_path)
    
    def discover_tests_from_file(self, file_path: str) -> List[TestSuite]:
        """Discover tests from file"""
        return self.test_discovery.discover_tests_from_file(file_path)
    
    async def run_tests(self, project_name: str, suite_name: str,
                       test_suites: List[TestSuite]) -> TestReport:
        """Run test suites and generate report"""
        return await self.executor.execute_test_report(project_name, suite_name, test_suites)
    
    def get_test_report(self, report_id: str) -> Optional[TestReport]:
        """Get test report by ID"""
        return self.executor.get_test_report(report_id)
    
    def get_test_reports_by_project(self, project_name: str) -> List[TestReport]:
        """Get test reports by project"""
        return self.executor.get_test_reports_by_project(project_name)


class TestDiscovery:
    """Test discovery and loading"""
    
    def __init__(self):
        self.supported_extensions = ['.py', '.js', '.ts', '.java', '.cpp', '.go', '.rs']
    
    def discover_tests_from_directory(self, directory_path: str) -> List[TestSuite]:
        """Discover tests from directory"""
        test_suites = []
        
        for root, dirs, files in os.walk(directory_path):
            # Skip hidden directories
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            
            for file in files:
                if any(file.endswith(ext) for ext in self.supported_extensions):
                    file_path = os.path.join(root, file)
                    file_suites = self.discover_tests_from_file(file_path)
                    test_suites.extend(file_suites)
        
        return test_suites
    
    def discover_tests_from_file(self, file_path: str) -> List[TestSuite]:
        """Discover tests from file"""
        test_suites = []
        
        try:
            # Parse file for test functions/classes
            if file_path.endswith('.py'):
                test_suites = self._discover_python_tests(file_path)
            elif file_path.endswith('.js'):
                test_suites = self._discover_javascript_tests(file_path)
            elif file_path.endswith('.ts'):
                test_suites = self._discover_typescript_tests(file_path)
            elif file_path.endswith('.java'):
                test_suites = self._discover_java_tests(file_path)
        
        except Exception as e:
            print(f"Error discovering tests in {file_path}: {e}")
        
        return test_suites
    
    def _discover_python_tests(self, file_path: str) -> List[TestSuite]:
        """Discover Python tests"""
        test_suites = []
        
        try:
            # Read file
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse AST to find test functions
            tree = ast.parse(content)
            
            test_functions = []
            test_classes = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name.startswith('test_'):
                    test_functions.append(node)
                elif isinstance(node, ast.ClassDef) and node.name.startswith('Test'):
                    test_classes.append(node)
            
            # Create test suite for functions
            if test_functions:
                test_cases = []
                for func in test_functions:
                    test_case = TestCase(
                        test_id=f"{file_path}_{func.name}",
                        name=func.name,
                        test_type=TestType.UNIT,
                        description=ast.get_docstring(func) or "",
                        setup_code="",
                        test_code=self._extract_function_code(content, func),
                        teardown_code="",
                        tags=["python", "unit"],
                        timeout=30
                    )
                    test_cases.append(test_case)
                
                test_suite = TestSuite(
                    suite_id=f"python_tests_{file_path}",
                    name=f"Python Tests - {os.path.basename(file_path)}",
                    description="Python unit tests discovered from file",
                    test_cases=test_cases,
                    setup_suite_code="",
                    teardown_suite_code="",
                    tags=["python", "unit", "discovered"]
                )
                test_suites.append(test_suite)
        
        except Exception as e:
            print(f"Error discovering Python tests in {file_path}: {e}")
        
        return test_suites
    
    def _discover_javascript_tests(self, file_path: str) -> List[TestSuite]:
        """Discover JavaScript tests"""
        test_suites = []
        
        try:
            # Read file
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Simple regex-based discovery
            import re
            
            # Find test functions
            test_functions = re.findall(r'function\s+(test_\w+)\s*\(', content)
            test_methods = re.findall(r'it\s*\(\s*[\'"]([^\'"]+)[\'"]\s*,', content)
            
            test_cases = []
            for func_name in test_functions:
                test_case = TestCase(
                    test_id=f"{file_path}_{func_name}",
                    name=func_name,
                    test_type=TestType.UNIT,
                    description=f"JavaScript test function: {func_name}",
                    setup_code="",
                    test_code=f"// Test function: {func_name}\n// Implementation not available for discovered tests",
                    teardown_code="",
                    tags=["javascript", "unit"],
                    timeout=30
                )
                test_cases.append(test_case)
            
            for method_name in test_methods:
                test_case = TestCase(
                    test_id=f"{file_path}_{method_name}",
                    name=method_name,
                    test_type=TestType.UNIT,
                    description=f"JavaScript test method: {method_name}",
                    setup_code="",
                    test_code=f"// Test method: {method_name}\n// Implementation not available for discovered tests",
                    teardown_code="",
                    tags=["javascript", "unit"],
                    timeout=30
                )
                test_cases.append(test_case)
            
            if test_cases:
                test_suite = TestSuite(
                    suite_id=f"javascript_tests_{file_path}",
                    name=f"JavaScript Tests - {os.path.basename(file_path)}",
                    description="JavaScript tests discovered from file",
                    test_cases=test_cases,
                    setup_suite_code="",
                    teardown_suite_code="",
                    tags=["javascript", "unit", "discovered"]
                )
                test_suites.append(test_suite)
        
        except Exception as e:
            print(f"Error discovering JavaScript tests in {file_path}: {e}")
        
        return test_suites
    
    def _discover_typescript_tests(self, file_path: str) -> List[TestSuite]:
        """Discover TypeScript tests"""
        # Similar to JavaScript discovery
        return self._discover_javascript_tests(file_path)
    
    def _discover_java_tests(self, file_path: str) -> List[TestSuite]:
        """Discover Java tests"""
        test_suites = []
        
        try:
            # Read file
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Simple regex-based discovery
            import re
            
            # Find JUnit test methods
            test_methods = re.findall(r'@Test\s+public\s+void\s+(\w+)\s*\(', content)
            
            test_cases = []
            for method_name in test_methods:
                test_case = TestCase(
                    test_id=f"{file_path}_{method_name}",
                    name=method_name,
                    test_type=TestType.UNIT,
                    description=f"Java test method: {method_name}",
                    setup_code="",
                    test_code=f"// Test method: {method_name}\n// Implementation not available for discovered tests",
                    teardown_code="",
                    tags=["java", "unit"],
                    timeout=30
                )
                test_cases.append(test_case)
            
            if test_cases:
                test_suite = TestSuite(
                    suite_id=f"java_tests_{file_path}",
                    name=f"Java Tests - {os.path.basename(file_path)}",
                    description="Java tests discovered from file",
                    test_cases=test_cases,
                    setup_suite_code="",
                    teardown_suite_code="",
                    tags=["java", "unit", "discovered"]
                )
                test_suites.append(test_suite)
        
        except Exception as e:
            print(f"Error discovering Java tests in {file_path}: {e}")
        
        return test_suites
    
    def _extract_function_code(self, content: str, func_node: ast.FunctionDef) -> str:
        """Extract function code from source"""
        # Get function start and end lines
        start_line = func_node.lineno - 1
        end_line = func_node.end_lineno if hasattr(func_node, 'end_lineno') else start_line + 10
        
        lines = content.split('\n')
        function_lines = lines[start_line:end_line]
        
        # Find the actual function end
        indent_level = len(function_lines[0]) - len(function_lines[0].lstrip())
        function_lines = []
        
        for i, line in enumerate(lines[start_line:]):
            if i == 0:
                function_lines.append(line)
            else:
                current_indent = len(line) - len(line.lstrip())
                if current_indent <= indent_level and line.strip():
                    break
                function_lines.append(line)
        
        return '\n'.join(function_lines)


class AutomatedTestingController:
    """Controller for automated testing operations"""
    
    def __init__(self, workspace_path: str = "/tmp/test_workspace"):
        self.framework = TestFramework(workspace_path)
        self.test_configs: Dict[str, Dict[str, Any]] = {}
    
    def configure_test_run(self, project_name: str, config: Dict[str, Any]) -> str:
        """Configure test run settings"""
        self.test_configs[project_name] = config
        return f"config_{project_name}_{int(datetime.now(timezone.utc).timestamp())}"
    
    async def run_project_tests(self, project_path: str, project_name: str,
                              test_types: List[TestType] = None) -> TestReport:
        """Run tests for a project"""
        if test_types is None:
            test_types = [TestType.UNIT, TestType.INTEGRATION]
        
        # Discover tests
        test_suites = self.framework.discover_tests_from_directory(project_path)
        
        # Filter by test type
        filtered_suites = []
        for suite in test_suites:
            filtered_tests = []
            for test in suite.test_cases:
                if test.test_type in test_types:
                    filtered_tests.append(test)
            
            if filtered_tests:
                suite.test_cases = filtered_tests
                filtered_suites.append(suite)
        
        # Run tests
        report = await self.framework.run_tests(project_name, "discovered_tests", filtered_suites)
        
        return report
    
    def generate_test_report(self, report: TestReport, output_format: str = "json") -> str:
        """Generate test report in specified format"""
        if output_format == "json":
            return json.dumps(report.to_dict(), indent=2)
        elif output_format == "html":
            return self._generate_html_report(report)
        elif output_format == "text":
            return self._generate_text_report(report)
        else:
            raise ValueError(f"Unsupported output format: {output_format}")
    
    def _generate_html_report(self, report: TestReport) -> str:
        """Generate HTML test report"""
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Test Report - {project_name}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
                .summary {{ background-color: #e8f5e8; padding: 15px; margin: 20px 0; border-radius: 5px; }}
                .failed {{ background-color: #ffebee; }}
                .error {{ background-color: #fff3e0; }}
                .passed {{ background-color: #e8f5e8; }}
                .skipped {{ background-color: #f3e5f5; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Test Report - {project_name}</h1>
                <p>Generated: {timestamp}</p>
            </div>
            
            <div class="summary">
                <h2>Summary</h2>
                <ul>
                    <li>Total Tests: {total_tests}</li>
                    <li>Passed: {passed_tests}</li>
                    <li>Failed: {failed_tests}</li>
                    <li>Errors: {error_tests}</li>
                    <li>Skipped: {skipped_tests}</li>
                    <li>Success Rate: {success_rate:.1f}%</li>
                    <li>Duration: {duration:.2f}s</li>
                </ul>
            </div>
            
            <div class="suites">
                <h2>Test Suites</h2>
                {suites_html}
            </div>
        </body>
        </html>
        """
        
        # Generate suites HTML
        suites_html = ""
        for suite in report.suites:
            suites_html += f"""
            <div class="suite">
                <h3>{suite.name}</h3>
                <p>{suite.description}</p>
                <table>
                    <tr>
                        <th>Test Name</th>
                        <th>Type</th>
                        <th>Status</th>
                        <th>Duration</th>
                        <th>Message</th>
                    </tr>
            """
            
            for test in suite.test_cases:
                status_class = test.status.value
                suites_html += f"""
                    <tr class="{status_class}">
                        <td>{test.name}</td>
                        <td>{test.test_type.value}</td>
                        <td>{test.status.value}</td>
                        <td>{test.duration:.2f}s</td>
                        <td>{test.error_message or ''}</td>
                    </tr>
                """
            
            suites_html += """
                </table>
            </div>
            """
        
        return html_template.format(
            project_name=report.project_name,
            timestamp=report.start_time.isoformat(),
            total_tests=report.total_tests,
            passed_tests=report.passed_tests,
            failed_tests=report.failed_tests,
            error_tests=report.error_tests,
            skipped_tests=report.skipped_tests,
            success_rate=(report.passed_tests / report.total_tests * 100) if report.total_tests > 0 else 0,
            duration=report.duration,
            suites_html=suites_html
        )
    
    def _generate_text_report(self, report: TestReport) -> str:
        """Generate text test report"""
        lines = []
        lines.append("=" * 60)
        lines.append(f"TEST REPORT - {report.project_name}")
        lines.append("=" * 60)
        lines.append(f"Generated: {report.start_time.isoformat()}")
        lines.append(f"Total Tests: {report.total_tests}")
        lines.append(f"Passed: {report.passed_tests}")
        lines.append(f"Failed: {report.failed_tests}")
        lines.append(f"Errors: {report.error_tests}")
        lines.append(f"Skipped: {report.skipped_tests}")
        lines.append(f"Success Rate: {(report.passed_tests / report.total_tests * 100):.1f}%")
        lines.append(f"Duration: {report.duration:.2f}s")
        lines.append("")
        
        for suite in report.suites:
            lines.append(f"SUITE: {suite.name}")
            lines.append("-" * 40)
            
            for test in suite.test_cases:
                status_emoji = {
                    TestStatus.PASSED: "✓",
                    TestStatus.FAILED: "✗",
                    TestStatus.ERROR: "!",
                    TestStatus.SKIPPED: "○"
                }.get(test.status, "?")
                
                lines.append(f"  {status_emoji} {test.name} ({test.test_type.value}) - {test.status.value}")
                
                if test.error_message:
                    lines.append(f"      Error: {test.error_message}")
                
                if test.duration:
                    lines.append(f"      Duration: {test.duration:.2f}s")
            
            lines.append("")
        
        return "\n".join(lines)
    
    def get_test_history(self, project_name: str, limit: int = 50) -> List[TestReport]:
        """Get test history for project"""
        reports = self.framework.get_test_reports_by_project(project_name)
        return sorted(reports, key=lambda r: r.start_time, reverse=True)[:limit]
    
    def get_test_metrics(self, project_name: str) -> Dict[str, Any]:
        """Get test metrics for project"""
        reports = self.framework.get_test_reports_by_project(project_name)
        
        if not reports:
            return {}
        
        # Calculate aggregate metrics
        total_reports = len(reports)
        total_tests = sum(r.total_tests for r in reports)
        total_passed = sum(r.passed_tests for r in reports)
        total_failed = sum(r.failed_tests for r in reports)
        total_errors = sum(r.error_tests for r in reports)
        total_duration = sum(r.duration for r in reports)
        
        # Calculate trends
        success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
        avg_duration = total_duration / total_reports if total_reports > 0 else 0
        
        # Test type distribution
        type_distribution = {}
        for report in reports:
            for suite in report.suites:
                for test in suite.test_cases:
                    test_type = test.test_type.value
                    type_distribution[test_type] = type_distribution.get(test_type, 0) + 1
        
        return {
            "total_reports": total_reports,
            "total_tests": total_tests,
            "total_passed": total_passed,
            "total_failed": total_failed,
            "total_errors": total_errors,
            "success_rate": success_rate,
            "average_duration": avg_duration,
            "test_type_distribution": type_distribution,
            "last_run": reports[0].start_time.isoformat() if reports else None
        }