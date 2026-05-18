"""
Event Publisher for Atsawin AI Event System
Publishes events to Redis message queue
"""

import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio
from .models import Event, EventType, EventPriority
from redis_client import redis_client

class EventPublisher:
    """Event publisher for publishing events to Redis"""
    
    def __init__(self, redis_client=None):
        self.logger = logging.getLogger(__name__)
        self.redis_client = redis_client or redis_client
        self.publish_channels = {}
        
    async def publish_event(self, event: Event, channel: str = "events") -> bool:
        """
        Publish an event to Redis
        
        Args:
            event: Event to publish
            channel: Redis channel to publish to
            
        Returns:
            bool: True if published successfully
        """
        try:
            # Convert event to JSON
            event_json = json.dumps(event.to_dict(), default=str)
            
            # Publish to Redis
            if self.redis_client:
                await self.redis_client.publish(channel, event_json)
                self.logger.info(f"Published event {event.id} to channel {channel}")
                return True
            else:
                self.logger.warning(f"Redis client not available for event {event.id}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to publish event {event.id}: {str(e)}")
            return False
    
    async def publish_system_event(self, event_type: EventType, source: str, 
                                 data: Dict[str, Any] = None, 
                                 priority: EventPriority = EventPriority.NORMAL,
                                 channel: str = "events") -> bool:
        """
        Convenience method to publish a system event
        
        Args:
            event_type: Type of event
            source: Source of the event
            data: Event data
            priority: Event priority
            channel: Redis channel
            
        Returns:
            bool: True if published successfully
        """
        event = Event(
            event_type=event_type,
            source=source,
            priority=priority,
            data=data or {}
        )
        
        return await self.publish_event(event, channel)
    
    async def publish_agent_task_event(self, task_id: str, agent_type: str, 
                                     status: str, result: Any = None,
                                     priority: EventPriority = EventPriority.NORMAL) -> bool:
        """
        Publish an agent task event
        
        Args:
            task_id: ID of the task
            agent_type: Type of agent
            status: Task status
            result: Task result
            priority: Event priority
            
        Returns:
            bool: True if published successfully
        """
        event_data = {
            "task_id": task_id,
            "agent_type": agent_type,
            "status": status,
            "timestamp": datetime.now().isoformat()
        }
        
        if result is not None:
            event_data["result"] = result
        
        event_type = self._get_task_event_type(status)
        
        return await self.publish_system_event(
            event_type=event_type,
            source=f"agent:{agent_type}",
            data=event_data,
            priority=priority,
            channel="agent_events"
        )
    
    async def publish_memory_event(self, operation: str, key: str, 
                                 memory_type: str = None, user_id: str = None,
                                 result: Any = None) -> bool:
        """
        Publish a memory system event
        
        Args:
            operation: Memory operation (store, retrieve, cleanup)
            key: Memory key
            memory_type: Type of memory
            user_id: User ID
            result: Operation result
            
        Returns:
            bool: True if published successfully
        """
        event_data = {
            "operation": operation,
            "key": key,
            "memory_type": memory_type,
            "user_id": user_id,
            "timestamp": datetime.now().isoformat()
        }
        
        if result is not None:
            event_data["result"] = result
        
        event_type = EventType.MEMORY_STORED if operation == "store" else \
                    EventType.MEMORY_RETRIEVED if operation == "retrieve" else \
                    EventType.MEMORY_CLEANUP
        
        return await self.publish_system_event(
            event_type=event_type,
            source="memory_manager",
            data=event_data,
            channel="memory_events"
        )
    
    async def publish_api_event(self, method: str, endpoint: str, 
                              status_code: int, response_time: float,
                              user_id: str = None) -> bool:
        """
        Publish an API event
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            status_code: HTTP status code
            response_time: Response time in seconds
            user_id: User ID
            
        Returns:
            bool: True if published successfully
        """
        event_data = {
            "method": method,
            "endpoint": endpoint,
            "status_code": status_code,
            "response_time": response_time,
            "user_id": user_id,
            "timestamp": datetime.now().isoformat()
        }
        
        event_type = EventType.API_REQUEST if status_code < 400 else EventType.API_ERROR
        
        return await self.publish_system_event(
            event_type=event_type,
            source="api_server",
            data=event_data,
            priority=EventPriority.HIGH if status_code >= 500 else EventPriority.NORMAL,
            channel="api_events"
        )
    
    async def publish_resource_alert(self, resource_type: str, current_usage: float,
                                   threshold: float, message: str) -> bool:
        """
        Publish a resource alert event
        
        Args:
            resource_type: Type of resource (CPU, memory, disk, etc.)
            current_usage: Current usage percentage
            threshold: Alert threshold
            message: Alert message
            
        Returns:
            bool: True if published successfully
        """
        event_data = {
            "resource_type": resource_type,
            "current_usage": current_usage,
            "threshold": threshold,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        
        return await self.publish_system_event(
            event_type=EventType.RESOURCE_ALERT,
            source="resource_manager",
            data=event_data,
            priority=EventPriority.HIGH,
            channel="resource_events"
        )
    
    def _get_task_event_type(self, status: str) -> EventType:
        """Get event type based on task status"""
        status_map = {
            "submitted": EventType.AGENT_TASK_SUBMITTED,
            "started": EventType.AGENT_TASK_STARTED,
            "completed": EventType.AGENT_TASK_COMPLETED,
            "failed": EventType.AGENT_TASK_FAILED,
            "coordination": EventType.AGENT_COORDINATION
        }
        return status_map.get(status, EventType.AGENT_TASK_SUBMITTED)
    
    async def batch_publish(self, events: List[Event], channel: str = "events") -> Dict[str, bool]:
        """
        Publish multiple events in batch
        
        Args:
            events: List of events to publish
            channel: Redis channel
            
        Returns:
            Dict mapping event IDs to success status
        """
        results = {}
        
        for event in events:
            results[event.id] = await self.publish_event(event, channel)
        
        success_count = sum(1 for success in results.values() if success)
        self.logger.info(f"Batch publish: {success_count}/{len(events)} events published successfully")
        
        return results
    
    async def publish_health_check(self, component: str, status: str, 
                                 metrics: Dict[str, Any] = None) -> bool:
        """
        Publish a health check event
        
        Args:
            component: Component name
            status: Health status (healthy, warning, critical)
            metrics: Health metrics
            
        Returns:
            bool: True if published successfully
        """
        event_data = {
            "component": component,
            "status": status,
            "metrics": metrics or {},
            "timestamp": datetime.now().isoformat()
        }
        
        event_type = EventType.SYSTEM_HEALTH_CHECK if status == "healthy" else EventType.RESOURCE_ALERT
        
        priority = EventPriority.CRITICAL if status == "critical" else \
                  EventPriority.HIGH if status == "warning" else EventPriority.NORMAL
        
        return await self.publish_system_event(
            event_type=event_type,
            source=component,
            data=event_data,
            priority=priority,
            channel="health_events"
        )