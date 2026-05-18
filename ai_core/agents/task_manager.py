"""
Autonomous Coding Pipeline - Task Manager
Handles task tracking, prioritization, and lifecycle management for autonomous coding operations.
"""

import asyncio
import uuid
import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
from concurrent.futures import ThreadPoolExecutor
import threading
from queue import Queue, Empty

from backend.memory_manager import memory_manager


class TaskPriority(Enum):
    CRITICAL = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4
    BACKGROUND = 5


class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskType(Enum):
    SCAN_PROJECT = "scan_project"
    GENERATE_CODE = "generate_code"
    ANALYZE_CODE = "analyze_code"
    REFRACTOR_CODE = "refactor_code"
    ADD_TESTS = "add_tests"
    DOCUMENTATION = "documentation"
    INTEGRATE_MODULE = "integrate_module"
    FIX_BUGS = "fix_bugs"
    OPTIMIZE_PERFORMANCE = "optimize_performance"


@dataclass
class CodingTask:
    id: str
    task_type: TaskType
    description: str
    priority: TaskPriority
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    estimated_duration: Optional[int] = None  # in seconds
    actual_duration: Optional[int] = None
    progress: float = 0.0  # 0.0 to 1.0
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    dependencies: List[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)
        if self.dependencies is None:
            self.dependencies = []
        if self.metadata is None:
            self.metadata = {}


class TaskManager:
    """Manages autonomous coding pipeline tasks with priority-based scheduling and dependencies."""
    
    def __init__(self, max_concurrent_tasks: int = 3):
        self.max_concurrent_tasks = max_concurrent_tasks
        self.logger = self._setup_logger()
        
        # Task storage
        self.tasks: Dict[str, CodingTask] = {}
        self.task_queue: List[str] = []  # task IDs, prioritized
        self.running_tasks: Dict[str, CodingTask] = {}
        self.completed_tasks: List[CodingTask] = []
        
        # Task execution
        self.executor = ThreadPoolExecutor(max_workers=max_concurrent_tasks)
        self.is_running = False
        self.execution_thread = None
        
        # Callbacks
        self.task_callbacks: Dict[str, Callable] = {}
        self.progress_callbacks: Dict[str, Callable] = {}
        
        # Performance metrics
        self.total_tasks = 0
        self.completed_count = 0
        self.failed_count = 0
        self.total_execution_time = 0.0
        
        # Lock for thread safety
        self._lock = threading.Lock()
        
        self.logger.info("Task Manager initialized")
    
    def _setup_logger(self) -> logging.Logger:
        """Setup logging configuration."""
        logger = logging.getLogger("task_manager")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    async def start(self):
        """Start the task manager."""
        with self._lock:
            if self.is_running:
                return
            
            self.is_running = True
            self.execution_thread = threading.Thread(target=self._execution_loop, daemon=True)
            self.execution_thread.start()
            
            self.logger.info("Task Manager started")
            
            # Store in memory for system tracking
            await memory_manager.store_memory(
                key="task_manager_status",
                value={"status": "running", "started_at": datetime.now(timezone.utc).isoformat()},
                memory_type="system",
                tags=["task_manager", "autonomous_coding"]
            )
    
    async def stop(self):
        """Stop the task manager."""
        with self._lock:
            if not self.is_running:
                return
            
            self.is_running = False
            
            # Cancel all running tasks
            for task_id in list(self.running_tasks.keys()):
                await self.cancel_task(task_id)
            
            self.logger.info("Task Manager stopped")
            
            # Update memory
            await memory_manager.store_memory(
                key="task_manager_status",
                value={"status": "stopped", "stopped_at": datetime.now(timezone.utc).isoformat()},
                memory_type="system",
                tags=["task_manager", "autonomous_coding"]
            )
    
    def _execution_loop(self):
        """Main execution loop for processing tasks."""
        while self.is_running:
            try:
                with self._lock:
                    if not self.task_queue or len(self.running_tasks) >= self.max_concurrent_tasks:
                        continue
                    
                    # Get next task from queue (highest priority first)
                    task_id = self.task_queue.pop(0)
                    task = self.tasks.get(task_id)
                    
                    if not task or task.status != TaskStatus.PENDING:
                        continue
                    
                    # Check dependencies
                    if not self._check_dependencies_met(task):
                        # Re-add to end of queue if dependencies not met
                        self.task_queue.append(task_id)
                        continue
                    
                    # Start task execution
                    task.status = TaskStatus.RUNNING
                    task.started_at = datetime.now(timezone.utc)
                    self.running_tasks[task_id] = task
                    
                    # Execute in thread pool
                    future = self.executor.submit(self._execute_task, task)
                    
            except Exception as e:
                self.logger.error(f"Error in execution loop: {e}")
            
            # Sleep briefly to avoid busy waiting
            threading.Event().wait(0.1)
    
    def _check_dependencies_met(self, task: CodingTask) -> bool:
        """Check if all task dependencies are completed."""
        for dep_id in task.dependencies:
            dep_task = self.tasks.get(dep_id)
            if not dep_task or dep_task.status != TaskStatus.COMPLETED:
                return False
        return True
    
    def _execute_task(self, task: CodingTask):
        """Execute a single task."""
        try:
            start_time = datetime.now(timezone.utc)
            
            # Call task callback if registered
            if task.task_type.value in self.task_callbacks:
                result = self.task_callbacks[task.task_type.value](task)
            else:
                # Default execution - just mark as completed
                result = {"status": "completed", "message": "Task executed successfully"}
            
            # Update task result
            with self._lock:
                task.result = result
                task.status = TaskStatus.COMPLETED
                task.completed_at = datetime.now(timezone.utc)
                task.actual_duration = (task.completed_at - start_time).total_seconds()
                
                # Move from running to completed
                self.running_tasks.pop(task.id, None)
                self.completed_tasks.append(task)
                
                # Update metrics
                self.completed_count += 1
                self.total_execution_time += task.actual_duration
                
                # Sort completed tasks by completion time
                self.completed_tasks.sort(key=lambda t: t.completed_at or datetime.min, reverse=True)
                
                self.logger.info(f"Task completed: {task.id} - {task.description}")
            
            # Call progress callback
            if task.id in self.progress_callbacks:
                self.progress_callbacks[task.id](100.0, "Task completed")
            
            # Store in memory for tracking
            asyncio.create_task(self._store_task_result(task))
            
        except Exception as e:
            with self._lock:
                task.status = TaskStatus.FAILED
                task.error = str(e)
                task.completed_at = datetime.now(timezone.utc)
                
                self.running_tasks.pop(task.id, None)
                self.completed_tasks.append(task)
                self.failed_count += 1
                
                self.logger.error(f"Task failed: {task.id} - {str(e)}")
            
            # Call progress callback
            if task.id in self.progress_callbacks:
                self.progress_callbacks[task.id](0.0, f"Task failed: {str(e)}")
            
            # Store error in memory
            asyncio.create_task(self._store_task_error(task))
    
    async def _store_task_result(self, task: CodingTask):
        """Store task result in memory."""
        try:
            await memory_manager.store_memory(
                key=f"task_result_{task.id}",
                value=asdict(task),
                memory_type="task_result",
                tags=["autonomous_coding", task.task_type.value]
            )
        except Exception as e:
            self.logger.error(f"Failed to store task result: {e}")
    
    async def _store_task_error(self, task: CodingTask):
        """Store task error in memory."""
        try:
            await memory_manager.store_memory(
                key=f"task_error_{task.id}",
                value={
                    "task_id": task.id,
                    "error": task.error,
                    "task_type": task.task_type.value,
                    "description": task.description,
                    "timestamp": task.completed_at.isoformat()
                },
                memory_type="task_error",
                tags=["autonomous_coding", "error", task.task_type.value]
            )
        except Exception as e:
            self.logger.error(f"Failed to store task error: {e}")
    
    def create_task(self, 
                   task_type: TaskType,
                   description: str,
                   priority: TaskPriority = TaskPriority.NORMAL,
                   dependencies: List[str] = None,
                   estimated_duration: Optional[int] = None,
                   metadata: Dict[str, Any] = None) -> str:
        """Create a new coding task."""
        
        task_id = str(uuid.uuid4())
        task = CodingTask(
            id=task_id,
            task_type=task_type,
            description=description,
            priority=priority,
            dependencies=dependencies or [],
            estimated_duration=estimated_duration,
            metadata=metadata or {}
        )
        
        with self._lock:
            self.tasks[task_id] = task
            self.total_tasks += 1
            
            # Add to priority queue
            self._add_to_priority_queue(task_id)
            
            # Sort queue by priority
            self.task_queue.sort(key=lambda tid: (
                self.tasks[tid].priority.value,
                self.tasks[tid].created_at
            ), reverse=True)
        
        self.logger.info(f"Task created: {task_id} - {description}")
        return task_id
    
    def _add_to_priority_queue(self, task_id: str):
        """Add task ID to priority queue."""
        self.task_queue.append(task_id)
    
    async def get_task(self, task_id: str) -> Optional[CodingTask]:
        """Get task by ID."""
        with self._lock:
            return self.tasks.get(task_id)
    
    async def get_tasks_by_status(self, status: TaskStatus) -> List[CodingTask]:
        """Get tasks by status."""
        with self._lock:
            if status == TaskStatus.RUNNING:
                return list(self.running_tasks.values())
            elif status == TaskStatus.PENDING:
                return [self.tasks[tid] for tid in self.task_queue if tid in self.tasks]
            elif status == TaskStatus.COMPLETED:
                return self.completed_tasks
            else:
                return []
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a task."""
        with self._lock:
            task = self.tasks.get(task_id)
            if not task:
                return False
            
            if task.status == TaskStatus.PENDING:
                task.status = TaskStatus.CANCELLED
                task.completed_at = datetime.now(timezone.utc)
                
                # Remove from queue
                if task_id in self.task_queue:
                    self.task_queue.remove(task_id)
                
                self.completed_tasks.append(task)
                self.logger.info(f"Task cancelled: {task_id}")
                return True
            
            elif task.status == TaskStatus.RUNNING:
                # Note: This doesn't actually stop the running thread,
                # but marks the task as cancelled for tracking
                task.status = TaskStatus.CANCELLED
                task.completed_at = datetime.now(timezone.utc)
                task.error = "Task cancelled by user"
                
                self.running_tasks.pop(task_id, None)
                self.completed_tasks.append(task)
                self.logger.info(f"Task cancelled while running: {task_id}")
                return True
            
            return False
    
    def register_task_callback(self, task_type: str, callback: Callable):
        """Register a callback for specific task type."""
        self.task_callbacks[task_type] = callback
        self.logger.info(f"Registered callback for task type: {task_type}")
    
    def register_progress_callback(self, task_id: str, callback: Callable):
        """Register a progress callback for a specific task."""
        self.progress_callbacks[task_id] = callback
    
    def update_progress(self, task_id: str, progress: float, message: str = ""):
        """Update task progress."""
        with self._lock:
            task = self.tasks.get(task_id)
            if task:
                task.progress = max(0.0, min(1.0, progress))
                if task_id in self.progress_callbacks:
                    self.progress_callbacks[task_id](task.progress, message)
                return True
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get task manager statistics."""
        with self._lock:
            success_rate = (self.completed_count / self.total_tasks * 100) if self.total_tasks > 0 else 0.0
            avg_duration = (self.total_execution_time / self.completed_count) if self.completed_count > 0 else 0.0
            
            return {
                "total_tasks": self.total_tasks,
                "completed_tasks": self.completed_count,
                "failed_tasks": self.failed_count,
                "running_tasks": len(self.running_tasks),
                "pending_tasks": len(self.task_queue),
                "success_rate": success_rate,
                "average_duration": avg_duration,
                "total_execution_time": self.total_execution_time,
                "is_running": self.is_running,
                "max_concurrent_tasks": self.max_concurrent_tasks,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    def get_task_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get task execution history."""
        with self._lock:
            history = []
            for task in self.completed_tasks[-limit:]:
                history.append({
                    "id": task.id,
                    "task_type": task.task_type.value,
                    "description": task.description,
                    "priority": task.priority.value,
                    "status": task.status.value,
                    "created_at": task.created_at.isoformat(),
                    "started_at": task.started_at.isoformat() if task.started_at else None,
                    "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                    "duration": task.actual_duration,
                    "progress": task.progress,
                    "result": task.result,
                    "error": task.error
                })
            return history
    
    def clear_completed_tasks(self, older_than_days: int = 7):
        """Clear completed tasks older than specified days."""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=older_than_days)
        
        with self._lock:
            # Remove from completed tasks
            self.completed_tasks = [
                task for task in self.completed_tasks 
                if task.completed_at and task.completed_at > cutoff_date
            ]
            
            # Remove from tasks dictionary
            tasks_to_remove = [
                task.id for task in self.completed_tasks 
                if task.completed_at and task.completed_at <= cutoff_date
            ]
            
            for task_id in tasks_to_remove:
                self.tasks.pop(task_id, None)
            
            self.logger.info(f"Cleared {len(tasks_to_remove)} old completed tasks")
    
    async def cleanup(self):
        """Cleanup resources and memory."""
        await self.stop()
        self.executor.shutdown(wait=True)
        
        # Clear memory
        try:
            await memory_manager.search_memories(
                query="autonomous_coding",
                memory_type="task_result",
                limit=1000
            )
        except Exception as e:
            self.logger.error(f"Failed to cleanup memory: {e}")
        
        self.logger.info("Task Manager cleanup completed")


# Global instance
task_manager = TaskManager()