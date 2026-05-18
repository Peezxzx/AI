"""
Enhanced Agent - Base class for all agents with communication capabilities
"""

import asyncio
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Callable
from enum import Enum

from .communication import (
    Message, MessageType, MessagePriority, AgentStatus,
    AgentState, CommunicationChannel, CommunicationManager,
    TaskRequestMessage, TaskResponseMessage, CoordinationRequestMessage
)


class AgentCapability(Enum):
    """Agent capabilities"""
    CODING = "coding"
    TRADING = "trading"
    MONITORING = "monitoring"
    RESEARCH = "research"
    COORDINATION = "coordination"
    DATA_ANALYSIS = "data_analysis"
    SYSTEM_ADMIN = "system_admin"


class EnhancedAgent:
    """Enhanced base agent with communication capabilities"""
    
    def __init__(self, agent_id: str, capabilities: List[str], 
                 communication_manager: CommunicationManager):
        self.agent_id = agent_id
        self.capabilities = capabilities
        self.communication_manager = communication_manager
        
        # Create communication channel
        self.communication_channel = CommunicationChannel(agent_id)
        
        # Agent state
        self.state = AgentState(
            agent_id=agent_id,
            status=AgentStatus.IDLE,
            capabilities=capabilities,
            load_score=0.0
        )
        
        # Task management
        self.current_task_id: Optional[str] = None
        self.task_queue: List[Dict[str, Any]] = []
        self.task_history: List[Dict[str, Any]] = []
        
        # Performance metrics
        self.processed_tasks = 0
        self.failed_tasks = 0
        self.total_processing_time = 0.0
        
        # Callbacks
        self.task_callbacks: Dict[str, Callable] = {}
        
        # Register agent
        self.communication_manager.register_agent(agent_id, capabilities, self.communication_channel)
        
        # Start agent lifecycle
        self.is_running = False
        self.heartbeat_interval = 30  # seconds
        self.last_heartbeat = datetime.now(timezone.utc)
    
    async def start(self):
        """Start the agent"""
        self.is_running = True
        print(f"[{self.agent_id}] Starting agent...")
        
        # Start communication processing
        self.communication_manager.start_message_processing()
        
        # Start heartbeat
        asyncio.create_task(self._heartbeat_loop())
        
        # Start task processing
        asyncio.create_task(self._task_processing_loop())
        
        print(f"[{self.agent_id}] Agent started successfully")
    
    async def stop(self):
        """Stop the agent"""
        self.is_running = False
        print(f"[{self.agent_id}] Stopping agent...")
        
        # Stop communication processing
        self.communication_manager.stop_message_processing()
        
        # Update state
        self.state.status = AgentStatus.OFFLINE
        self.communication_manager.agent_registry.update_agent_state(
            self.agent_id, AgentStatus.OFFLINE
        )
        
        print(f"[{self.agent_id}] Agent stopped")
    
    async def _heartbeat_loop(self):
        """Send heartbeat at regular intervals"""
        while self.is_running:
            try:
                self.communication_manager.broadcast_heartbeat(self.agent_id)
                self.last_heartbeat = datetime.now(timezone.utc)
                
                # Update state
                self.communication_manager.agent_registry.update_agent_state(
                    self.agent_id, self.state.status, self.current_task_id, self.state.load_score
                )
                
                await asyncio.sleep(self.heartbeat_interval)
            except Exception as e:
                print(f"[{self.agent_id}] Error in heartbeat loop: {e}")
                await asyncio.sleep(5)  # Wait before retry
    
    async def _task_processing_loop(self):
        """Process tasks from queue"""
        while self.is_running:
            try:
                if self.task_queue and self.state.status == AgentStatus.IDLE:
                    task = self.task_queue.pop(0)
                    await self._process_task(task)
                
                await asyncio.sleep(0.1)  # 100ms check interval
            except Exception as e:
                print(f"[{self.agent_id}] Error in task processing loop: {e}")
                await asyncio.sleep(1)
    
    async def _process_task(self, task: Dict[str, Any]):
        """Process a single task"""
        task_id = task.get("task_id")
        task_data = task.get("data", {})
        
        if not task_id:
            print(f"[{self.agent_id}] Invalid task: missing task_id")
            return
        
        print(f"[{self.agent_id}] Processing task: {task_id}")
        
        # Update state
        self.state.status = AgentStatus.WORKING
        self.current_task_id = task_id
        self.communication_manager.agent_registry.update_agent_state(
            self.agent_id, AgentStatus.WORKING, task_id
        )
        
        start_time = time.time()
        
        try:
            # Execute task
            result = await self.execute_task(task_id, task_data)
            
            # Update metrics
            processing_time = time.time() - start_time
            self.total_processing_time += processing_time
            self.processed_tasks += 1
            
            # Send response
            response = TaskResponseMessage()
            response.set_response(task_id, result, "coordinator")
            response.header.source_agent = self.agent_id
            
            channel = self.communication_manager.agent_registry.get_channel("coordinator")
            if channel:
                channel.send_message(response)
            
            # Add to history
            self.task_history.append({
                "task_id": task_id,
                "status": "completed",
                "result": result,
                "processing_time": processing_time,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
        except Exception as e:
            # Update metrics
            self.failed_tasks += 1
            
            # Send error response
            error_result = {
                "status": "failed",
                "error": str(e),
                "task_id": task_id
            }
            
            response = TaskResponseMessage()
            response.set_response(task_id, error_result, "coordinator")
            response.header.source_agent = self.agent_id
            
            channel = self.communication_manager.agent_registry.get_channel("coordinator")
            if channel:
                channel.send_message(response)
            
            # Add to history
            self.task_history.append({
                "task_id": task_id,
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
        
        finally:
            # Update state back to idle
            self.state.status = AgentStatus.IDLE
            self.current_task_id = None
            self.communication_manager.agent_registry.update_agent_state(
                self.agent_id, AgentStatus.IDLE
            )
            
            # Update load score based on performance
            self._update_load_score()
    
    def _update_load_score(self):
        """Update agent load score based on performance"""
        if self.processed_tasks > 0:
            success_rate = self.processed_tasks / (self.processed_tasks + self.failed_tasks)
            avg_processing_time = self.total_processing_time / self.processed_tasks
            
            # Calculate load score (0.0 to 1.0)
            self.state.load_score = (1.0 - success_rate) * 0.3 + (min(avg_processing_time / 60.0, 1.0)) * 0.7
        else:
            self.state.load_score = 0.0
    
    async def execute_task(self, task_id: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the actual task - to be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement execute_task")
    
    def submit_task(self, task_id: str, task_data: Dict[str, Any]) -> bool:
        """Submit a task to this agent"""
        task = {
            "task_id": task_id,
            "data": task_data,
            "submitted_at": datetime.now(timezone.utc).isoformat()
        }
        
        self.task_queue.append(task)
        print(f"[{self.agent_id}] Task submitted: {task_id}")
        return True
    
    def get_status(self) -> Dict[str, Any]:
        """Get agent status"""
        return {
            "agent_id": self.agent_id,
            "status": self.state.status.value,
            "capabilities": self.capabilities,
            "current_task": self.current_task_id,
            "queue_size": len(self.task_queue),
            "load_score": self.state.load_score,
            "processed_tasks": self.processed_tasks,
            "failed_tasks": self.failed_tasks,
            "success_rate": self.processed_tasks / (self.processed_tasks + self.failed_tasks) if (self.processed_tasks + self.failed_tasks) > 0 else 0.0,
            "avg_processing_time": self.total_processing_time / self.processed_tasks if self.processed_tasks > 0 else 0.0
        }
    
    def get_task_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get task history"""
        return self.task_history[-limit:]
    
    def register_task_callback(self, task_type: str, callback: Callable):
        """Register callback for specific task type"""
        self.task_callbacks[task_type] = callback
    
    def can_handle_task(self, task_type: str) -> bool:
        """Check if agent can handle specific task type"""
        return task_type in self.capabilities


class TaskCoordinator:
    """Task coordination utility"""
    
    def __init__(self, communication_manager: CommunicationManager):
        self.communication_manager = communication_manager
    
    def coordinate_task(self, task_id: str, required_capabilities: List[str],
                       task_data: Dict[str, Any]) -> Optional[str]:
        """Coordinate task across multiple agents"""
        # Find available agents with required capabilities
        available_agents = self._find_available_agents(required_capabilities)
        
        if not available_agents:
            print(f"[TaskCoordinator] No available agents for task: {task_id}")
            return None
        
        # Select best agent based on load score
        best_agent = min(available_agents, key=lambda a: a.load_score)
        
        # Send task request
        success = self.communication_manager.send_task_request(
            source_agent="coordinator",
            target_agent=best_agent.agent_id,
            task_id=task_id,
            task_data=task_data,
            priority=MessagePriority.NORMAL
        )
        
        if success:
            print(f"[TaskCoordinator] Task {task_id} assigned to {best_agent.agent_id}")
            return best_agent.agent_id
        else:
            print(f"[TaskCoordinator] Failed to assign task {task_id}")
            return None
    
    def _find_available_agents(self, required_capabilities: List[str]) -> List[AgentState]:
        """Find available agents with required capabilities"""
        available_agents = []
        
        for agent_state in self.communication_manager.agent_registry.agents.values():
            if (agent_state.status == AgentStatus.IDLE and
                any(cap in agent_state.capabilities for cap in required_capabilities)):
                available_agents.append(agent_state)
        
        return available_agents
    
    def check_agent_availability(self, agent_id: str) -> bool:
        """Check if agent is available"""
        agent = self.communication_manager.agent_registry.get_agent(agent_id)
        return agent is not None and agent.status == AgentStatus.IDLE