import asyncio
import psutil
import time
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import threading
from queue import Queue, Empty

class ResourceType(Enum):
    CPU = "cpu"
    MEMORY = "memory"
    DISK = "disk"
    NETWORK = "network"
    GPU = "gpu"

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

@dataclass
class ResourceUsage:
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    network_sent: float
    network_recv: float
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "cpu_percent": self.cpu_percent,
            "memory_percent": self.memory_percent,
            "disk_percent": self.disk_percent,
            "network_sent": self.network_sent,
            "network_recv": self.network_recv,
            "timestamp": self.timestamp.isoformat()
        }

@dataclass
class SystemTask:
    id: str
    name: str
    description: str
    priority: TaskPriority
    required_resources: Dict[ResourceType, float]
    max_duration: Optional[int] = None
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

class ResourceManager:
    """System Resource Manager for AI Operating System"""
    
    def __init__(self, 
                 max_cpu_usage: float = 80.0,
                 max_memory_usage: float = 85.0,
                 max_disk_usage: float = 90.0,
                 monitoring_interval: int = 5):
        self.max_cpu_usage = max_cpu_usage
        self.max_memory_usage = max_memory_usage
        self.max_disk_usage = max_disk_usage
        self.monitoring_interval = monitoring_interval
        
        self.logger = logging.getLogger(__name__)
        self.task_queue = Queue()
        self.running_tasks: Dict[str, SystemTask] = {}
        self.completed_tasks: List[SystemTask] = []
        
        # Resource monitoring
        self.resource_history: List[ResourceUsage] = []
        self.is_monitoring = False
        self.monitoring_thread = None
        
        # Load balancing
        self.task_weights: Dict[str, float] = {}
        self.node_resources: Dict[str, ResourceUsage] = {}
        
        self.logger.info("System Resource Manager initialized")

    def start_monitoring(self):
        """Start resource monitoring thread"""
        if not self.is_monitoring:
            self.is_monitoring = True
            self.monitoring_thread = threading.Thread(target=self._monitor_resources)
            self.monitoring_thread.daemon = True
            self.monitoring_thread.start()
            self.logger.info("Resource monitoring started")

    def stop_monitoring(self):
        """Stop resource monitoring"""
        self.is_monitoring = False
        if self.monitoring_thread:
            self.monitoring_thread.join()
        self.logger.info("Resource monitoring stopped")

    def _monitor_resources(self):
        """Monitor system resources continuously"""
        while self.is_monitoring:
            try:
                # Collect resource usage
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                
                # Network usage
                network = psutil.net_io_counters()
                
                resource_usage = ResourceUsage(
                    cpu_percent=cpu_percent,
                    memory_percent=memory.percent,
                    disk_percent=disk.percent,
                    network_sent=network.bytes_sent,
                    network_recv=network.bytes_recv,
                    timestamp=datetime.now()
                )
                
                # Store history (keep last 1000 entries)
                self.resource_history.append(resource_usage)
                if len(self.resource_history) > 1000:
                    self.resource_history.pop(0)
                
                # Check resource limits
                self._check_resource_limits(resource_usage)
                
            except Exception as e:
                self.logger.error(f"Resource monitoring error: {e}")
            
            time.sleep(self.monitoring_interval)

    def _check_resource_limits(self, usage: ResourceUsage):
        """Check if resource limits are exceeded"""
        alerts = []
        
        if usage.cpu_percent > self.max_cpu_usage:
            alerts.append(f"CPU usage {usage.cpu_percent:.1f}% exceeded limit {self.max_cpu_usage}%")
        
        if usage.memory_percent > self.max_memory_usage:
            alerts.append(f"Memory usage {usage.memory_percent:.1f}% exceeded limit {self.max_memory_usage}%")
        
        if usage.disk_percent > self.max_disk_usage:
            alerts.append(f"Disk usage {usage.disk_percent:.1f}% exceeded limit {self.max_disk_usage}%")
        
        if alerts:
            self.logger.warning(f"Resource limits exceeded: {', '.join(alerts)}")

    def submit_task(self, task: SystemTask) -> str:
        """Submit a task for execution"""
        task_id = task.id
        self.task_queue.put(task)
        self.logger.info(f"Task submitted: {task_id} - {task.name}")
        return task_id

    def get_task_status(self, task_id: str) -> Optional[SystemTask]:
        """Get task status"""
        # Check running tasks
        if task_id in self.running_tasks:
            return self.running_tasks[task_id]
        
        # Check completed tasks
        for task in self.completed_tasks:
            if task.id == task_id:
                return task
        
        return None

    def cancel_task(self, task_id: str) -> bool:
        """Cancel a task"""
        # Check if task is in queue
        # Note: Queue doesn't support direct removal, so we'll mark it as cancelled
        # when it comes up for processing
        
        task = self.get_task_id(task_id)
        if task and task.status == TaskStatus.PENDING:
            task.status = TaskStatus.CANCELLED
            return True
        
        return False

    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status"""
        current_usage = self.resource_history[-1] if self.resource_history else None
        
        return {
            "resource_usage": current_usage.to_dict() if current_usage else None,
            "running_tasks": len(self.running_tasks),
            "pending_tasks": self.task_queue.qsize(),
            "completed_tasks": len(self.completed_tasks),
            "resource_limits": {
                "cpu_max": self.max_cpu_usage,
                "memory_max": self.max_memory_usage,
                "disk_max": self.max_disk_usage
            },
            "timestamp": datetime.now().isoformat()
        }

    def get_resource_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get resource usage history"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        filtered_history = [
            usage.to_dict() for usage in self.resource_history
            if usage.timestamp >= cutoff_time
        ]
        
        return filtered_history

    def can_execute_task(self, task: SystemTask) -> bool:
        """Check if system has enough resources to execute task"""
        if not self.resource_history:
            return True
        
        current_usage = self.resource_history[-1]
        
        # Check if required resources are available
        for resource_type, required_amount in task.required_resources.items():
            available = self._get_available_resource(resource_type, current_usage)
            
            if available < required_amount:
                self.logger.warning(f"Insufficient {resource_type.value} for task {task.id}")
                return False
        
        return True

    def _get_available_resource(self, resource_type: ResourceType, usage: ResourceUsage) -> float:
        """Calculate available resource percentage"""
        if resource_type == ResourceType.CPU:
            return max(0, 100 - usage.cpu_percent)
        elif resource_type == ResourceType.MEMORY:
            return max(0, 100 - usage.memory_percent)
        elif resource_type == ResourceType.DISK:
            return max(0, 100 - usage.disk_percent)
        elif resource_type == ResourceType.NETWORK:
            # Network is not percentage-based, return a high value
            return 100.0
        else:
            return 100.0

    def schedule_tasks(self):
        """Schedule tasks based on priority and resource availability"""
        if self.task_queue.empty():
            return
        
        # Get next task
        try:
            task = self.task_queue.get_nowait()
        except Empty:
            return
        
        # Check if we can execute this task
        if self.can_execute_task(task):
            self.execute_task(task)
        else:
            # Put it back in queue with delay
            self.task_queue.put(task)
            self.logger.info(f"Task {task.id} rescheduled due to insufficient resources")

    def execute_task(self, task: SystemTask):
        """Execute a task"""
        if task.status != TaskStatus.PENDING:
            return
        
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now()
        self.running_tasks[task.id] = task
        
        self.logger.info(f"Executing task: {task.id} - {task.name}")
        
        # Simulate task execution
        try:
            # In a real implementation, this would call the actual task logic
            result = self._simulate_task_execution(task)
            
            task.result = result
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            
            self.logger.info(f"Task completed: {task.id}")
            
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            task.completed_at = datetime.now()
            
            self.logger.error(f"Task failed: {task.id} - {str(e)}")
        
        finally:
            # Move from running to completed
            if task.id in self.running_tasks:
                del self.running_tasks[task.id]
            self.completed_tasks.append(task)

    def _simulate_task_execution(self, task: SystemTask) -> Any:
        """Simulate task execution"""
        # Simulate processing time based on priority
        time.sleep(1 + (5 - task.priority.value) * 0.5)
        
        # Simulate result based on task name
        if "analysis" in task.name.lower():
            return {"analysis_result": "Task analysis completed"}
        elif "processing" in task.name.lower():
            return {"processed_items": 100}
        else:
            return {"status": "completed", "timestamp": datetime.now().isoformat()}

    def optimize_resources(self):
        """Optimize resource allocation"""
        # Analyze resource usage patterns
        if len(self.resource_history) < 10:
            return
        
        # Find peak usage times
        cpu_usage = [usage.cpu_percent for usage in self.resource_history[-100:]]
        avg_cpu = sum(cpu_usage) / len(cpu_usage)
        
        if avg_cpu > 70:
            self.logger.warning(f"High average CPU usage: {avg_cpu:.1f}%")
        
        # Adjust task scheduling based on usage
        if avg_cpu > 80:
            self.logger.info("High CPU usage detected, reducing task priority")

    def cleanup_completed_tasks(self, max_age_hours: int = 24):
        """Clean up old completed tasks"""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        
        self.completed_tasks = [
            task for task in self.completed_tasks
            if task.completed_at and task.completed_at >= cutoff_time
        ]
        
        self.logger.info(f"Cleaned up completed tasks. Remaining: {len(self.completed_tasks)}")

# Global instance
resource_manager = ResourceManager()