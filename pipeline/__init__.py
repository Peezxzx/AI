"""
Autonomous Coding Pipeline - Shared Configuration & Constants

This package provides the core infrastructure for the autonomous coding pipeline.
All pipeline modules import shared types, constants, and configuration from here.

Modules:
    logger          - Centralized logging with file + console output
    task_manager    - Task lifecycle tracking (create, update, complete, fail)
    project_scanner - Project structure analysis (files, deps, complexity)
    code_writer     - Safe file creation and modification engine
    memory_updater  - Updates spec.md and hot.md after pipeline runs
    pipeline        - Main orchestrator that ties all modules together
"""

import os
from pathlib import Path
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Project-wide paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path("/root/Atsawin-AI-Core")
SPEC_FILE = PROJECT_ROOT / "spec.md"
HOT_FILE = PROJECT_ROOT / "hot.md"
LOG_DIR = PROJECT_ROOT / "AI" / "logs"
PIPELINE_LOG_DIR = LOG_DIR / "pipeline"
MEMORY_DIR = PROJECT_ROOT / "memory"

# Ensure directories exist
for _d in [LOG_DIR, PIPELINE_LOG_DIR, MEMORY_DIR]:
    _d.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------
class PipelinePhase(str, Enum):
    """High-level phases of the autonomous coding pipeline."""
    IDLE = "idle"
    SCANNING = "scanning"
    PLANNING = "planning"
    CODING = "coding"
    VALIDATING = "validating"
    UPDATING_MEMORY = "updating_memory"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(int, Enum):
    CRITICAL = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4
    BACKGROUND = 5


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------
@dataclass
class PipelineConfig:
    """Runtime configuration for a pipeline execution."""
    project_root: str = str(PROJECT_ROOT)
    max_concurrent_tasks: int = 3
    scan_ignore: List[str] = field(default_factory=lambda: [
        "__pycache__", "*.pyc", ".git", ".venv", "venv",
        "node_modules", ".DS_Store", "*.log", "dist", "build",
    ])
    log_to_file: bool = True
    log_to_console: bool = True
    update_memory: bool = True
    dry_run: bool = False


@dataclass
class PipelineResult:
    """Summary of a full pipeline execution."""
    success: bool
    phase_reached: PipelinePhase
    tasks_total: int
    tasks_completed: int
    tasks_failed: int
    files_created: int
    files_modified: int
    scan_summary: Optional[Dict[str, Any]] = None
    errors: List[str] = field(default_factory=list)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_seconds: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "phase_reached": self.phase_reached.value,
            "tasks_total": self.tasks_total,
            "tasks_completed": self.tasks_completed,
            "tasks_failed": self.tasks_failed,
            "files_created": self.files_created,
            "files_modified": self.files_modified,
            "scan_summary": self.scan_summary,
            "errors": self.errors,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": self.duration_seconds,
        }
