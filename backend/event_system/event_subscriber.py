"""
Event Subscriber for Atsawin AI Event System
Subscribes to events from Redis message queue
"""

import json
import logging
import asyncio
from typing import List, Dict, Any, Callable, Optional
from datetime import datetime
from .models import Event, EventType, EventPriority, EventFilter
from redis_client import redis_client

class EventSubscriber:
    """Event subscriber for subscribing to events from Redis"""
    
    def __init__(self, redis_client=None):
        self.logger = logging.getLogger(__name__)
        self.redis_client = redis_client or redis_client
        self.subscribers = {}
        self.event_handlers = {}
        self.is_running = False
        self.subscribed_channels = set()
        
    async def subscribe(self, channel: str, filter: EventFilter = None, 
                       handler: Callable = None) -> str:
        """
        Subscribe to a Redis channel with optional event filtering
        
        Args:
            channel: Redis channel to subscribe to
            filter: Event filter for filtering events
            handler: Event handler function
            
        Returns:
            str: Subscription ID
        """
        if channel not in self.subscribers:
            self.subscribers[channel] = {
                "filter": filter,
                "handlers": [],
                "active": False
            }
        
        subscription_id = f"{channel}_{datetime.now().timestamp()}"
        
        if handler:
            self.subscribers[channel]["handlers"].append(handler)
            
        # Add to event handlers if filter is provided
        if filter:
            if subscription_id not in self.event_handlers:
                self.event_handlers[subscription_id] = []
            self.event_handlers[subscription_id].append(filter)
        
        self.logger.info(f"Subscribed to channel {channel} with subscription ID {subscription_id}")
        return subscription_id
    
    async def unsubscribe(self, subscription_id: str) -> bool:
        """
        Unsubscribe from a channel
        
        Args:
            subscription_id: Subscription ID to unsubscribe
            
        Returns:
            bool: True if unsubscribed successfully
        """
        # Remove from event handlers
        if subscription_id in self.event_handlers:
            del self.event_handlers[subscription_id]
            self.logger.info(f"Unsubscribed {subscription_id} from event handlers")
            
        # Check if this was the last handler for any channel
        for channel, sub_info in self.subscribers.items():
            # Remove handlers associated with this subscription
            sub_info["handlers"] = [
                h for h in sub_info["handlers"] 
                if hasattr(h, '__name__') and subscription_id not in h.__name__
            ]
            
            # If no handlers left, mark as inactive
            if not sub_info["handlers"]:
                sub_info["active"] = False
                if channel in self.subscribed_channels:
                    await self._unsubscribe_from_redis(channel)
                    self.subscribed_channels.remove(channel)
                    self.logger.info(f"Unsubscribed from Redis channel {channel}")
        
        return True
    
    async def start_listening(self, channels: List[str] = None):
        """
        Start listening for events on specified channels
        
        Args:
            channels: List of channels to listen on. If None, listen to all subscribed channels
        """
        if not channels:
            channels = [ch for ch, sub_info in self.subscribers.items() if sub_info["active"]]
        
        if not channels:
            self.logger.warning("No active channels to listen on")
            return
        
        self.is_running = True
        self.logger.info(f"Starting event listener on channels: {channels}")
        
        # Subscribe to Redis channels
        for channel in channels:
            if channel not in self.subscribed_channels:
                await self._subscribe_to_redis(channel)
                self.subscribed_channels.add(channel)
                self.subscribers[channel]["active"] = True
        
        # Start listening loop
        await self._listen_for_events()
    
    async def stop_listening(self):
        """Stop listening for events"""
        self.is_running = False
        
        # Unsubscribe from all Redis channels
        for channel in list(self.subscribed_channels):
            await self._unsubscribe_from_redis(channel)
        
        self.subscribed_channels.clear()
        self.logger.info("Stopped event listener")
    
    async def _subscribe_to_redis(self, channel: str):
        """Subscribe to Redis channel"""
        if self.redis_client:
            try:
                # Create a pubsub instance
                self.pubsub = self.redis_client.pubsub()
                await self.pubsub.subscribe(channel)
                self.logger.info(f"Subscribed to Redis channel {channel}")
            except Exception as e:
                self.logger.error(f"Failed to subscribe to Redis channel {channel}: {str(e)}")
    
    async def _unsubscribe_from_redis(self, channel: str):
        """Unsubscribe from Redis channel"""
        if hasattr(self, 'pubsub') and self.pubsub:
            try:
                await self.pubsub.unsubscribe(channel)
                self.logger.info(f"Unsubscribed from Redis channel {channel}")
            except Exception as e:
                self.logger.error(f"Failed to unsubscribe from Redis channel {channel}: {str(e)}")
    
    async def _listen_for_events(self):
        """Listen for events from Redis"""
        while self.is_running:
            try:
                if hasattr(self, 'pubsub') and self.pubsub:
                    # Wait for message with timeout
                    message = await asyncio.wait_for(self.pubsub.get_message(timeout=1.0), timeout=1.0)
                    
                    if message and message['type'] == 'message':
                        await self._process_redis_message(message)
                        
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                self.logger.error(f"Error in event listener: {str(e)}")
                await asyncio.sleep(1)  # Prevent tight loop on errors
    
    async def _process_redis_message(self, message: Dict[str, Any]):
        """Process a message from Redis"""
        try:
            channel = message['channel']
            data = json.loads(message['data'])
            
            # Create event from data
            event = Event.from_dict(data)
            
            # Process event through filters and handlers
            await self._process_event(event, channel)
            
        except Exception as e:
            self.logger.error(f"Error processing Redis message: {str(e)}")
    
    async def _process_event(self, event: Event, channel: str):
        """Process an event through filters and handlers"""
        # Get subscription info for this channel
        if channel not in self.subscribers:
            return
        
        sub_info = self.subscribers[channel]
        
        # Check if event matches any filter
        for subscription_id, filters in self.event_handlers.items():
            for filter_obj in filters:
                if filter_obj.matches(event):
                    # Process through handlers for this subscription
                    for handler in sub_info["handlers"]:
                        try:
                            if asyncio.iscoroutinefunction(handler):
                                await handler(event)
                            else:
                                handler(event)
                        except Exception as e:
                            self.logger.error(f"Error in event handler {handler.__name__}: {str(e)}")
    
    async def add_handler(self, subscription_id: str, handler: Callable):
        """
        Add a handler to an existing subscription
        
        Args:
            subscription_id: Subscription ID
            handler: Event handler function
        """
        # Find the channel for this subscription
        for channel, sub_info in self.subscribers.items():
            if subscription_id in f"{channel}_{datetime.now().timestamp()}":
                sub_info["handlers"].append(handler)
                self.logger.info(f"Added handler to subscription {subscription_id}")
                break
    
    def register_system_handler(self, handler: Callable, filter: EventFilter = None):
        """
        Register a system-wide event handler
        
        Args:
            handler: Handler function
            filter: Optional event filter
        """
        subscription_id = f"system_handler_{datetime.now().timestamp()}"
        
        if subscription_id not in self.event_handlers:
            self.event_handlers[subscription_id] = []
        
        if filter:
            self.event_handlers[subscription_id].append(filter)
        
        self.logger.info(f"Registered system handler: {handler.__name__}")
        return subscription_id
    
    async def handle_agent_events(self, event: Event):
        """Handle agent-related events"""
        if event.event_type in [
            EventType.AGENT_TASK_SUBMITTED,
            EventType.AGENT_TASK_STARTED,
            EventType.AGENT_TASK_COMPLETED,
            EventType.AGENT_TASK_FAILED,
            EventType.AGENT_COORDINATION
        ]:
            self.logger.info(f"Processing agent event: {event.event_type.value} - {event.data}")
            # Here you could add specific agent event processing logic
    
    async def handle_memory_events(self, event: Event):
        """Handle memory-related events"""
        if event.event_type in [EventType.MEMORY_STORED, EventType.MEMORY_RETRIEVED, EventType.MEMORY_CLEANUP]:
            self.logger.info(f"Processing memory event: {event.event_type.value} - {event.data}")
            # Here you could add specific memory event processing logic
    
    async def handle_resource_events(self, event: Event):
        """Handle resource-related events"""
        if event.event_type == EventType.RESOURCE_ALERT:
            self.logger.warning(f"Resource alert: {event.data}")
            # Here you could add specific resource alert processing logic
    
    async def handle_api_events(self, event: Event):
        """Handle API-related events"""
        if event.event_type in [EventType.API_REQUEST, EventType.API_RESPONSE, EventType.API_ERROR]:
            self.logger.info(f"Processing API event: {event.event_type.value} - {event.data}")
            # Here you could add specific API event processing logic
    
    async def handle_health_events(self, event: Event):
        """Handle health check events"""
        if event.event_type == EventType.SYSTEM_HEALTH_CHECK:
            status = event.data.get("status", "unknown")
            self.logger.info(f"Health check: {event.data.get('component', 'unknown')} - {status}")
            # Here you could add specific health check processing logic
    
    def get_subscription_info(self) -> Dict[str, Any]:
        """Get information about active subscriptions"""
        return {
            "subscribers": self.subscribers,
            "event_handlers": self.event_handlers,
            "is_running": self.is_running,
            "subscribed_channels": list(self.subscribed_channels)
        }