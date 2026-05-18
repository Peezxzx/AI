"""
Event Router for Atsawin AI Event System
Routes events based on filters, priorities, and routing rules
"""

import logging
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
from .models import Event, EventType, EventPriority, EventFilter
from .event_publisher import EventPublisher
from .event_subscriber import EventSubscriber

class EventRouter:
    """Event router for intelligent event routing"""
    
    def __init__(self, publisher: EventPublisher, subscriber: EventSubscriber):
        self.logger = logging.getLogger(__name__)
        self.publisher = publisher
        self.subscriber = subscriber
        self.routing_rules = {}
        self.priority_handlers = {}
        self.event_history = []
        self.max_history = 1000
        
    def add_routing_rule(self, rule_name: str, filter: EventFilter, 
                        target_channel: str, priority: EventPriority = EventPriority.NORMAL,
                        transform_func: Optional[Callable] = None):
        """
        Add a routing rule
        
        Args:
            rule_name: Name of the routing rule
            filter: Event filter to match
            target_channel: Target channel to route to
            priority: Route priority
            transform_func: Optional function to transform event before routing
        """
        self.routing_rules[rule_name] = {
            "filter": filter,
            "target_channel": target_channel,
            "priority": priority,
            "transform_func": transform_func,
            "created_at": datetime.now()
        }
        
        self.logger.info(f"Added routing rule: {rule_name} -> {target_channel}")
    
    def add_priority_handler(self, priority: EventPriority, handler: Callable):
        """
        Add a priority handler for specific priority events
        
        Args:
            priority: Event priority
            handler: Handler function
        """
        if priority not in self.priority_handlers:
            self.priority_handlers[priority] = []
        
        self.priority_handlers[priority].append(handler)
        self.logger.info(f"Added priority handler for {priority.name}")
    
    async def route_event(self, event: Event) -> bool:
        """
        Route an event based on routing rules and priorities
        
        Args:
            event: Event to route
            
        Returns:
            bool: True if event was routed successfully
        """
        try:
            # Log event
            self._log_event(event)
            
            # Process priority handlers
            await self._process_priority_handlers(event)
            
            # Apply routing rules
            routed = await self._apply_routing_rules(event)
            
            if not routed:
                # If no specific routing rule matches, route based on event type
                await self._route_by_event_type(event)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error routing event {event.id}: {str(e)}")
            return False
    
    async def _process_priority_handlers(self, event: Event):
        """Process priority handlers for the event"""
        if event.priority in self.priority_handlers:
            for handler in self.priority_handlers[event.priority]:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(event)
                    else:
                        handler(event)
                except Exception as e:
                    self.logger.error(f"Error in priority handler: {str(e)}")
    
    async def _apply_routing_rules(self, event: Event) -> bool:
        """Apply routing rules to the event"""
        routed = False
        
        for rule_name, rule in self.routing_rules.items():
            if rule["filter"].matches(event):
                # Transform event if transform function is provided
                if rule["transform_func"]:
                    try:
                        event = rule["transform_func"](event)
                    except Exception as e:
                        self.logger.error(f"Error transforming event for rule {rule_name}: {str(e)}")
                        continue
                
                # Route to target channel
                success = await self.publisher.publish_event(event, rule["target_channel"])
                
                if success:
                    routed = True
                    self.logger.info(f"Event {event.id} routed via rule {rule_name} to {rule['target_channel']}")
                    break
        
        return routed
    
    async def _route_by_event_type(self, event: Event):
        """Route event based on event type"""
        channel_map = {
            EventType.SYSTEM_STARTUP: "system_events",
            EventType.SYSTEM_SHUTDOWN: "system_events",
            EventType.SYSTEM_HEALTH_CHECK: "health_events",
            EventType.RESOURCE_ALERT: "resource_events",
            EventType.AGENT_TASK_SUBMITTED: "agent_events",
            EventType.AGENT_TASK_STARTED: "agent_events",
            EventType.AGENT_TASK_COMPLETED: "agent_events",
            EventType.AGENT_TASK_FAILED: "agent_events",
            EventType.AGENT_COORDINATION: "agent_events",
            EventType.MEMORY_STORED: "memory_events",
            EventType.MEMORY_RETRIEVED: "memory_events",
            EventType.MEMORY_CLEANUP: "memory_events",
            EventType.MODEL_REQUEST: "model_events",
            EventType.MODEL_RESPONSE: "model_events",
            EventType.MODEL_ROUTING: "model_events",
            EventType.DB_CONNECTION: "database_events",
            EventType.DB_QUERY: "database_events",
            EventType.DB_ERROR: "database_events",
            EventType.API_REQUEST: "api_events",
            EventType.API_RESPONSE: "api_events",
            EventType.API_ERROR: "api_events",
            EventType.DOCKER_CONTAINER_START: "docker_events",
            EventType.DOCKER_CONTAINER_STOP: "docker_events",
            EventType.DOCKER_HEALTH_CHECK: "docker_events",
            EventType.TELEGRAM_MESSAGE: "telegram_events",
            EventType.TELEGRAM_COMMAND: "telegram_events",
            EventType.TELEGRAM_ERROR: "telegram_events"
        }
        
        target_channel = channel_map.get(event.event_type, "default_events")
        
        success = await self.publisher.publish_event(event, target_channel)
        if success:
            self.logger.info(f"Event {event.id} routed by type to {target_channel}")
    
    def _log_event(self, event: Event):
        """Log event to history"""
        event_entry = {
            "id": event.id,
            "event_type": event.event_type.value,
            "priority": event.priority.name,
            "source": event.source,
            "target": event.target,
            "timestamp": event.timestamp.isoformat(),
            "data": event.data
        }
        
        self.event_history.append(event_entry)
        
        # Keep history size limited
        if len(self.event_history) > self.max_history:
            self.event_history.pop(0)
    
    def get_routing_rules(self) -> Dict[str, Any]:
        """Get all routing rules"""
        return self.routing_rules
    
    def get_event_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get event history"""
        return self.event_history[-limit:]
    
    def get_event_statistics(self) -> Dict[str, Any]:
        """Get event routing statistics"""
        if not self.event_history:
            return {"total_events": 0}
        
        # Count by event type
        event_type_counts = {}
        for entry in self.event_history:
            event_type = entry["event_type"]
            event_type_counts[event_type] = event_type_counts.get(event_type, 0) + 1
        
        # Count by priority
        priority_counts = {}
        for entry in self.event_history:
            priority = entry["priority"]
            priority_counts[priority] = priority_counts.get(priority, 0) + 1
        
        # Count by source
        source_counts = {}
        for entry in self.event_history:
            source = entry["source"]
            source_counts[source] = source_counts.get(source, 0) + 1
        
        return {
            "total_events": len(self.event_history),
            "event_types": event_type_counts,
            "priorities": priority_counts,
            "sources": source_counts,
            "time_range": {
                "start": self.event_history[0]["timestamp"],
                "end": self.event_history[-1]["timestamp"]
            }
        }
    
    async def broadcast_event(self, event: Event, channels: List[str] = None) -> Dict[str, bool]:
        """
        Broadcast event to multiple channels
        
        Args:
            event: Event to broadcast
            channels: List of channels to broadcast to. If None, broadcast to all relevant channels
            
        Returns:
            Dict mapping channel names to success status
        """
        if not channels:
            # Determine relevant channels based on event type
            channels = self._get_relevant_channels(event.event_type)
        
        results = {}
        
        for channel in channels:
            results[channel] = await self.publisher.publish_event(event, channel)
        
        return results
    
    def _get_relevant_channels(self, event_type: EventType) -> List[str]:
        """Get relevant channels for an event type"""
        channel_map = {
            EventType.SYSTEM_STARTUP: ["system_events", "health_events"],
            EventType.SYSTEM_SHUTDOWN: ["system_events", "health_events"],
            EventType.SYSTEM_HEALTH_CHECK: ["health_events", "system_events"],
            EventType.RESOURCE_ALERT: ["resource_events", "health_events"],
            EventType.AGENT_TASK_SUBMITTED: ["agent_events", "system_events"],
            EventType.AGENT_TASK_STARTED: ["agent_events", "system_events"],
            EventType.AGENT_TASK_COMPLETED: ["agent_events", "system_events"],
            EventType.AGENT_TASK_FAILED: ["agent_events", "health_events"],
            EventType.AGENT_COORDINATION: ["agent_events"],
            EventType.MEMORY_STORED: ["memory_events", "system_events"],
            EventType.MEMORY_RETRIEVED: ["memory_events"],
            EventType.MEMORY_CLEANUP: ["memory_events"],
            EventType.MODEL_REQUEST: ["model_events", "system_events"],
            EventType.MODEL_RESPONSE: ["model_events"],
            EventType.MODEL_ROUTING: ["model_events"],
            EventType.DB_CONNECTION: ["database_events", "system_events"],
            EventType.DB_QUERY: ["database_events"],
            EventType.DB_ERROR: ["database_events", "health_events"],
            EventType.API_REQUEST: ["api_events", "system_events"],
            EventType.API_RESPONSE: ["api_events"],
            EventType.API_ERROR: ["api_events", "health_events"],
            EventType.DOCKER_CONTAINER_START: ["docker_events", "system_events"],
            EventType.DOCKER_CONTAINER_STOP: ["docker_events", "system_events"],
            EventType.DOCKER_HEALTH_CHECK: ["docker_events", "health_events"],
            EventType.TELEGRAM_MESSAGE: ["telegram_events", "system_events"],
            EventType.TELEGRAM_COMMAND: ["telegram_events"],
            EventType.TELEGRAM_ERROR: ["telegram_events", "health_events"]
        }
        
        return channel_map.get(event_type, ["default_events"])
    
    async def create_routing_rule_from_event_type(self, event_type: EventType, 
                                                 target_channel: str, 
                                                 priority: EventPriority = EventPriority.NORMAL,
                                                 rule_name: str = None):
        """
        Create a routing rule from an event type
        
        Args:
            event_type: Event type to create rule for
            target_channel: Target channel
            priority: Route priority
            rule_name: Optional rule name
        """
        if not rule_name:
            rule_name = f"route_{event_type.value}_to_{target_channel}"
        
        filter = EventFilter(event_types=[event_type])
        
        self.add_routing_rule(
            rule_name=rule_name,
            filter=filter,
            target_channel=target_channel,
            priority=priority
        )
        
        self.logger.info(f"Created routing rule for {event_type.value} -> {target_channel}")