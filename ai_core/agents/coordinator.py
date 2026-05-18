"""
Cross-Agent Coordinator - Advanced coordination system for inter-agent task delegation
"""

import asyncio
import time
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import threading

from ai_core.agents import (
    Message, MessageType, MessagePriority, AgentStatus,
    AgentState, CommunicationManager, TaskCoordinator
)


class TaskPriority(Enum):
    """Task priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


class TaskStatus(Enum):
    """Task status states"""
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Task:
    """Task data structure"""
    task_id: str
    task_type: str
    priority: TaskPriority
    required_capabilities: List[str]
    task_data: Dict[str, Any]
    created_at: datetime
    deadline: Optional[datetime] = None
    assigned_agent: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING
    progress: float = 0.0
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    dependencies: List[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.metadata is None:
            self.metadata = {}


@dataclass
class AgentCapabilityScore:
    """Agent capability score for matching"""
    agent_id: str
    capability_match_score: float
    load_score: float
    availability_score: float
    total_score: float


class TaskDependencyManager:
    """Manages task dependencies and execution order"""
    
    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self.dependency_graph: Dict[str, Set[str]] = {}
    
    def add_task(self, task: Task):
        """Add a task to the dependency graph"""
        self.tasks[task.task_id] = task
        
        # Build dependency graph
        if task.dependencies:
            self.dependency_graph[task.task_id] = set(task.dependencies)
        else:
            self.dependency_graph[task.task_id] = set()
    
    def get_ready_tasks(self) -> List[Task]:
        """Get tasks that are ready to execute (dependencies met)"""
        ready_tasks = []
        
        for task in self.tasks.values():
            if (task.status == TaskStatus.PENDING and 
                not task.dependencies and 
                self._are_dependencies_met(task.task_id)):
                ready_tasks.append(task)
            elif (task.status == TaskStatus.PENDING and 
                  self._are_dependencies_met(task.task_id)):
                ready_tasks.append(task)
        
        # Sort by priority and creation time
        ready_tasks.sort(key=lambda t: (t.priority.value, t.created_at.timestamp()), reverse=True)
        
        return ready_tasks
    
    def _are_dependencies_met(self, task_id: str) -> bool:
        """Check if all dependencies for a task are met"""
        if task_id not in self.dependency_graph:
            return True
        
        dependencies = self.dependency_graph[task_id]
        for dep_id in dependencies:
            dep_task = self.tasks.get(dep_id)
            if not dep_task or dep_task.status != TaskStatus.COMPLETED:
                return False
        
        return True
    
    def mark_task_completed(self, task_id: str):
        """Mark a task as completed and update dependents"""
        if task_id in self.tasks:
            self.tasks[task_id].status = TaskStatus.COMPLETED
            
            # Update tasks that depend on this one
            for t_id, deps in self.dependency_graph.items():
                if task_id in deps:
                    # Mark dependency as satisfied
                    if hasattr(self, 'completed_dependencies'):
                        self.completed_dependencies.setdefault(t_id, set()).add(task_id)
    
    def get_task_chain(self, task_id: str) -> List[str]:
        """Get the chain of dependencies for a task"""
        chain = []
        visited = set()
        
        def _build_chain(current_id: str):
            if current_id in visited:
                return
            visited.add(current_id)
            
            if current_id in self.dependency_graph:
                for dep_id in self.dependency_graph[current_id]:
                    _build_chain(dep_id)
            
            chain.append(current_id)
        
        _build_chain(task_id)
        return chain


class AgentMatcher:
    """Matches tasks to best available agents"""
    
    def __init__(self, communication_manager: CommunicationManager):
        self.communication_manager = communication_manager
        self.capability_weights = {
            "coding": 1.0,
            "trading": 1.0,
            "monitoring": 1.0,
            "research": 1.0,
            "coordination": 1.0,
            "data_analysis": 1.2,
            "system_admin": 0.8
        }
    
    def find_best_agent(self, task: Task) -> Optional[AgentCapabilityScore]:
        """Find the best agent for a task"""
        available_agents = self._get_available_agents(task)
        
        if not available_agents:
            return None
        
        scores = []
        for agent in available_agents:
            score = self._calculate_agent_score(agent, task)
            scores.append(score)
        
        # Return the best agent
        return max(scores, key=lambda x: x.total_score)
    
    def _get_available_agents(self, task: Task) -> List[AgentState]:
        """Get available agents that can handle the task"""
        available_agents = []
        
        for agent_state in self.communication_manager.agent_registry.agents.values():
            if (agent_state.status == AgentStatus.IDLE and
                self._can_handle_task(agent_state, task)):
                available_agents.append(agent_state)
        
        return available_agents
    
    def _can_handle_task(self, agent: AgentState, task: Task) -> bool:
        """Check if agent can handle the task"""
        required_caps = set(task.required_capabilities)
        agent_caps = set(agent.capabilities)
        
        # Check if agent has at least one required capability
        return len(required_caps & agent_caps) > 0
    
    def _calculate_agent_score(self, agent: AgentState, task: Task) -> AgentCapabilityScore:
        """Calculate score for an agent based on multiple factors"""
        # Capability match score
        capability_match_score = self._calculate_capability_match(agent, task)
        
        # Load score (inverse - lower load is better)
        availability_score = 1.0 - agent.load_score
        
        # Priority bonus
        priority_bonus = task.priority.value / TaskPriority.CRITICAL.value
        
        # Experience bonus (if we had historical data)
        experience_bonus = 0.0
        
        # Calculate total score
        total_score = (
            capability_match_score * 0.4 +
            availability_score * 0.3 +
            priority_bonus * 0.2 +
            experience_bonus * 0.1
        )
        
        return AgentCapabilityScore(
            agent_id=agent.agent_id,
            capability_match_score=capability_match_score,
            load_score=agent.load_score,
            availability_score=availability_score,
            total_score=total_score
        )
    
    def _calculate_capability_match(self, agent: AgentState, task: Task) -> float:
        """Calculate capability match score"""
        required_caps = set(task.required_capabilities)
        agent_caps = set(agent.capabilities)
        
        if not required_caps:
            return 1.0
        
        # Calculate weighted match
        total_weight = 0.0
        matched_weight = 0.0
        
        for cap in required_caps:
            weight = self.capability_weights.get(cap, 1.0)
            total_weight += weight
            
            if cap in agent_caps:
                matched_weight += weight
        
        return matched_weight / total_weight if total_weight > 0 else 0.0


class TaskScheduler:
    """Advanced task scheduler with priority and deadline management"""
    
    def __init__(self):
        self.task_queue: List[Task] = []
        self.deadline_queue: Dict[datetime, List[Task]] = {}
        self.scheduled_tasks: Dict[str, Task] = {}
    
    def add_task(self, task: Task):
        """Add task to scheduler"""
        self.scheduled_tasks[task.task_id] = task
        
        # Add to priority queue
        self.task_queue.append(task)
        self.task_queue.sort(key=lambda t: (t.priority.value, t.created_at.timestamp()), reverse=True)
        
        # Add to deadline queue if deadline exists
        if task.deadline:
            if task.deadline not in self.deadline_queue:
                self.deadline_queue[task.deadline] = []
            self.deadline_queue[task.deadline].append(task)
    
    def get_next_task(self, current_time: datetime = None) -> Optional[Task]:
        """Get the next task to execute"""
        if current_time is None:
            current_time = datetime.now(timezone.utc)
        
        # Check for overdue tasks first
        overdue_tasks = self._get_overdue_tasks(current_time)
        if overdue_tasks:
            return overdue_tasks[0]
        
        # Get highest priority task
        for task in self.task_queue:
            if task.status == TaskStatus.PENDING:
                return task
        
        return None
    
    def _get_overdue_tasks(self, current_time: datetime) -> List[Task]:
        """Get tasks that are overdue"""
        overdue = []
        
        for deadline, tasks in self.deadline_queue.items():
            if deadline < current_time:
                for task in tasks:
                    if task.status == TaskStatus.PENDING:
                        task.priority = TaskPriority.CRITICAL  # Boost priority
                        overdue.append(task)
        
        return overdue


class CrossAgentCoordinator:
    """Main cross-agent coordination system"""
    
    def __init__(self, communication_manager: CommunicationManager):
        self.communication_manager = communication_manager
        self.dependency_manager = TaskDependencyManager()
        self.agent_matcher = AgentMatcher(communication_manager)
        self.task_scheduler = TaskScheduler()
        
        # Coordination state
        self.is_running = False
        self.coordination_thread = None
        self.scheduling_interval = 5.0  # seconds
        
        # Task tracking
        self.active_tasks: Dict[str, Task] = {}
        self.completed_tasks: Dict[str, Task] = {}
        self.failed_tasks: Dict[str, Task] = {}
        
        # Performance metrics
        self.total_tasks_processed = 0
        self.successful_tasks = 0
        self.failed_task_count = 0
        self.average_processing_time = 0.0
    
    def start(self):
        """Start the coordination system"""
        if not self.is_running:
            self.is_running = True
            self.coordination_thread = threading.Thread(target=self._coordination_loop)
            self.coordination_thread.daemon = True
            self.coordination_thread.start()
            print("[CrossAgentCoordinator] Started coordination system")
    
    def stop(self):
        """Stop the coordination system"""
        self.is_running = False
        if self.coordination_thread:
            self.coordination_thread.join(timeout=5)
        print("[CrossAgentCoordinator] Stopped coordination system")
    
    def _coordination_loop(self):
        """Main coordination loop"""
        while self.is_running:
            try:
                # Schedule tasks
                self._schedule_tasks()
                
                # Monitor active tasks
                self._monitor_active_tasks()
                
                # Handle task conflicts
                self._handle_task_conflicts()
                
                time.sleep(self.scheduling_interval)
            except Exception as e:
                print(f"[CrossAgentCoordinator] Error in coordination loop: {e}")
                time.sleep(1)
    
    def _schedule_tasks(self):
        """Schedule tasks to appropriate agents"""
        ready_tasks = self.dependency_manager.get_ready_tasks()
        
        for task in ready_tasks:
            if task.status == TaskStatus.PENDING:
                best_agent = self.agent_matcher.find_best_agent(task)
                
                if best_agent:
                    self._assign_task_to_agent(task, best_agent)
                else:
                    print(f"[CrossAgentCoordinator] No available agent for task: {task.task_id}")
    
    def _assign_task_to_agent(self, task: Task, agent_score: AgentCapabilityScore):
        """Assign task to agent"""
        task.assigned_agent = agent_score.agent_id
        task.status = TaskStatus.ASSIGNED
        
        # Send task to agent
        success = self.communication_manager.send_task_request(
            source_agent="coordinator",
            target_agent=agent_score.agent_id,
            task_id=task.task_id,
            task_data=task.task_data,
            priority=MessagePriority(task.priority.value)
        )
        
        if success:
            self.active_tasks[task.task_id] = task
            print(f"[CrossAgentCoordinator] Task {task.task_id} assigned to {agent_score.agent_id}")
        else:
            task.status = TaskStatus.PENDING
            task.assigned_agent = None
            print(f"[CrossAgentCoordinator] Failed to assign task {task.task_id}")
    
    def _monitor_active_tasks(self):
        """Monitor active tasks for completion"""
        completed_task_ids = []
        
        for task_id, task in self.active_tasks.items():
            if task.status == TaskStatus.COMPLETED:
                completed_task_ids.append(task_id)
                self.completed_tasks[task_id] = task
                self.dependency_manager.mark_task_completed(task_id)
                self.successful_tasks += 1
            elif task.status == TaskStatus.FAILED:
                completed_task_ids.append(task_id)
                self.failed_tasks[task_id] = task
                self.failed_task_count += 1
                
                # Handle retries
                if task.retry_count < task.max_retries:
                    task.retry_count += 1
                    task.status = TaskStatus.PENDING
                    task.assigned_agent = None
                    print(f"[CrossAgentCoordinator] Retrying task {task.task_id} (attempt {task.retry_count})")
                else:
                    print(f"[CrossAgentCoordinator] Task {task.task_id} failed permanently")
        
        # Remove completed tasks from active
        for task_id in completed_task_ids:
            del self.active_tasks[task_id]
        
        # Update metrics
        self.total_tasks_processed += len(completed_task_ids)
        if self.total_tasks_processed > 0:
            self.average_processing_time = (
                (self.average_processing_time * (self.total_tasks_processed - len(completed_task_ids)) + 
                 len(completed_task_ids)) / self.total_tasks_processed
            )
    
    def _handle_task_conflicts(self):
        """Handle task conflicts and resource contention"""
        # Check for conflicts in task assignments
        agent_assignments = {}
        
        for task in self.active_tasks.values():
            if task.assigned_agent:
                if task.assigned_agent not in agent_assignments:
                    agent_assignments[task.assigned_agent] = []
                agent_assignments[task.assigned_agent].append(task)
        
        # Resolve conflicts
        for agent_id, tasks in agent_assignments.items():
            if len(tasks) > 1:
                print(f"[CrossAgentCoordinator] Conflict detected: Agent {agent_id} has {len(tasks)} tasks")
                # Re-prioritize tasks
                tasks.sort(key=lambda t: t.priority.value, reverse=True)
                for i, task in enumerate(tasks[1:], 1):  # Keep highest priority, re-assign others
                    self._reassign_conflicted_task(task)
    
    def _reassign_conflicted_task(self, task: Task):
        """Reassign a conflicted task"""
        task.assigned_agent = None
        task.status = TaskStatus.PENDING
        
        # Try to find alternative agent
        best_agent = self.agent_matcher.find_best_agent(task)
        if best_agent:
            self._assign_task_to_agent(task, best_agent)
        else:
            print(f"[CrossAgentCoordinator] No alternative agent available for conflicted task {task.task_id}")
    
    def submit_task(self, task_type: str, required_capabilities: List[str], 
                   task_data: Dict[str, Any], priority: TaskPriority = TaskPriority.NORMAL,
                   deadline: Optional[datetime] = None, dependencies: List[str] = None) -> str:
        """Submit a task for coordination"""
        task_id = str(uuid.uuid4())
        
        task = Task(
            task_id=task_id,
            task_type=task_type,
            priority=priority,
            required_capabilities=required_capabilities,
            task_data=task_data,
            created_at=datetime.now(timezone.utc),
            deadline=deadline,
            dependencies=dependencies or []
        )
        
        # Add to dependency manager
        self.dependency_manager.add_task(task)
        
        # Add to scheduler
        self.task_scheduler.add_task(task)
        
        print(f"[CrossAgentCoordinator] Task submitted: {task_id}")
        return task_id
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task status"""
        # Check active tasks
        if task_id in self.active_tasks:
            task = self.active_tasks[task_id]
            return {
                "task_id": task.task_id,
                "status": task.status.value,
                "assigned_agent": task.assigned_agent,
                "priority": task.priority.name,
                "progress": task.progress,
                "created_at": task.created_at.isoformat(),
                "deadline": task.deadline.isoformat() if task.deadline else None,
                "retry_count": task.retry_count
            }
        
        # Check completed tasks
        if task_id in self.completed_tasks:
            task = self.completed_tasks[task_id]
            return {
                "task_id": task.task_id,
                "status": task.status.value,
                "assigned_agent": task.assigned_agent,
                "priority": task.priority.name,
                "progress": task.progress,
                "created_at": task.created_at.isoformat(),
                "deadline": task.deadline.isoformat() if task.deadline else None,
                "result": task.result,
                "completed_at": datetime.now(timezone.utc).isoformat()
            }
        
        # Check failed tasks
        if task_id in self.failed_tasks:
            task = self.failed_tasks[task_id]
            return {
                "task_id": task.task_id,
                "status": task.status.value,
                "assigned_agent": task.assigned_agent,
                "priority": task.priority.name,
                "progress": task.progress,
                "created_at": task.created_at.isoformat(),
                "deadline": task.deadline.isoformat() if task.deadline else None,
                "error": task.error_message,
                "failed_at": datetime.now(timezone.utc).isoformat()
            }
        
        return None
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get coordination system metrics"""
        return {
            "total_tasks_submitted": len(self.dependency_manager.tasks),
            "active_tasks": len(self.active_tasks),
            "completed_tasks": len(self.completed_tasks),
            "failed_tasks": len(self.failed_tasks),
            "total_tasks_processed": self.total_tasks_processed,
            "successful_tasks": self.successful_tasks,
            "failed_task_count": self.failed_task_count,
            "success_rate": self.successful_tasks / self.total_tasks_processed if self.total_tasks_processed > 0 else 0.0,
            "average_processing_time": self.average_processing_time,
            "pending_tasks": len([t for t in self.dependency_manager.tasks.values() if t.status == TaskStatus.PENDING]),
            "agents_available": len([a for a in self.communication_manager.agent_registry.agents.values() if a.status == AgentStatus.IDLE])
        }