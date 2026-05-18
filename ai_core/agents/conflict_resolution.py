"""
Conflict Resolution System - Handle agent task conflicts and resource contention
"""

import asyncio
import time
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import threading
import heapq

from ai_core.agents import (
    AgentStatus, AgentState, Message, MessageType, MessagePriority
)


class ConflictType(Enum):
    """Types of conflicts"""
    RESOURCE_CONTENTION = "resource_contention"
    TASK_DEPENDENCY = "task_dependency"
    PRIORITY_CONFLICT = "priority_conflict"
    CAPABILITY_CONFLICT = "capability_conflict"
    SCHEDULE_CONFLICT = "schedule_conflict"


class ConflictSeverity(Enum):
    """Conflict severity levels"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class Conflict:
    """Conflict data structure"""
    conflict_id: str
    conflict_type: ConflictType
    severity: ConflictSeverity
    description: str
    affected_agents: Set[str]
    affected_tasks: Set[str]
    timestamp: datetime
    resolution_strategy: Optional[str] = None
    resolved: bool = False
    resolution_timestamp: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert conflict to dictionary"""
        return {
            "conflict_id": self.conflict_id,
            "conflict_type": self.conflict_type.value,
            "severity": self.severity.value,
            "description": self.description,
            "affected_agents": list(self.affected_agents),
            "affected_tasks": list(self.affected_tasks),
            "timestamp": self.timestamp.isoformat(),
            "resolution_strategy": self.resolution_strategy,
            "resolved": self.resolved,
            "resolution_timestamp": self.resolution_timestamp.isoformat() if self.resolution_timestamp else None
        }


class ConflictDetector:
    """Detect conflicts in the agent system"""
    
    def __init__(self):
        self.conflict_thresholds = {
            "high_load": 0.8,
            "low_memory": 0.2,
            "cpu_threshold": 0.9,
            "disk_threshold": 0.9,
            "network_threshold": 0.9
        }
    
    def detect_conflicts(self, agent_states: Dict[str, AgentState], 
                        active_tasks: Dict[str, Dict[str, Any]]) -> List[Conflict]:
        """Detect various types of conflicts"""
        conflicts = []
        
        # Resource contention conflicts
        conflicts.extend(self._detect_resource_contention(agent_states))
        
        # Task dependency conflicts
        conflicts.extend(self._detect_task_dependency_conflicts(active_tasks))
        
        # Priority conflicts
        conflicts.extend(self._detect_priority_conflicts(agent_states, active_tasks))
        
        # Capability conflicts
        conflicts.extend(self._detect_capability_conflicts(agent_states))
        
        # Schedule conflicts
        conflicts.extend(self._detect_schedule_conflicts(agent_states, active_tasks))
        
        return sorted(conflicts, key=lambda c: (c.severity.value, c.timestamp.timestamp()), reverse=True)
    
    def _detect_resource_contention(self, agent_states: Dict[str, AgentState]) -> List[Conflict]:
        """Detect resource contention conflicts"""
        conflicts = []
        
        # Group agents by resource usage
        high_load_agents = []
        low_memory_agents = []
        
        for agent_id, state in agent_states.items():
            # High load score
            if state.load_score > self.conflict_thresholds["high_load"]:
                high_load_agents.append(agent_id)
            
            # Low memory
            if state.resource_usage.get("memory", 1.0) < self.conflict_thresholds["low_memory"]:
                low_memory_agents.append(agent_id)
        
        # Create conflicts
        if len(high_load_agents) > 1:
            conflict = Conflict(
                conflict_id=str(uuid.uuid4()),
                conflict_type=ConflictType.RESOURCE_CONTENTION,
                severity=ConflictSeverity.HIGH,
                description=f"Resource contention detected among {len(high_load_agents)} agents with high load scores",
                affected_agents=set(high_load_agents),
                affected_tasks=set(),
                timestamp=datetime.now(timezone.utc),
                resolution_strategy="load_balancing"
            )
            conflicts.append(conflict)
        
        if len(low_memory_agents) > 1:
            conflict = Conflict(
                conflict_id=str(uuid.uuid4()),
                conflict_type=ConflictType.RESOURCE_CONTENTION,
                severity=ConflictSeverity.CRITICAL,
                description=f"Memory contention detected among {len(low_memory_agents)} agents with low memory",
                affected_agents=set(low_memory_agents),
                affected_tasks=set(),
                timestamp=datetime.now(timezone.utc),
                resolution_strategy="memory_optimization"
            )
            conflicts.append(conflict)
        
        return conflicts
    
    def _detect_task_dependency_conflicts(self, active_tasks: Dict[str, Dict[str, Any]]) -> List[Conflict]:
        """Detect task dependency conflicts"""
        conflicts = []
        
        # Build dependency graph
        dependency_graph = {}
        task_to_agents = {}
        
        for task_id, task_info in active_tasks.items():
            task_deps = task_info.get("dependencies", [])
            dependency_graph[task_id] = set(task_deps)
            
            assigned_agent = task_info.get("assigned_agent")
            if assigned_agent:
                task_to_agents[task_id] = assigned_agent
        
        # Detect cycles
        visited = set()
        rec_stack = set()
        
        def has_cycle(node):
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in dependency_graph.get(node, []):
                if neighbor not in visited:
                    if has_cycle(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True
            
            rec_stack.remove(node)
            return False
        
        for task_id in dependency_graph:
            if task_id not in visited:
                if has_cycle(task_id):
                    conflict = Conflict(
                        conflict_id=str(uuid.uuid4()),
                        conflict_type=ConflictType.TASK_DEPENDENCY,
                        severity=ConflictSeverity.CRITICAL,
                        description=f"Circular dependency detected among tasks",
                        affected_agents=set(task_to_agents.values()),
                        affected_tasks=set(dependency_graph.keys()),
                        timestamp=datetime.now(timezone.utc),
                        resolution_strategy="dependency_resolution"
                    )
                    conflicts.append(conflict)
                    break
        
        return conflicts
    
    def _detect_priority_conflicts(self, agent_states: Dict[str, AgentState], 
                                 active_tasks: Dict[str, Dict[str, Any]]) -> List[Conflict]:
        """Detect priority conflicts"""
        conflicts = []
        
        # Group tasks by priority and agent
        agent_priority_groups = {}
        
        for task_id, task_info in active_tasks.items():
            assigned_agent = task_info.get("assigned_agent")
            if assigned_agent:
                priority = task_info.get("priority", 2)  # Default to NORMAL
                
                if assigned_agent not in agent_priority_groups:
                    agent_priority_groups[assigned_agent] = {}
                
                if priority not in agent_priority_groups[assigned_agent]:
                    agent_priority_groups[assigned_agent][priority] = []
                
                agent_priority_groups[assigned_agent][priority].append(task_id)
        
        # Detect agents with multiple high-priority tasks
        for agent_id, priority_tasks in agent_priority_groups.items():
            high_priority_count = len(priority_tasks.get(4, []))  # CRITICAL priority
            if high_priority_count > 1:
                conflict = Conflict(
                    conflict_id=str(uuid.uuid4()),
                    conflict_type=ConflictType.PRIORITY_CONFLICT,
                    severity=ConflictSeverity.HIGH,
                    description=f"Agent {agent_id} has {high_priority_count} high-priority tasks",
                    affected_agents={agent_id},
                    affected_tasks=set(priority_tasks.get(4, [])),
                    timestamp=datetime.now(timezone.utc),
                    resolution_strategy="priority_rebalancing"
                )
                conflicts.append(conflict)
        
        return conflicts
    
    def _detect_capability_conflicts(self, agent_states: Dict[str, AgentState]) -> List[Conflict]:
        """Detect capability conflicts"""
        conflicts = []
        
        # Check for over-specialized agents
        capability_counts = {}
        for agent_id, state in agent_states.items():
            for capability in state.capabilities:
                capability_counts[capability] = capability_counts.get(capability, 0) + 1
        
        # Detect capability bottlenecks
        for capability, count in capability_counts.items():
            if count == 1:  # Only one agent has this capability
                # Find the agent with this capability
                bottleneck_agents = [
                    agent_id for agent_id, state in agent_states.items()
                    if capability in state.capabilities and state.status != AgentStatus.IDLE
                ]
                
                if bottleneck_agents:
                    conflict = Conflict(
                        conflict_id=str(uuid.uuid4()),
                        conflict_type=ConflictType.CAPABILITY_CONFLICT,
                        severity=ConflictSeverity.MEDIUM,
                        description=f"Capability bottleneck detected: only {count} agent(s) have capability '{capability}'",
                        affected_agents=set(bottleneck_agents),
                        affected_tasks=set(),
                        timestamp=datetime.now(timezone.utc),
                        resolution_strategy="capability_sharing"
                    )
                    conflicts.append(conflict)
        
        return conflicts
    
    def _detect_schedule_conflicts(self, agent_states: Dict[str, AgentState], 
                                 active_tasks: Dict[str, Dict[str, Any]]) -> List[Conflict]:
        """Detect schedule conflicts"""
        conflicts = []
        
        # Check for agents with too many tasks
        overloaded_agents = {}
        
        for task_id, task_info in active_tasks.items():
            assigned_agent = task_info.get("assigned_agent")
            if assigned_agent:
                if assigned_agent not in overloaded_agents:
                    overloaded_agents[assigned_agent] = 0
                overloaded_agents[assigned_agent] += 1
        
        # Detect overloaded agents
        for agent_id, task_count in overloaded_agents.items():
            if task_count > 3:  # More than 3 tasks is overloaded
                conflict = Conflict(
                    conflict_id=str(uuid.uuid4()),
                    conflict_type=ConflictType.SCHEDULE_CONFLICT,
                    severity=ConflictSeverity.MEDIUM,
                    description=f"Agent {agent_id} is overloaded with {task_count} tasks",
                    affected_agents={agent_id},
                    affected_tasks=[task_id for task_id, task_info in active_tasks.items() 
                                  if task_info.get("assigned_agent") == agent_id],
                    timestamp=datetime.now(timezone.utc),
                    resolution_strategy="task_rebalancing"
                )
                conflicts.append(conflict)
        
        return conflicts


class ConflictResolver:
    """Resolve conflicts detected in the system"""
    
    def __init__(self):
        self.resolution_strategies = {
            "load_balancing": self._resolve_load_balancing,
            "memory_optimization": self._resolve_memory_optimization,
            "dependency_resolution": self._resolve_dependency_conflicts,
            "priority_rebalancing": self._resolve_priority_conflicts,
            "capability_sharing": self._resolve_capability_conflicts,
            "task_rebalancing": self._resolve_schedule_conflicts
        }
    
    def resolve_conflict(self, conflict: Conflict, agent_states: Dict[str, AgentState],
                        active_tasks: Dict[str, Dict[str, Any]]) -> bool:
        """Resolve a conflict using appropriate strategy"""
        if conflict.resolved:
            return True
        
        if conflict.resolution_strategy not in self.resolution_strategies:
            print(f"[ConflictResolver] No resolution strategy for: {conflict.resolution_strategy}")
            return False
        
        try:
            resolver_func = self.resolution_strategies[conflict.resolution_strategy]
            success = resolver_func(conflict, agent_states, active_tasks)
            
            if success:
                conflict.resolved = True
                conflict.resolution_timestamp = datetime.now(timezone.utc)
                print(f"[ConflictResolver] Resolved conflict: {conflict.conflict_id}")
            else:
                print(f"[ConflictResolver] Failed to resolve conflict: {conflict.conflict_id}")
            
            return success
        
        except Exception as e:
            print(f"[ConflictResolver] Error resolving conflict {conflict.conflict_id}: {e}")
            return False
    
    def _resolve_load_balancing(self, conflict: Conflict, agent_states: Dict[str, AgentState],
                              active_tasks: Dict[str, Dict[str, Any]]) -> bool:
        """Resolve load balancing conflicts"""
        # Reassign tasks from overloaded agents to less loaded ones
        overloaded_agents = list(conflict.affected_agents)
        
        if len(overloaded_agents) < 2:
            return False
        
        # Find less loaded agents
        available_agents = []
        for agent_id, state in agent_states.items():
            if (agent_id not in overloaded_agents and 
                state.status == AgentStatus.IDLE and 
                state.load_score < 0.5):
                available_agents.append((agent_id, state.load_score))
        
        if not available_agents:
            return False
        
        # Sort by load score (ascending)
        available_agents.sort(key=lambda x: x[1])
        
        # Reassign tasks
        success_count = 0
        for overloaded_agent in overloaded_agents:
            overloaded_tasks = [
                task_id for task_id, task_info in active_tasks.items()
                if task_info.get("assigned_agent") == overloaded_agent
            ]
            
            for task_id in overloaded_tasks:
                # Find available agent
                if available_agents:
                    target_agent, _ = available_agents.pop(0)
                    
                    # Reassign task
                    active_tasks[task_id]["assigned_agent"] = target_agent
                    success_count += 1
                    
                    print(f"[ConflictResolver] Reassigned task {task_id} from {overloaded_agent} to {target_agent}")
        
        return success_count > 0
    
    def _resolve_memory_optimization(self, conflict: Conflict, agent_states: Dict[str, AgentState],
                                  active_tasks: Dict[str, Dict[str, Any]]) -> bool:
        """Resolve memory optimization conflicts"""
        # Clear caches and optimize memory usage
        for agent_id in conflict.affected_agents:
            print(f"[ConflictResolver] Optimizing memory for agent: {agent_id}")
            # In real implementation, this would trigger memory optimization
        
        return True
    
    def _resolve_dependency_conflicts(self, conflict: Conflict, agent_states: Dict[str, AgentState],
                                    active_tasks: Dict[str, Dict[str, Any]]) -> bool:
        """Resolve dependency conflicts"""
        # Break circular dependencies by reordering tasks
        print(f"[ConflictResolver] Breaking circular dependencies")
        
        # In real implementation, this would use topological sorting
        return True
    
    def _resolve_priority_conflicts(self, conflict: Conflict, agent_states: Dict[str, AgentState],
                                  active_tasks: Dict[str, Dict[str, Any]]) -> bool:
        """Resolve priority conflicts"""
        # Rebalance high-priority tasks
        for task_id in conflict.affected_tasks:
            task_info = active_tasks.get(task_id)
            if task_info and task_info.get("priority") == 4:  # CRITICAL
                # Find alternative agent
                target_agents = [
                    agent_id for agent_id, state in agent_states.items()
                    if (state.status == AgentStatus.IDLE and 
                        agent_id != task_info.get("assigned_agent"))
                ]
                
                if target_agents:
                    target_agent = target_agents[0]
                    task_info["assigned_agent"] = target_agent
                    print(f"[ConflictResolver] Rebalanced high-priority task {task_id} to {target_agent}")
        
        return True
    
    def _resolve_capability_conflicts(self, conflict: Conflict, agent_states: Dict[str, AgentState],
                                    active_tasks: Dict[str, Dict[str, Any]]) -> bool:
        """Resolve capability conflicts"""
        # Implement capability sharing or training
        print(f"[ConflictResolver] Implementing capability sharing")
        
        # In real implementation, this would trigger capability sharing or training
        return True
    
    def _resolve_schedule_conflicts(self, conflict: Conflict, agent_states: Dict[str, AgentState],
                                  active_tasks: Dict[str, Dict[str, Any]]) -> bool:
        """Resolve schedule conflicts"""
        # Rebalance tasks to reduce overload
        overloaded_agent = list(conflict.affected_agents)[0]
        
        # Get tasks for overloaded agent
        overloaded_tasks = [
            task_id for task_id, task_info in active_tasks.items()
            if task_info.get("assigned_agent") == overloaded_agent
        ]
        
        # Find idle agents
        idle_agents = [
            agent_id for agent_id, state in agent_states.items()
            if state.status == AgentStatus.IDLE
        ]
        
        if not idle_agents:
            return False
        
        # Reassign some tasks
        reassign_count = min(len(overloaded_tasks) // 2, len(idle_agents))
        success_count = 0
        
        for i in range(reassign_count):
            task_id = overloaded_tasks[i]
            target_agent = idle_agents[i]
            
            active_tasks[task_id]["assigned_agent"] = target_agent
            success_count += 1
            
            print(f"[ConflictResolver] Reassigned task {task_id} to {target_agent}")
        
        return success_count > 0


class ConflictManager:
    """Main conflict management system"""
    
    def __init__(self):
        self.detector = ConflictDetector()
        self.resolver = ConflictResolver()
        self.conflicts: Dict[str, Conflict] = {}
        self.conflict_history: List[Conflict] = []
        self.max_history = 1000
        
        # Conflict management settings
        self.detection_interval = 30.0  # seconds
        self.auto_resolve_threshold = ConflictSeverity.MEDIUM  # Auto-resolve medium and above
        
        # Background threads
        self.is_running = False
        self.detection_thread = None
        self.resolution_thread = None
    
    def start(self):
        """Start conflict management system"""
        if not self.is_running:
            self.is_running = True
            self.detection_thread = threading.Thread(target=self._detection_loop)
            self.resolution_thread = threading.Thread(target=self._resolution_loop)
            
            self.detection_thread.daemon = True
            self.resolution_thread.daemon = True
            
            self.detection_thread.start()
            self.resolution_thread.start()
            
            print("[ConflictManager] Started conflict management system")
    
    def stop(self):
        """Stop conflict management system"""
        self.is_running = False
        if self.detection_thread:
            self.detection_thread.join(timeout=5)
        if self.resolution_thread:
            self.resolution_thread.join(timeout=5)
        print("[ConflictManager] Stopped conflict management system")
    
    def _detection_loop(self):
        """Background conflict detection loop"""
        while self.is_running:
            try:
                time.sleep(self.detection_interval)
                # Detection logic would be called here
            except Exception as e:
                print(f"[ConflictManager] Error in detection loop: {e}")
                time.sleep(1)
    
    def _resolution_loop(self):
        """Background conflict resolution loop"""
        while self.is_running:
            try:
                time.sleep(10.0)  # Check every 10 seconds
                self._auto_resolve_conflicts()
            except Exception as e:
                print(f"[ConflictManager] Error in resolution loop: {e}")
                time.sleep(1)
    
    def detect_conflicts(self, agent_states: Dict[str, AgentState], 
                        active_tasks: Dict[str, Dict[str, Any]]) -> List[Conflict]:
        """Detect conflicts and update internal state"""
        detected_conflicts = self.detector.detect_conflicts(agent_states, active_tasks)
        
        for conflict in detected_conflicts:
            if conflict.conflict_id not in self.conflicts:
                self.conflicts[conflict.conflict_id] = conflict
                self.conflict_history.append(conflict)
                
                # Limit history size
                if len(self.conflict_history) > self.max_history:
                    self.conflict_history.pop(0)
                
                print(f"[ConflictManager] New conflict detected: {conflict.conflict_id} - {conflict.description}")
        
        return detected_conflicts
    
    def resolve_conflict(self, conflict_id: str) -> bool:
        """Manually resolve a specific conflict"""
        conflict = self.conflicts.get(conflict_id)
        if not conflict:
            return False
        
        # In real implementation, we would get current agent states and tasks
        return self.resolver.resolve_conflict(conflict, {}, {})
    
    def _auto_resolve_conflicts(self):
        """Auto-resolve conflicts that meet the threshold"""
        for conflict_id, conflict in list(self.conflicts.items()):
            if (not conflict.resolved and 
                conflict.severity.value >= self.auto_resolve_threshold.value):
                
                self.resolve_conflict(conflict_id)
    
    def get_conflicts(self, resolved: Optional[bool] = None) -> Dict[str, Conflict]:
        """Get conflicts, optionally filtered by resolution status"""
        if resolved is None:
            return self.conflicts.copy()
        
        return {cid: conflict for cid, conflict in self.conflicts.items() 
                if conflict.resolved == resolved}
    
    def get_conflict_history(self, limit: int = 100) -> List[Conflict]:
        """Get conflict history"""
        return self.conflict_history[-limit:]
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get conflict management metrics"""
        total_conflicts = len(self.conflicts)
        resolved_conflicts = len([c for c in self.conflicts.values() if c.resolved])
        active_conflicts = total_conflicts - resolved_conflicts
        
        conflict_types = {}
        for conflict in self.conflicts.values():
            conflict_type = conflict.conflict_type.value
            conflict_types[conflict_type] = conflict_types.get(conflict_type, 0) + 1
        
        severity_counts = {}
        for conflict in self.conflicts.values():
            severity = conflict.severity.value
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        return {
            "total_conflicts": total_conflicts,
            "resolved_conflicts": resolved_conflicts,
            "active_conflicts": active_conflicts,
            "resolution_rate": resolved_conflicts / total_conflicts if total_conflicts > 0 else 0.0,
            "conflict_types": conflict_types,
            "severity_distribution": severity_counts,
            "detection_interval": self.detection_interval,
            "auto_resolve_threshold": self.auto_resolve_threshold.name
        }