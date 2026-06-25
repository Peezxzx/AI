"""
Event System Manager for Atsawin AI Operating System
Coordinates all event system components and provides high-level API
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
from .models import Event, EventType, EventPriority, EventFilter
from .event_publisher import EventPublisher
from .event_subscriber import EventSubscriber
from .event_router import EventRouter
from .event_processor import EventProcessor
from ..redis_client import redis_client

class EventSystemManager:
    """Event system manager for coordinating all event system components"""
    
    def __init__(self, redis_client=None):
        self.logger = logging.getLogger(__name__)
        self.redis_client = redis_client or redis_client
        
        # Initialize components
        self.publisher = EventPublisher(self.redis_client)
        self.subscriber = EventSubscriber(self.redis_client)
        self.router = EventRouter(self.publisher, self.subscriber)
        self.processor = EventProcessor(self.publisher, self.subscriber)
        
        # System state
        self.is_running = False
        self.start_time = None
        self.event_count = 0
        
        # Configuration
        self.config = {
            "enable_processing": True,
            "enable_routing": True,
            "enable_subscription": True,
            "max_retry_attempts": 3,
            "processing_timeout": 30,
            "max_concurrent_processes": 10
        }
        
    async def initialize(self):
        """Initialize the event system"""
        self.logger.info("Initializing Event System Manager")
        
        try:
            # Initialize processor
            if self.config["enable_processing"]:
                await self.processor.create_system_processor()
                await self.processor.create_agent_processor()
                await self.processor.create_memory_processor()
            
            # Setup default routing rules
            await self._setup_default_routing_rules()
            
            # Setup default subscriptions
            if self.config["enable_subscription"]:
                await self._setup_default_subscriptions()
            
            self.logger.info("Event System Manager initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Error initializing Event System Manager: {str(e)}")
            raise
    
    async def start(self):
        """Start the event system"""
        if self.is_running:
            self.logger.warning("Event system is already running")
            return
        
        self.logger.info("Starting Event System Manager")
        self.is_running = True
        self.start_time = datetime.now()
        
        try:
            # Start event processing
            if self.config["enable_processing"]:
                asyncio.create_task(self.processor.process_events())
            
            # Start event listening
            if self.config["enable_subscription"]:
                asyncio.create_task(self.subscriber.start_listening())
            
            self.logger.info("Event System Manager started successfully")
            
        except Exception as e:
            self.logger.error(f"Error starting Event System Manager: {str(e)}")
            self.is_running = False
            raise
    
    async def stop(self):
        """Stop the event system"""
        if not self.is_running:
            self.logger.warning("Event system is not running")
            return
        
        self.logger.info("Stopping Event System Manager")
        
        try:
            # Stop event processing
            if self.config["enable_processing"]:
                # Note: This is a simplified stop - in production you'd want more graceful shutdown
                pass
            
            # Stop event listening
            if self.config["enable_subscription"]:
                await self.subscriber.stop_listening()
            
            self.is_running = False
            self.logger.info("Event System Manager stopped successfully")
            
        except Exception as e:
            self.logger.error(f"Error stopping Event System Manager: {str(e)}")
            raise
    
    async def publish_event(self, event: Event, channel: str = "events") -> bool:
        """
        Publish an event to the system
        
        Args:
            event: Event to publish
            channel: Channel to publish to
            
        Returns:
            bool: True if published successfully
        """
        success = await self.publisher.publish_event(event, channel)
        
        if success:
            self.event_count += 1
            self.logger.debug(f"Event published: {event.id} ({event.event_type.value})")
        
        return success
    
    async def submit_event_for_processing(self, event: Event, 
                                       priority: EventPriority = None) -> bool:
        """
        Submit an event for processing
        
        Args:
            event: Event to process
            priority: Processing priority
            
        Returns:
            bool: True if event was submitted successfully
        """
        if not self.config["enable_processing"]:
            # If processing is disabled, just publish the event
            return await self.publish_event(event)
        
        return await self.processor.submit_event(event, priority)
    
    async def create_system_event(self, event_type: EventType, source: str,
                                data: Dict[str, Any] = None,
                                priority: EventPriority = EventPriority.NORMAL,
                                channel: str = "events") -> bool:
        """
        Create and publish a system event
        
        Args:
            event_type: Type of event
            source: Source of the event
            data: Event data
            priority: Event priority
            channel: Channel to publish to
            
        Returns:
            bool: True if event was created and published successfully
        """
        event = Event(
            event_type=event_type,
            source=source,
            priority=priority,
            data=data or {}
        )
        
        return await self.publish_event(event, channel)
    
    async def create_agent_task_event(self, task_id: str, agent_type: str,
                                    status: str, result: Any = None,
                                    priority: EventPriority = EventPriority.NORMAL) -> bool:
        """
        Create and publish an agent task event
        
        Args:
            task_id: ID of the task
            agent_type: Type of agent
            status: Task status
            result: Task result
            priority: Event priority
            
        Returns:
            bool: True if event was created and published successfully
        """
        return await self.publisher.publish_agent_task_event(
            task_id, agent_type, status, result, priority
        )
    
    async def create_memory_event(self, operation: str, key: str,
                                memory_type: str = None, user_id: str = None,
                                result: Any = None) -> bool:
        """
        Create and publish a memory event
        
        Args:
            operation: Memory operation
            key: Memory key
            memory_type: Type of memory
            user_id: User ID
            result: Operation result
            
        Returns:
            bool: True if event was created and published successfully
        """
        return await self.publisher.publish_memory_event(
            operation, key, memory_type, user_id, result
        )
    
    async def create_api_event(self, method: str, endpoint: str,
                             status_code: int, response_time: float,
                             user_id: str = None) -> bool:
        """
        Create and publish an API event
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            status_code: HTTP status code
            response_time: Response time in seconds
            user_id: User ID
            
        Returns:
            bool: True if event was created and published successfully
        """
        return await self.publisher.publish_api_event(
            method, endpoint, status_code, response_time, user_id
        )
    
    async def create_resource_alert(self, resource_type: str, current_usage: float,
                                  threshold: float, message: str) -> bool:
        """
        Create and publish a resource alert event
        
        Args:
            resource_type: Type of resource
            current_usage: Current usage percentage
            threshold: Alert threshold
            message: Alert message
            
        Returns:
            bool: True if event was created and published successfully
        """
        return await self.publisher.publish_resource_alert(
            resource_type, current_usage, threshold, message
        )
    
    async def create_health_check(self, component: str, status: str,
                                metrics: Dict[str, Any] = None) -> bool:
        """
        Create and publish a health check event
        
        Args:
            component: Component name
            status: Health status
            metrics: Health metrics
            
        Returns:
            bool: True if event was created and published successfully
        """
        return await self.publisher.publish_health_check(
            component, status, metrics
        )
    
    async def add_routing_rule(self, rule_name: str, event_types: List[EventType],
                             target_channel: str, priority: EventPriority = EventPriority.NORMAL):
        """
        Add a routing rule
        
        Args:
            rule_name: Name of the routing rule
            event_types: List of event types to route
            target_channel: Target channel
            priority: Route priority
        """
        filter = EventFilter(event_types=event_types)
        
        self.router.add_routing_rule(
            rule_name=rule_name,
            filter=filter,
            target_channel=target_channel,
            priority=priority
        )
    
    async def register_event_handler(self, event_type: EventType, handler: Callable):
        """
        Register an event handler
        
        Args:
            event_type: Event type to handle
            handler: Handler function
        """
        self.processor.register_handler(event_type, handler)
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get system status"""
        return {
            "is_running": self.is_running,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "event_count": self.event_count,
            "processing_enabled": self.config["enable_processing"],
            "routing_enabled": self.config["enable_routing"],
            "subscription_enabled": self.config["enable_subscription"],
            "processor_stats": self.processor.get_processing_stats(),
            "routing_rules": self.router.get_routing_rules(),
            "subscriber_info": self.subscriber.get_subscription_info()
        }
    
    async def get_event_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get event history"""
        return self.router.get_event_history(limit)
    
    async def get_event_statistics(self) -> Dict[str, Any]:
        """Get event statistics"""
        return self.router.get_event_statistics()
    
    async def _setup_default_routing_rules(self):
        """Setup default routing rules"""
        # System events
        await self.add_routing_rule(
            rule_name="system_to_health",
            event_types=[EventType.SYSTEM_HEALTH_CHECK, EventType.RESOURCE_ALERT],
            target_channel="health_events",
            priority=EventPriority.HIGH
        )
        
        # Agent events
        await self.add_routing_rule(
            rule_name="agent_to_processing",
            event_types=[EventType.AGENT_TASK_SUBMITTED, EventType.AGENT_TASK_STARTED],
            target_channel="agent_events",
            priority=EventPriority.NORMAL
        )
        
        # Memory events
        await self.add_routing_rule(
            rule_name="memory_to_storage",
            event_types=[EventType.MEMORY_STORED, EventType.MEMORY_RETRIEVED],
            target_channel="memory_events",
            priority=EventPriority.NORMAL
        )
        
        # API events
        await self.add_routing_rule(
            rule_name="api_to_monitoring",
            event_types=[EventType.API_REQUEST, EventType.API_RESPONSE, EventType.API_ERROR],
            target_channel="api_events",
            priority=EventPriority.NORMAL
        )
        
        self.logger.info("Default routing rules setup complete")
    
    async def _setup_default_subscriptions(self):
        """Setup default subscriptions"""
        # Subscribe to system events
        await self.subscriber.subscribe(
            channel="system_events",
            filter=EventFilter(event_types=[
                EventType.SYSTEM_STARTUP,
                EventType.SYSTEM_SHUTDOWN,
                EventType.SYSTEM_HEALTH_CHECK
            ])
        )
        
        # Subscribe to agent events
        await self.subscriber.subscribe(
            channel="agent_events",
            filter=EventFilter(event_types=[
                EventType.AGENT_TASK_SUBMITTED,
                EventType.AGENT_TASK_STARTED,
                EventType.AGENT_TASK_COMPLETED,
                EventType.AGENT_TASK_FAILED
            ])
        )
        
        # Subscribe to memory events
        await self.subscriber.subscribe(
            channel="memory_events",
            filter=EventFilter(event_types=[
                EventType.MEMORY_STORED,
                EventType.MEMORY_RETRIEVED,
                EventType.MEMORY_CLEANUP
            ])
        )
        
        # Subscribe to resource events
        await self.subscriber.subscribe(
            channel="resource_events",
            filter=EventFilter(event_types=[EventType.RESOURCE_ALERT])
        )
        
        # Health check subscription
        await self.subscriber.subscribe(
            channel="health_events"
        )
        
        self.logger.info("Default subscriptions setup complete")
    
    async def broadcast_system_event(self, event_type: EventType, source: str,
                                  data: Dict[str, Any] = None,
                                  priority: EventPriority = EventPriority.NORMAL) -> Dict[str, bool]:
        """
        Broadcast a system event to multiple channels
        
        Args:
            event_type: Type of event
            source: Source of the event
            data: Event data
            priority: Event priority
            
        Returns:
            Dict mapping channel names to success status
        """
        event = Event(
            event_type=event_type,
            source=source,
            priority=priority,
            data=data or {}
        )
        
        return await self.router.broadcast_event(event)
    
    async def create_event_from_dict(self, event_data: Dict[str, Any]) -> Event:
        """
        Create an event from dictionary data
        
        Args:
            event_data: Event data dictionary
            
        Returns:
            Event: Created event
        """
        return Event.from_dict(event_data)
    
    def configure(self, config: Dict[str, Any]):
        """
        Configure the event system
        
        Args:
            config: Configuration dictionary
        """
        self.config.update(config)
        
        # Update processor config
        if "max_retry_attempts" in config:
            self.processor.max_retry_attempts = config["max_retry_attempts"]
        
        if "processing_timeout" in config:
            self.processor.processing_timeout = config["processing_timeout"]
        
        if "max_concurrent_processes" in config:
            self.processor.max_concurrent_processes = config["max_concurrent_processes"]
        
        self.logger.info(f"Event system configured: {config}")

# Global event system manager instance
event_system_manager = EventSystemManager()