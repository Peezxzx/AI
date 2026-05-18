"""
Agent State Manager - Synchronized agent state management across the system
"""

import asyncio
import json
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Set, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import threading
import redis
import pickle

from ai_core.agents import (
    AgentStatus, AgentState, Message, MessageType
)


class AgentEventType(Enum):
    """Agent event types"""
    STATUS_CHANGE = "status_change"
    TASK_ASSIGNMENT = "task_assignment"
    TASK_COMPLETION = "task_completion"
    HEARTBEAT = "heartbeat"
    ERROR = "error"
    REGISTRATION = "registration"
    DEREGISTRATION = "deregistration"
    STATE_SYNC = "state_sync"


@dataclass
class AgentEvent:
    """Agent event data structure"""
    event_id: str
    event_type: AgentEventType
    agent_id: str
    timestamp: datetime
    data: Dict[str, Any]
    previous_state: Optional[AgentState] = None
    current_state: Optional[AgentState] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary"""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "agent_id": self.agent_id,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data,
            "previous_state": asdict(self.previous_state) if self.previous_state else None,
            "current_state": asdict(self.current_state) if self.current_state else None
        }


class AgentStateMachine:
    """State machine for agent lifecycle"""
    
    def __init__(self):
        self.states = {
            AgentStatus.IDLE: {
                "transitions": {
                    AgentStatus.WORKING: "start_work",
                    AgentStatus.COORDINATING: "start_coordination",
                    AgentStatus.OFFLINE: "go_offline"
                },
                "can_receive_tasks": True,
                "can_coordinate": True
            },
            AgentStatus.WORKING: {
                "transitions": {
                    AgentStatus.IDLE: "finish_work",
                    AgentStatus.COORDINATING: "start_coordination",
                    AgentStatus.ERROR: "encounter_error",
                    AgentStatus.OFFLINE: "go_offline"
                },
                "can_receive_tasks": False,
                "can_coordinate": True
            },
            AgentStatus.COORDINATING: {
                "transitions": {
                    AgentStatus.IDLE: "finish_coordination",
                    AgentStatus.WORKING: "start_work",
                    AgentStatus.ERROR: "encounter_error",
                    AgentStatus.OFFLINE: "go_offline"
                },
                "can_receive_tasks": False,
                "can_coordinate": True
            },
            AgentStatus.ERROR: {
                "transitions": {
                    AgentStatus.IDLE: "recover",
                    AgentStatus.OFFLINE: "go_offline"
                },
                "can_receive_tasks": False,
                "can_coordinate": False
            },
            AgentStatus.OFFLINE: {
                "transitions": {
                    AgentStatus.IDLE: "come_online"
                },
                "can_receive_tasks": False,
                "can_coordinate": False
            }
        }
    
    def can_transition(self, current_status: AgentStatus, new_status: AgentStatus) -> bool:
        """Check if state transition is valid"""
        current_state = self.states.get(current_status)
        if not current_state:
            return False
        
        return new_status in current_state["transitions"]
    
    def get_transition_action(self, current_status: AgentStatus, new_status: AgentStatus) -> Optional[str]:
        """Get action for state transition"""
        current_state = self.states.get(current_status)
        if not current_state:
            return None
        
        return current_state["transitions"].get(new_status)
    
    def can_receive_tasks(self, status: AgentStatus) -> bool:
        """Check if agent can receive tasks in current state"""
        state = self.states.get(status)
        return state["can_receive_tasks"] if state else False
    
    def can_coordinate(self, status: AgentStatus) -> bool:
        """Check if agent can coordinate in current state"""
        state = self.states.get(status)
        return state["can_coordinate"] if state else False


class AgentStatePersistence:
    """Persistent storage for agent states"""
    
    def __init__(self, redis_host: str = "localhost", redis_port: int = 6379, redis_db: int = 0):
        try:
            self.redis = redis.Redis(
                host=redis_host,
                port=redis_port,
                db=redis_db,
                decode_responses=True
            )
            self.redis.ping()
            print(f"[AgentStatePersistence] Connected to Redis at {redis_host}:{redis_port}")
        except Exception as e:
            print(f"[AgentStatePersistence] Failed to connect to Redis: {e}")
            self.redis = None
    
    def save_agent_state(self, agent_id: str, agent_state: AgentState) -> bool:
        """Save agent state to persistent storage"""
        if not self.redis:
            return False
        
        try:
            key = f"agent_state:{agent_id}"
            value = json.dumps(asdict(agent_state))
            self.redis.set(key, value)
            self.redis.expire(key, 3600)  # 1 hour TTL
            return True
        except Exception as e:
            print(f"[AgentStatePersistence] Error saving agent state: {e}")
            return False
    
    def load_agent_state(self, agent_id: str) -> Optional[AgentState]:
        """Load agent state from persistent storage"""
        if not self.redis:
            return None
        
        try:
            key = f"agent_state:{agent_id}"
            value = self.redis.get(key)
            
            if value:
                data = json.loads(value)
                return AgentState(**data)
            return None
        except Exception as e:
            print(f"[AgentStatePersistence] Error loading agent state: {e}")
            return None
    
    def save_agent_history(self, agent_id: str, event: AgentEvent) -> bool:
        """Save agent event history"""
        if not self.redis:
            return False
        
        try:
            key = f"agent_history:{agent_id}"
            value = json.dumps(event.to_dict())
            
            # Add to list
            self.redis.rpush(key, value)
            self.redis.ltrim(key, -1000, -1)  # Keep last 1000 events
            self.redis.expire(key, 86400)  # 24 hours TTL
            
            return True
        except Exception as e:
            print(f"[AgentStatePersistence] Error saving agent history: {e}")
            return False
    
    def get_agent_history(self, agent_id: str, limit: int = 100) -> List[AgentEvent]:
        """Get agent event history"""
        if not self.redis:
            return []
        
        try:
            key = f"agent_history:{agent_id}"
            values = self.redis.lrange(key, -limit, -1)
            
            events = []
            for value in values:
                data = json.loads(value)
                event = AgentEvent(
                    event_id=data["event_id"],
                    event_type=AgentEventType(data["event_type"]),
                    agent_id=data["agent_id"],
                    timestamp=datetime.fromisoformat(data["timestamp"]),
                    data=data["data"],
                    previous_state=AgentState(**data["previous_state"]) if data["previous_state"] else None,
                    current_state=AgentState(**data["current_state"]) if data["current_state"] else None
                )
                events.append(event)
            
            return events
        except Exception as e:
            print(f"[AgentStatePersistence] Error loading agent history: {e}")
            return []


class AgentStateSynchronizer:
    """Synchronize agent states across the system"""
    
    def __init__(self, persistence: AgentStatePersistence):
        self.persistence = persistence
        self.state_machine = AgentStateMachine()
        self.agent_states: Dict[str, AgentState] = {}
        self.event_callbacks: Dict[str, List[Callable]] = {}
        self.sync_interval = 30.0  # seconds
        self.is_running = False
        self.sync_thread = None
    
    def register_agent(self, agent_id: str, initial_state: AgentState):
        """Register a new agent"""
        # Load from persistence first
        persisted_state = self.persistence.load_agent_state(agent_id)
        state = persisted_state if persisted_state else initial_state
        
        self.agent_states[agent_id] = state
        
        # Create registration event
        event = AgentEvent(
            event_id=str(time.time()),
            event_type=AgentEventType.REGISTRATION,
            agent_id=agent_id,
            timestamp=datetime.now(timezone.utc),
            data={"initial_state": state.status.value},
            previous_state=None,
            current_state=state
        )
        
        # Save to persistence
        self.persistence.save_agent_state(agent_id, state)
        self.persistence.save_agent_history(agent_id, event)
        
        # Notify callbacks
        self._notify_listeners(agent_id, event)
        
        print(f"[AgentStateSynchronizer] Registered agent: {agent_id}")
    
    def update_agent_state(self, agent_id: str, new_status: AgentStatus, 
                          force_update: bool = False) -> bool:
        """Update agent state with validation"""
        if agent_id not in self.agent_states:
            print(f"[AgentStateSynchronizer] Agent {agent_id} not registered")
            return False
        
        current_state = self.agent_states[agent_id]
        
        # Validate state transition
        if not force_update and not self.state_machine.can_transition(current_state.status, new_status):
            print(f"[AgentStateSynchronizer] Invalid transition: {current_state.status.value} -> {new_status.value}")
            return False
        
        # Create transition event
        previous_state = AgentState(
            agent_id=current_state.agent_id,
            status=current_state.status,
            capabilities=current_state.capabilities,
            load_score=current_state.load_score,
            last_heartbeat=current_state.last_heartbeat,
            resource_usage=current_state.resource_usage
        )
        
        # Update state
        current_state.status = new_status
        current_state.last_heartbeat = datetime.now(timezone.utc)
        
        # Create event
        event = AgentEvent(
            event_id=str(time.time()),
            event_type=AgentEventType.STATUS_CHANGE,
            agent_id=agent_id,
            timestamp=datetime.now(timezone.utc),
            data={"new_status": new_status.value},
            previous_state=previous_state,
            current_state=current_state
        )
        
        # Save to persistence
        self.persistence.save_agent_state(agent_id, current_state)
        self.persistence.save_agent_history(agent_id, event)
        
        # Notify callbacks
        self._notify_listeners(agent_id, event)
        
        print(f"[AgentStateSynchronizer] State updated: {agent_id} {previous_state.status.value} -> {new_status.value}")
        return True
    
    def update_agent_metrics(self, agent_id: str, load_score: float, 
                           resource_usage: Dict[str, float]):
        """Update agent metrics"""
        if agent_id not in self.agent_states:
            return False
        
        agent_state = self.agent_states[agent_id]
        
        # Update metrics
        previous_load_score = agent_state.load_score
        previous_resource_usage = agent_state.resource_usage.copy()
        
        agent_state.load_score = load_score
        agent_state.resource_usage = resource_usage
        
        # Create metrics update event
        event = AgentEvent(
            event_id=str(time.time()),
            event_type=AgentEventType.HEARTBEAT,
            agent_id=agent_id,
            timestamp=datetime.now(timezone.utc),
            data={
                "load_score": load_score,
                "resource_usage": resource_usage
            },
            previous_state=AgentState(
                agent_id=agent_state.agent_id,
                status=agent_state.status,
                capabilities=agent_state.capabilities,
                load_score=previous_load_score,
                last_heartbeat=agent_state.last_heartbeat,
                resource_usage=previous_resource_usage
            ),
            current_state=agent_state
        )
        
        # Save to persistence
        self.persistence.save_agent_state(agent_id, agent_state)
        self.persistence.save_agent_history(agent_id, event)
        
        # Notify callbacks
        self._notify_listeners(agent_id, event)
        
        return True
    
    def assign_task(self, agent_id: str, task_id: str) -> bool:
        """Assign task to agent"""
        if agent_id not in self.agent_states:
            return False
        
        agent_state = self.agent_states[agent_id]
        
        # Check if agent can receive tasks
        if not self.state_machine.can_receive_tasks(agent_state.status):
            print(f"[AgentStateSynchronizer] Agent {agent_id} cannot receive tasks in state: {agent_state.status.value}")
            return False
        
        # Create task assignment event
        previous_task_id = agent_state.current_task_id
        
        agent_state.current_task_id = task_id
        
        event = AgentEvent(
            event_id=str(time.time()),
            event_type=AgentEventType.TASK_ASSIGNMENT,
            agent_id=agent_id,
            timestamp=datetime.now(timezone.utc),
            data={"task_id": task_id},
            previous_state=AgentState(
                agent_id=agent_state.agent_id,
                status=agent_state.status,
                capabilities=agent_state.capabilities,
                load_score=agent_state.load_score,
                last_heartbeat=agent_state.last_heartbeat,
                resource_usage=agent_state.resource_usage,
                current_task_id=previous_task_id
            ),
            current_state=agent_state
        )
        
        # Save to persistence
        self.persistence.save_agent_state(agent_id, agent_state)
        self.persistence.save_agent_history(agent_id, event)
        
        # Notify callbacks
        self._notify_listeners(agent_id, event)
        
        print(f"[AgentStateSynchronizer] Task assigned: {agent_id} -> {task_id}")
        return True
    
    def complete_task(self, agent_id: str, task_id: str, result: Any) -> bool:
        """Mark task as completed"""
        if agent_id not in self.agent_states:
            return False
        
        agent_state = self.agent_states[agent_id]
        
        # Create task completion event
        previous_task_id = agent_state.current_task_id
        
        agent_state.current_task_id = None
        
        event = AgentEvent(
            event_id=str(time.time()),
            event_type=AgentEventType.TASK_COMPLETION,
            agent_id=agent_id,
            timestamp=datetime.now(timezone.utc),
            data={"task_id": task_id, "result": result},
            previous_state=AgentState(
                agent_id=agent_state.agent_id,
                status=agent_state.status,
                capabilities=agent_state.capabilities,
                load_score=agent_state.load_score,
                last_heartbeat=agent_state.last_heartbeat,
                resource_usage=agent_state.resource_usage,
                current_task_id=previous_task_id
            ),
            current_state=agent_state
        )
        
        # Save to persistence
        self.persistence.save_agent_state(agent_id, agent_state)
        self.persistence.save_agent_history(agent_id, event)
        
        # Notify callbacks
        self._notify_listeners(agent_id, event)
        
        print(f"[AgentStateSynchronizer] Task completed: {agent_id} -> {task_id}")
        return True
    
    def get_agent_state(self, agent_id: str) -> Optional[AgentState]:
        """Get agent state"""
        return self.agent_states.get(agent_id)
    
    def get_all_agents(self) -> Dict[str, AgentState]:
        """Get all agent states"""
        return self.agent_states.copy()
    
    def get_agents_by_status(self, status: AgentStatus) -> List[AgentState]:
        """Get agents by status"""
        return [state for state in self.agent_states.values() if state.status == status]
    
    def get_agents_by_capability(self, capability: str) -> List[AgentState]:
        """Get agents by capability"""
        return [state for state in self.agent_states.values() if capability in state.capabilities]
    
    def get_agent_history(self, agent_id: str, limit: int = 100) -> List[AgentEvent]:
        """Get agent event history"""
        return self.persistence.get_agent_history(agent_id, limit)
    
    def register_callback(self, agent_id: str, callback: Callable):
        """Register callback for agent events"""
        if agent_id not in self.event_callbacks:
            self.event_callbacks[agent_id] = []
        self.event_callbacks[agent_id].append(callback)
    
    def _notify_listeners(self, agent_id: str, event: AgentEvent):
        """Notify event listeners"""
        if agent_id in self.event_callbacks:
            for callback in self.event_callbacks[agent_id]:
                try:
                    callback(event)
                except Exception as e:
                    print(f"[AgentStateSynchronizer] Error in callback: {e}")
    
    def start_sync(self):
        """Start background synchronization"""
        if not self.is_running:
            self.is_running = True
            self.sync_thread = threading.Thread(target=self._sync_loop)
            self.sync_thread.daemon = True
            self.sync_thread.start()
            print("[AgentStateSynchronizer] Started state synchronization")
    
    def stop_sync(self):
        """Stop background synchronization"""
        self.is_running = False
        if self.sync_thread:
            self.sync_thread.join(timeout=5)
        print("[AgentStateSynchronizer] Stopped state synchronization")
    
    def _sync_loop(self):
        """Background synchronization loop"""
        while self.is_running:
            try:
                # Check for stale agents
                self._check_stale_agents()
                
                # Sync with persistence
                self._sync_with_persistence()
                
                time.sleep(self.sync_interval)
            except Exception as e:
                print(f"[AgentStateSynchronizer] Error in sync loop: {e}")
                time.sleep(1)
    
    def _check_stale_agents(self):
        """Check for stale agents (no heartbeat)"""
        current_time = datetime.now(timezone.utc)
        stale_threshold = 120  # 2 minutes
        
        stale_agents = []
        for agent_id, agent_state in self.agent_states.items():
            time_diff = (current_time - agent_state.last_heartbeat).total_seconds()
            if time_diff > stale_threshold:
                stale_agents.append(agent_id)
        
        # Mark stale agents as offline
        for agent_id in stale_agents:
            print(f"[AgentStateSynchronizer] Agent {agent_id} is stale, marking as offline")
            self.update_agent_state(agent_id, AgentStatus.OFFLINE, force_update=True)
    
    def _sync_with_persistence(self):
        """Sync agent states with persistence layer"""
        for agent_id, agent_state in self.agent_states.items():
            self.persistence.save_agent_state(agent_id, agent_state)
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get system-wide state metrics"""
        total_agents = len(self.agent_states)
        
        status_counts = {}
        for status in AgentStatus:
            status_counts[status.value] = len(self.get_agents_by_status(status))
        
        capability_counts = {}
        all_capabilities = set()
        for state in self.agent_states.values():
            all_capabilities.update(state.capabilities)
        
        for capability in all_capabilities:
            capability_counts[capability] = len(self.get_agents_by_capability(capability))
        
        return {
            "total_agents": total_agents,
            "status_distribution": status_counts,
            "capability_distribution": capability_counts,
            "last_sync": datetime.now(timezone.utc).isoformat()
        }