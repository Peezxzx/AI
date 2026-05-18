"""
Agent Communication Protocol - Standardized message format for inter-agent communication
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field
import uuid
import json


class MessageType(Enum):
    """Message types for agent communication"""
    TASK_REQUEST = "task_request"
    TASK_RESPONSE = "task_response"
    TASK_UPDATE = "task_update"
    TASK_CANCEL = "task_cancel"
    HEARTBEAT = "heartbeat"
    ERROR = "error"
    COORDINATION_REQUEST = "coordination_request"
    COORDINATION_RESPONSE = "coordination_response"
    RESOURCE_REQUEST = "resource_request"
    RESOURCE_RESPONSE = "resource_response"
    KNOWLEDGE_SHARE = "knowledge_share"
    STATE_SYNC = "state_sync"


class MessagePriority(Enum):
    """Message priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


class AgentStatus(Enum):
    """Agent status states"""
    IDLE = "idle"
    WORKING = "working"
    COORDINATING = "coordinating"
    ERROR = "error"
    OFFLINE = "offline"


class MessageHeader(BaseModel):
    """Standardized message header"""
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    message_type: MessageType
    priority: MessagePriority = MessagePriority.NORMAL
    source_agent: str
    target_agent: Optional[str] = None
    correlation_id: Optional[str] = None
    reply_to: Optional[str] = None
    
    class Config:
        use_enum_values = True


class MessagePayload(BaseModel):
    """Standardized message payload"""
    task_id: Optional[str] = None
    task_data: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    error_info: Optional[Dict[str, Any]] = None
    performance_metrics: Optional[Dict[str, Any]] = None
    
    class Config:
        use_enum_values = True


class AgentState(BaseModel):
    """Agent state information"""
    agent_id: str
    status: AgentStatus
    current_task_id: Optional[str] = None
    capabilities: List[str] = Field(default_factory=list)
    load_score: float = 0.0
    last_heartbeat: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    resource_usage: Dict[str, float] = Field(default_factory=dict)


class Message(BaseModel):
    """Complete standardized message format"""
    header: MessageHeader
    payload: MessagePayload
    signature: Optional[str] = None
    
    class Config:
        use_enum_values = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary"""
        return self.model_dump()
    
    def to_json(self) -> str:
        """Convert message to JSON string"""
        return self.model_dump_json()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """Create message from dictionary"""
        return cls(**data)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Message':
        """Create message from JSON string"""
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def is_targeted(self, agent_id: str) -> bool:
        """Check if message is targeted to specific agent"""
        return self.header.target_agent == agent_id or self.header.target_agent is None


class TaskRequestMessage(BaseModel):
    """Task request message"""
    header: MessageHeader = Field(default_factory=lambda: MessageHeader(
        message_type=MessageType.TASK_REQUEST,
        priority=MessagePriority.NORMAL
    ))
    payload: MessagePayload = Field(default_factory=MessagePayload)
    
    def set_task(self, task_id: str, task_data: Dict[str, Any], target_agent: str):
        """Set task information"""
        self.header.message_id = str(uuid.uuid4())
        self.header.timestamp = datetime.now(timezone.utc)
        self.header.target_agent = target_agent
        self.payload.task_id = task_id
        self.payload.task_data = task_data


class TaskResponseMessage(BaseModel):
    """Task response message"""
    header: MessageHeader = Field(default_factory=lambda: MessageHeader(
        message_type=MessageType.TASK_RESPONSE,
        priority=MessagePriority.NORMAL
    ))
    payload: MessagePayload = Field(default_factory=MessagePayload)
    
    def set_response(self, task_id: str, result: Any, target_agent: str):
        """Set response information"""
        self.header.message_id = str(uuid.uuid4())
        self.header.timestamp = datetime.now(timezone.utc)
        self.header.target_agent = target_agent
        self.header.reply_to = task_id
        self.payload.task_id = task_id
        self.payload.task_data = {"result": result}


class CoordinationRequestMessage(BaseModel):
    """Coordination request message"""
    header: MessageHeader = Field(default_factory=lambda: MessageHeader(
        message_type=MessageType.COORDINATION_REQUEST,
        priority=MessagePriority.HIGH
    ))
    payload: MessagePayload = Field(default_factory=MessagePayload)
    
    def set_coordination_request(self, task_id: str, coordination_data: Dict[str, Any], 
                                target_agent: str):
        """Set coordination request"""
        self.header.message_id = str(uuid.uuid4())
        self.header.timestamp = datetime.now(timezone.utc)
        self.header.target_agent = target_agent
        self.payload.task_id = task_id
        self.payload.task_data = coordination_data


class CommunicationChannel:
    """Communication channel for agent messaging"""
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.message_queue = []
        self.processed_messages = []
    
    def send_message(self, message: Message) -> bool:
        """Send message to target agent"""
        try:
            # In real implementation, this would send via Redis or message queue
            # For now, we'll simulate the send
            print(f"[{self.agent_id}] Sending message: {message.header.message_type}")
            print(f"  -> To: {message.header.target_agent}")
            print(f"  -> Task ID: {message.payload.task_id}")
            return True
        except Exception as e:
            print(f"[{self.agent_id}] Error sending message: {e}")
            return False
    
    def receive_message(self, message: Message) -> bool:
        """Receive message from another agent"""
        if message.is_targeted(self.agent_id):
            self.message_queue.append(message)
            print(f"[{self.agent_id}] Received message: {message.header.message_type}")
            return True
        return False
    
    def process_messages(self):
        """Process all pending messages"""
        while self.message_queue:
            message = self.message_queue.pop(0)
            self._process_single_message(message)
            self.processed_messages.append(message)
    
    def _process_single_message(self, message: Message):
        """Process a single message based on type"""
        msg_type = message.header.message_type
        
        if msg_type == MessageType.TASK_REQUEST:
            self._handle_task_request(message)
        elif msg_type == MessageType.TASK_RESPONSE:
            self._handle_task_response(message)
        elif msg_type == MessageType.COORDINATION_REQUEST:
            self._handle_coordination_request(message)
        elif msg_type == MessageType.HEARTBEAT:
            self._handle_heartbeat(message)
        elif msg_type == MessageType.ERROR:
            self._handle_error(message)
        else:
            print(f"[{self.agent_id}] Unknown message type: {msg_type}")
    
    def _handle_task_request(self, message: Message):
        """Handle task request message"""
        print(f"[{self.agent_id}] Processing task request: {message.payload.task_id}")
        # Implement task processing logic
        pass
    
    def _handle_task_response(self, message: Message):
        """Handle task response message"""
        print(f"[{self.agent_id}] Received task response for: {message.payload.task_id}")
        # Implement response handling logic
        pass
    
    def _handle_coordination_request(self, message: Message):
        """Handle coordination request message"""
        print(f"[{self.agent_id}] Processing coordination request: {message.payload.task_id}")
        # Implement coordination logic
        pass
    
    def _handle_heartbeat(self, message: Message):
        """Handle heartbeat message"""
        print(f"[{self.agent_id}] Received heartbeat from {message.header.source_agent}")
        # Implement heartbeat handling
        pass
    
    def _handle_error(self, message: Message):
        """Handle error message"""
        print(f"[{self.agent_id}] Error from {message.header.source_agent}: {message.payload.error_info}")
        # Implement error handling
        pass


class MessageValidator:
    """Message validation utility"""
    
    @staticmethod
    def validate_message(message: Message) -> bool:
        """Validate message format and content"""
        try:
            # Check required fields
            if not message.header.message_id:
                return False
            if not message.header.timestamp:
                return False
            if not message.header.source_agent:
                return False
            if not message.header.message_type:
                return False
            
            # Check payload validity
            if message.payload.task_id and not isinstance(message.payload.task_id, str):
                return False
            
            return True
        except Exception:
            return False
    
    @staticmethod
    def create_error_message(original_message: Message, error_type: str, 
                           error_details: Dict[str, Any]) -> Message:
        """Create error response message"""
        error_msg = Message(
            header=MessageHeader(
                message_type=MessageType.ERROR,
                source_agent=original_message.header.target_agent or "system",
                target_agent=original_message.header.source_agent,
                reply_to=original_message.header.message_id
            ),
            payload=MessagePayload(
                task_id=original_message.payload.task_id,
                error_info={
                    "type": error_type,
                    "details": error_details,
                    "original_message": original_message.header.message_id
                }
            )
        )
        return error_msg