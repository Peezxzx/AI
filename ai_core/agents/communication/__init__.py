"""
Communication Module - Enhanced Multi-Agent Communication System
"""

from .protocol import (
    Message, MessageType, MessagePriority, AgentStatus,
    AgentState, CommunicationChannel, MessageValidator,
    TaskRequestMessage, TaskResponseMessage, CoordinationRequestMessage
)

from .manager import (
    AgentRegistry, MessageRouter, CommunicationManager, MessageProcessor
)

__all__ = [
    # Protocol components
    'Message', 'MessageType', 'MessagePriority', 'AgentStatus',
    'AgentState', 'CommunicationChannel', 'MessageValidator',
    'TaskRequestMessage', 'TaskResponseMessage', 'CoordinationRequestMessage',
    
    # Manager components
    'AgentRegistry', 'MessageRouter', 'CommunicationManager', 'MessageProcessor'
]