"""
Event data models for the Atsawin AI Event System
"""

from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from typing import Dict, Any, Optional, List
import uuid

class EventType(Enum):
    """Event types for the AI Operating System"""
    # System Events
    SYSTEM_STARTUP = "system_startup"
    SYSTEM_SHUTDOWN = "system_shutdown"
    SYSTEM_HEALTH_CHECK = "system_health_check"
    RESOURCE_ALERT = "resource_alert"
    
    # Agent Events
    AGENT_TASK_SUBMITTED = "agent_task_submitted"
    AGENT_TASK_STARTED = "agent_task_started"
    AGENT_TASK_COMPLETED = "agent_task_completed"
    AGENT_TASK_FAILED = "agent_task_failed"
    AGENT_COORDINATION = "agent_coordination"
    
    # Memory Events
    MEMORY_STORED = "memory_stored"
    MEMORY_RETRIEVED = "memory_retrieved"
    MEMORY_CLEANUP = "memory_cleanup"
    
    # AI Model Events
    MODEL_REQUEST = "model_request"
    MODEL_RESPONSE = "model_response"
    MODEL_ROUTING = "model_routing"
    
    # Database Events
    DB_CONNECTION = "db_connection"
    DB_QUERY = "db_query"
    DB_ERROR = "db_error"
    
    # API Events
    API_REQUEST = "api_request"
    API_RESPONSE = "api_response"
    API_ERROR = "api_error"
    
    # Docker Events
    DOCKER_CONTAINER_START = "docker_container_start"
    DOCKER_CONTAINER_STOP = "docker_container_stop"
    DOCKER_HEALTH_CHECK = "docker_health_check"
    
    # Telegram Events
    TELEGRAM_MESSAGE = "telegram_message"
    TELEGRAM_COMMAND = "telegram_command"
    TELEGRAM_ERROR = "telegram_error"

class EventPriority(Enum):
    """Event priority levels"""
    CRITICAL = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4
    BACKGROUND = 5

@dataclass
class Event:
    """Base event structure"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: EventType = None
    priority: EventPriority = EventPriority.NORMAL
    source: str = None
    target: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    retry_count: int = 0
    max_retries: int = 3
    
    def __post_init__(self):
        if self.event_type is None:
            raise ValueError("Event type must be specified")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary"""
        return {
            "id": self.id,
            "event_type": self.event_type.value,
            "priority": self.priority.value,
            "source": self.source,
            "target": self.target,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data,
            "metadata": self.metadata,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Event':
        """Create event from dictionary"""
        return cls(
            id=data["id"],
            event_type=EventType(data["event_type"]),
            priority=EventPriority(data["priority"]),
            source=data.get("source"),
            target=data.get("target"),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            data=data.get("data", {}),
            metadata=data.get("metadata", {}),
            retry_count=data.get("retry_count", 0),
            max_retries=data.get("max_retries", 3)
        )
    
    def is_retryable(self) -> bool:
        """Check if event can be retried"""
        return self.retry_count < self.max_retries
    
    def increment_retry(self):
        """Increment retry count"""
        self.retry_count += 1
    
    def should_retry(self) -> bool:
        """Check if event should be retried"""
        return self.is_retryable() and self.metadata.get("retry_on_failure", True)

@dataclass
class EventFilter:
    """Event filter for subscription"""
    event_types: List[EventType] = None
    sources: List[str] = None
    priorities: List[EventPriority] = None
    source_contains: Optional[str] = None
    data_filter: Optional[Dict[str, Any]] = None
    
    def matches(self, event: Event) -> bool:
        """Check if event matches filter"""
        # Filter by event types
        if self.event_types and event.event_type not in self.event_types:
            return False
        
        # Filter by sources
        if self.sources and event.source not in self.sources:
            return False
        
        # Filter by priorities
        if self.priorities and event.priority not in self.priorities:
            return False
        
        # Filter by source contains
        if self.source_contains and self.source_contains not in event.source:
            return False
        
        # Filter by data
        if self.data_filter:
            for key, value in self.data_filter.items():
                if key not in event.data or event.data[key] != value:
                    return False
        
        return True