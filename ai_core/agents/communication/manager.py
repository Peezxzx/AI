"""
Agent Communication Manager - Centralized communication hub for all agents
"""

import asyncio
import threading
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Callable, Any
from collections import defaultdict

from .protocol import (
    Message, MessageType, MessagePriority, AgentStatus,
    AgentState, CommunicationChannel,
    MessageValidator, TaskRequestMessage, TaskResponseMessage,
    CoordinationRequestMessage
)


class AgentRegistry:
    """Registry of all active agents in the system"""
    
    def __init__(self):
        self.agents: Dict[str, AgentState] = {}
        self.agent_channels: Dict[str, CommunicationChannel] = {}
        self.agent_callbacks: Dict[str, Dict[str, Callable]] = defaultdict(dict)
    
    def register_agent(self, agent_id: str, agent_state: AgentState, 
                      channel: CommunicationChannel):
        """Register a new agent"""
        self.agents[agent_id] = agent_state
        self.agent_channels[agent_id] = channel
        print(f"[AgentRegistry] Registered agent: {agent_id}")
    
    def unregister_agent(self, agent_id: str):
        """Unregister an agent"""
        if agent_id in self.agents:
            del self.agents[agent_id]
        if agent_id in self.agent_channels:
            del self.agent_channels[agent_id]
        print(f"[AgentRegistry] Unregistered agent: {agent_id}")
    
    def get_agent(self, agent_id: str) -> Optional[AgentState]:
        """Get agent by ID"""
        return self.agents.get(agent_id)
    
    def get_channel(self, agent_id: str) -> Optional[CommunicationChannel]:
        """Get communication channel for agent"""
        return self.agent_channels.get(agent_id)
    
    def get_all_agents(self) -> Dict[str, AgentState]:
        """Get all registered agents"""
        return self.agents.copy()
    
    def update_agent_state(self, agent_id: str, status: AgentStatus, 
                          current_task_id: Optional[str] = None,
                          load_score: float = 0.0):
        """Update agent state"""
        if agent_id in self.agents:
            self.agents[agent_id].status = status
            self.agents[agent_id].current_task_id = current_task_id
            self.agents[agent_id].load_score = load_score
            self.agents[agent_id].last_heartbeat = datetime.now(timezone.utc)
    
    def register_callback(self, agent_id: str, message_type: str, callback: Callable):
        """Register callback for specific agent and message type"""
        self.agent_callbacks[agent_id][message_type] = callback
    
    def get_callback(self, agent_id: str, message_type: str) -> Optional[Callable]:
        """Get callback for specific agent and message type"""
        return self.agent_callbacks.get(agent_id, {}).get(message_type)


class MessageRouter:
    """Message routing and distribution"""
    
    def __init__(self, agent_registry: AgentRegistry):
        self.agent_registry = agent_registry
        self.routing_rules: Dict[str, List[str]] = {}
        self.message_history: List[Message] = []
        self.max_history = 1000
    
    def add_routing_rule(self, message_type: str, target_agents: List[str]):
        """Add routing rule for message type"""
        self.routing_rules[message_type.value] = target_agents
    
    def route_message(self, message: Message) -> List[str]:
        """Route message to appropriate agents"""
        routed_agents = []
        
        # Check routing rules
        routing_key = message.header.message_type.value
        if routing_key in self.routing_rules:
            routed_agents.extend(self.routing_rules[routing_key])
        
        # If no routing rules, broadcast to all agents (except source)
        if not routed_agents:
            for agent_id in self.agent_registry.agents:
                if agent_id != message.header.source_agent:
                    routed_agents.append(agent_id)
        
        # Filter out agents that don't match target specification
        final_targets = []
        for agent_id in routed_agents:
            if message.is_targeted(agent_id):
                final_targets.append(agent_id)
        
        return final_targets
    
    def send_message(self, message: Message) -> Dict[str, bool]:
        """Send message to target agents"""
        results = {}
        target_agents = self.route_message(message)
        
        for agent_id in target_agents:
            channel = self.agent_registry.get_channel(agent_id)
            if channel:
                results[agent_id] = channel.receive_message(message)
            else:
                results[agent_id] = False
        
        # Add to history
        self.message_history.append(message)
        if len(self.message_history) > self.max_history:
            self.message_history.pop(0)
        
        return results
    
    def get_message_history(self, agent_id: Optional[str] = None, 
                          message_type: Optional[MessageType] = None,
                          limit: int = 100) -> List[Message]:
        """Get message history with optional filtering"""
        history = self.message_history[-limit:] if limit else self.message_history
        
        if agent_id:
            history = [msg for msg in history 
                      if msg.header.source_agent == agent_id or 
                         msg.header.target_agent == agent_id]
        
        if message_type:
            history = [msg for msg in history 
                      if msg.header.message_type == message_type]
        
        return history


class CommunicationManager:
    """Main communication manager for agent coordination"""
    
    def __init__(self):
        self.agent_registry = AgentRegistry()
        self.message_router = MessageRouter(self.agent_registry)
        self.message_processor = MessageProcessor(self.agent_registry)
        self.is_running = False
        self.processing_thread = None
        
        # Setup default routing rules
        self._setup_routing_rules()
    
    def _setup_routing_rules(self):
        """Setup default routing rules for different message types"""
        # Task requests go to available agents
        self.message_router.add_routing_rule(
            MessageType.TASK_REQUEST, 
            ["coding_agent", "trading_agent", "research_agent"]
        )
        
        # Coordination requests go to coordination agent
        self.message_router.add_routing_rule(
            MessageType.COORDINATION_REQUEST,
            ["coordination_agent"]
        )
        
        # Heartbeats go to all agents
        self.message_router.add_routing_rule(
            MessageType.HEARTBEAT,
            ["coding_agent", "trading_agent", "monitoring_agent", "research_agent", "coordination_agent"]
        )
    
    def register_agent(self, agent_id: str, capabilities: List[str], 
                      channel: CommunicationChannel):
        """Register a new agent"""
        agent_state = AgentState(
            agent_id=agent_id,
            status=AgentStatus.IDLE,
            capabilities=capabilities,
            load_score=0.0
        )
        
        self.agent_registry.register_agent(agent_id, agent_state, channel)
        
        # Register default callbacks
        self.agent_registry.register_callback(
            agent_id, MessageType.TASK_REQUEST.value,
            lambda msg: self.message_processor.handle_task_request(agent_id, msg)
        )
        
        self.agent_registry.register_callback(
            agent_id, MessageType.COORDINATION_REQUEST.value,
            lambda msg: self.message_processor.handle_coordination_request(agent_id, msg)
        )
    
    def start_message_processing(self):
        """Start background message processing"""
        if not self.is_running:
            self.is_running = True
            self.processing_thread = threading.Thread(target=self._process_messages_loop)
            self.processing_thread.daemon = True
            self.processing_thread.start()
            print("[CommunicationManager] Started message processing")
    
    def stop_message_processing(self):
        """Stop background message processing"""
        self.is_running = False
        if self.processing_thread:
            self.processing_thread.join(timeout=5)
        print("[CommunicationManager] Stopped message processing")
    
    def _process_messages_loop(self):
        """Background message processing loop"""
        while self.is_running:
            try:
                # Process all channels
                for agent_id, channel in self.agent_registry.agent_channels.items():
                    channel.process_messages()
                
                time.sleep(0.1)  # 100ms processing interval
            except Exception as e:
                print(f"[CommunicationManager] Error in processing loop: {e}")
    
    def send_task_request(self, source_agent: str, target_agent: str, 
                         task_id: str, task_data: Dict[str, Any],
                         priority: MessagePriority = MessagePriority.NORMAL) -> bool:
        """Send task request to target agent"""
        message = TaskRequestMessage()
        message.set_task(task_id, task_data, target_agent)
        message.header.source_agent = source_agent
        message.header.priority = priority
        
        if MessageValidator.validate_message(message):
            results = self.message_router.send_message(message)
            return any(results.values())
        else:
            print(f"[CommunicationManager] Invalid task request for task {task_id}")
            return False
    
    def send_coordination_request(self, source_agent: str, target_agent: str,
                                 task_id: str, coordination_data: Dict[str, Any]) -> bool:
        """Send coordination request to target agent"""
        message = CoordinationRequestMessage()
        message.set_coordination_request(task_id, coordination_data, target_agent)
        message.header.source_agent = source_agent
        
        if MessageValidator.validate_message(message):
            results = self.message_router.send_message(message)
            return any(results.values())
        else:
            print(f"[CommunicationManager] Invalid coordination request for task {task_id}")
            return False
    
    def broadcast_heartbeat(self, source_agent: str):
        """Broadcast heartbeat from source agent"""
        from .protocol import Message, MessageHeader, MessagePayload, MessageType
        
        message = Message(
            header=MessageHeader(
                message_type=MessageType.HEARTBEAT,
                source_agent=source_agent
            ),
            payload=MessagePayload()
        )
        
        results = self.message_router.send_message(message)
        return results
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status"""
        agents = self.agent_registry.get_all_agents()
        status = {
            "total_agents": len(agents),
            "active_agents": len([a for a in agents.values() if a.status != AgentStatus.OFFLINE]),
            "agents": {}
        }
        
        for agent_id, agent_state in agents.items():
            status["agents"][agent_id] = {
                "status": agent_state.status.value,
                "capabilities": agent_state.capabilities,
                "load_score": agent_state.load_score,
                "last_heartbeat": agent_state.last_heartbeat.isoformat() if agent_state.last_heartbeat else None,
                "current_task": agent_state.current_task_id
            }
        
        return status
    
    def get_message_statistics(self) -> Dict[str, Any]:
        """Get message processing statistics"""
        total_messages = len(self.message_router.message_history)
        
        # Count by type
        type_counts = defaultdict(int)
        for message in self.message_router.message_history:
            type_counts[message.header.message_type.value] += 1
        
        return {
            "total_messages": total_messages,
            "messages_by_type": dict(type_counts),
            "routing_rules": len(self.message_router.routing_rules)
        }


class MessageProcessor:
    """Message processing logic"""
    
    def __init__(self, agent_registry: AgentRegistry):
        self.agent_registry = agent_registry
    
    def handle_task_request(self, agent_id: str, message: Message):
        """Handle task request for specific agent"""
        print(f"[MessageProcessor] Agent {agent_id} handling task request: {message.payload.task_id}")
        
        # Update agent state
        self.agent_registry.update_agent_state(agent_id, AgentStatus.WORKING, message.payload.task_id)
        
        # TODO: Implement actual task processing
        # For now, just simulate task completion
        result = {"status": "completed", "result": f"Task {message.payload.task_id} processed by {agent_id}"}
        
        # Send response
        response = TaskResponseMessage()
        response.set_response(message.payload.task_id, result, message.header.source_agent)
        response.header.source_agent = agent_id
        
        channel = self.agent_registry.get_channel(message.header.source_agent)
        if channel:
            channel.send_message(response)
        
        # Update agent state back to idle
        self.agent_registry.update_agent_state(agent_id, AgentStatus.IDLE)
    
    def handle_coordination_request(self, agent_id: str, message: Message):
        """Handle coordination request for specific agent"""
        print(f"[MessageProcessor] Agent {agent_id} handling coordination request: {message.payload.task_id}")
        
        # TODO: Implement actual coordination logic
        coordination_result = {
            "status": "coordinated",
            "coordinated_agents": [agent_id],
            "task_id": message.payload.task_id
        }
        
        # Send response
        from .protocol import TaskResponseMessage
        response = TaskResponseMessage()
        response.set_response(message.payload.task_id, coordination_result, message.header.source_agent)
        response.header.source_agent = agent_id
        
        channel = self.agent_registry.get_channel(message.header.source_agent)
        if channel:
            channel.send_message(response)