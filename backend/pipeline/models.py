"""
Autonomous Coding Pipeline - Data Models
"""
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
from datetime import datetime


class PipelinePhase(str, Enum):
    IDLE = "idle"
    SCANNING = "scanning"
    PLANNING = "planning"
    CODING = "coding"
    VALIDATING = "validating"
    UPDATING_MEMORY = "updating_memory"
    COMPLETED = "completed"
    FAILED = "failed"


class PipelineStatus(str, Enum):
    STARTED = "started"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class FileAction(str, Enum):
    CREATE = "create"
    MODIFY = "modify"
    PATCH = "patch"
    APPEND = "append"
    DELETE = "delete"


class TestType(str, Enum):
    UNIT = "unit"
    INTEGRATION = "integration"
    E2E = "e2e"
    ALL = "all"


class CICDEnvironment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class Severity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class FilePlan:
    action: FileAction
    path: str
    content: Optional[str] = None
    old_string: Optional[str] = None
    new_string: Optional[str] = None
    overwrite: bool = False
    replace_all: bool = False


@dataclass
class PipelineRequest:
    plan: list[FilePlan] = field(default_factory=list)
    scan_only: bool = False
    update_memory: bool = False
    dry_run: bool = False


@dataclass
class PipelineResult:
    pipeline_id: str = ""
    status: PipelineStatus = PipelineStatus.STARTED
    phase: PipelinePhase = PipelinePhase.IDLE
    progress: float = 0.0
    files_created: int = 0
    files_modified: int = 0
    errors: list[str] = field(default_factory=list)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: float = 0.0


@dataclass
class PipelineReport:
    pipeline_id: str = ""
    success: bool = False
    phase_reached: str = ""
    tasks_total: int = 0
    tasks_completed: int = 0
    tasks_failed: int = 0
    files_created: int = 0
    files_modified: int = 0
    scan_summary: dict = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    duration_seconds: float = 0.0


@dataclass
class ScanResult:
    total_files: int = 0
    languages: dict = field(default_factory=dict)
    total_lines: int = 0
    dependencies: list[str] = field(default_factory=list)
    structure: dict = field(default_factory=dict)
    scanned_at: Optional[datetime] = None


@dataclass
class QualityIssue:
    type: str = ""
    severity: Severity = Severity.INFO
    file: str = ""
    line: int = 0
    message: str = ""
    suggestion: str = ""


@dataclass
class QualityReport:
    path: str = ""
    overall_score: float = 0.0
    issues: list[QualityIssue] = field(default_factory=list)
    metrics: dict = field(default_factory=dict)


@dataclass
class GitStatus:
    branch: str = ""
    clean: bool = True
    modified_files: list[str] = field(default_factory=list)
    untracked_files: list[str] = field(default_factory=list)
    last_commit: dict = field(default_factory=dict)


@dataclass
class CICDStage:
    name: str = ""
    status: str = "pending"
    duration_seconds: float = 0.0


@dataclass
class CICDResult:
    run_id: str = ""
    status: str = "triggered"
    environment: str = ""
    stages: list[CICDStage] = field(default_factory=list)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


@dataclass
class TestFailure:
    test_name: str = ""
    file: str = ""
    line: int = 0
    error: str = ""


@dataclass
class TestResult:
    test_run_id: str = ""
    status: str = "started"
    total_tests: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    coverage_percentage: float = 0.0
    duration_seconds: float = 0.0
    failures: list[TestFailure] = field(default_factory=list)
