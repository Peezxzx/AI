"""
Agent Package - Enhanced multi-agent communication system
"""

from .communication.protocol import (
    Message, MessageType, MessagePriority, AgentStatus,
    AgentState, CommunicationChannel, MessageValidator,
    TaskRequestMessage, TaskResponseMessage, CoordinationRequestMessage
)

from .communication.manager import (
    AgentRegistry, MessageRouter, CommunicationManager, MessageProcessor
)

from .enhanced_agent import (
    EnhancedAgent, AgentCapability, TaskCoordinator
)

from .coding_agent import (
    EnhancedCodingAgent
)

__all__ = [
    # Communication components
    'Message', 'MessageType', 'MessagePriority', 'AgentStatus',
    'AgentState', 'CommunicationChannel', 'MessageValidator',
    'TaskRequestMessage', 'TaskResponseMessage', 'CoordinationRequestMessage',
    
    # Manager components
    'AgentRegistry', 'MessageRouter', 'CommunicationManager', 'MessageProcessor',
    
    # Agent components
    'EnhancedAgent', 'AgentCapability', 'TaskCoordinator',
    
    # Specialized agents
    'EnhancedCodingAgent'
]