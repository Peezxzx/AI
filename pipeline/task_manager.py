"""
Autonomous Coding Pipeline - Task Manager

Manages the lifecycle of autonomous coding tasks:
  - Create tasks with priority, type, and metadata
  - Track status (pending -> running -> completed/failed)
  - Query tasks by status, type, or priority
  - Generate statistics and history reports

This is a standalone pipeline task manager that complements (not replaces)
the existing ai_core/agents/task_manager.py which handles agent-level tasks.

Usage:
    from pipeline.task_manager import TaskManager, TaskType, TaskPriority
    tm = TaskManager()
    task_id = tm.create_task(TaskType.SCAN, "Scan project structure")
    tm.start_task(task_id)
    tm.complete_task(task_id, result={"files": 42})
"""

import uuid
import threading
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict

from pipeline import TaskStatus, TaskPriority
from pipeline.logger import get_logger, log_task_event

logger = get_logger("task_manager")


class TaskType(str, Enum):
    """Types of pipeline tasks."""
    SCAN = "scan_project"
    PLAN = "plan_changes"
    WRITE_CODE = "write_code"
    MODIFY_FILE = "modify_file"
    CREATE_FILE = "create_file"
    VALIDATE = "validate"
    UPDATE_MEMORY = "update_memory"
    GIT_COMMIT = "git_commit"
    CUSTOM = "custom"


@dataclass
class PipelineTask:
    """Represents a single pipeline task."""
    id: str
    task_type: TaskType
    description: str
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    duration_seconds: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["task_type"] = self.task_type.value
        d["priority"] = self.priority.value
        d["status"] = self.status.value
        d["created_at"] = self.created_at.isoformat()
        d["started_at"] = self.started_at.isoformat() if self.started_at else None
        d["completed_at"] = self.completed_at.isoformat() if self.completed_at else None
        return d


class TaskManager:
    """
    Thread-safe task manager for the autonomous coding pipeline.

    Tracks all tasks through their lifecycle and provides
    statistics, history, and querying capabilities.
    """

    def __init__(self):
        self._tasks: Dict[str, PipelineTask] = {}
        self._lock = threading.Lock()
        logger.info("TaskManager initialized")

    # ------------------------------------------------------------------
    # Task CRUD
    # ------------------------------------------------------------------
    def create_task(
        self,
        task_type: TaskType,
        description: str,
        priority: TaskPriority = TaskPriority.NORMAL,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Create a new task and return its ID."""
        task_id = str(uuid.uuid4())[:12]
        task = PipelineTask(
            id=task_id,
            task_type=task_type,
            description=description,
            priority=priority,
            metadata=metadata or {},
        )
        with self._lock:
            self._tasks[task_id] = task
        log_task_event(logger, task_id, "created", task_type=task_type.value)
        return task_id

    def get_task(self, task_id: str) -> Optional[PipelineTask]:
        """Get a task by ID."""
        return self._tasks.get(task_id)

    def start_task(self, task_id: str) -> bool:
        """Mark a task as running."""
        with self._lock:
            task = self._tasks.get(task_id)
            if not task or task.status != TaskStatus.PENDING:
                return False
            task.status = TaskStatus.RUNNING
            task.started_at = datetime.now(timezone.utc)
        log_task_event(logger, task_id, "started")
        return True

    def complete_task(self, task_id: str, result: Optional[Dict[str, Any]] = None) -> bool:
        """Mark a task as completed with optional result data."""
        with self._lock:
            task = self._tasks.get(task_id)
            if not task or task.status != TaskStatus.RUNNING:
                return False
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now(timezone.utc)
            task.result = result
            if task.started_at:
                task.duration_seconds = (task.completed_at - task.started_at).total_seconds()
        log_task_event(logger, task_id, "completed", duration=task.duration_seconds)
        return True

    def fail_task(self, task_id: str, error: str) -> bool:
        """Mark a task as failed with an error message."""
        with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return False
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.now(timezone.utc)
            task.error = error
            if task.started_at:
                task.duration_seconds = (task.completed_at - task.started_at).total_seconds()
        log_task_event(logger, task_id, "failed", error=error)
        return True

    def cancel_task(self, task_id: str) -> bool:
        """Cancel a pending or running task."""
        with self._lock:
            task = self._tasks.get(task_id)
            if not task or task.status not in (TaskStatus.PENDING, TaskStatus.RUNNING):
                return False
            task.status = TaskStatus.CANCELLED
            task.completed_at = datetime.now(timezone.utc)
        log_task_event(logger, task_id, "cancelled")
        return True

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------
    def get_tasks_by_status(self, status: TaskStatus) -> List[PipelineTask]:
        """Get all tasks with a given status."""
        return [t for t in self._tasks.values() if t.status == status]

    def get_tasks_by_type(self, task_type: TaskType) -> List[PipelineTask]:
        """Get all tasks of a given type."""
        return [t for t in self._tasks.values() if t.task_type == task_type]

    def get_all_tasks(self) -> List[PipelineTask]:
        """Get all tasks."""
        return list(self._tasks.values())

    def get_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get completed/failed tasks as dicts, most recent first."""
        completed = [
            t for t in self._tasks.values()
            if t.status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED)
        ]
        completed.sort(key=lambda t: t.completed_at or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
        return [t.to_dict() for t in completed[:limit]]

    # ------------------------------------------------------------------
    # Statistics
    # ------------------------------------------------------------------
    def get_statistics(self) -> Dict[str, Any]:
        """Get aggregate task statistics."""
        total = len(self._tasks)
        completed = sum(1 for t in self._tasks.values() if t.status == TaskStatus.COMPLETED)
        failed = sum(1 for t in self._tasks.values() if t.status == TaskStatus.FAILED)
        running = sum(1 for t in self._tasks.values() if t.status == TaskStatus.RUNNING)
        pending = sum(1 for t in self._tasks.values() if t.status == TaskStatus.PENDING)

        durations = [t.duration_seconds for t in self._tasks.values() if t.duration_seconds > 0]
        avg_duration = sum(durations) / len(durations) if durations else 0.0

        return {
            "total": total,
            "completed": completed,
            "failed": failed,
            "running": running,
            "pending": pending,
            "success_rate": (completed / (completed + failed) * 100) if (completed + failed) > 0 else 0.0,
            "average_duration_seconds": round(avg_duration, 2),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


# Global singleton
task_manager = TaskManager()
