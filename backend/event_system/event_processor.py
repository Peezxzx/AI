"""
Event Processor for Atsawin AI Event System
Processes events with retry logic, error handling, and async execution
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Callable, Type
from datetime import datetime, timedelta
from enum import Enum
from .models import Event, EventType, EventPriority
from .event_publisher import EventPublisher
from .event_subscriber import EventSubscriber

class ProcessingStatus(Enum):
    """Event processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    CANCELLED = "cancelled"

class EventProcessor:
    """Event processor for async event processing"""
    
    def __init__(self, publisher: EventPublisher, subscriber: EventSubscriber):
        self.logger = logging.getLogger(__name__)
        self.publisher = publisher
        self.subscriber = subscriber
        self.event_queue = asyncio.Queue()
        self.processing_events = {}
        self.completed_events = []
        self.failed_events = []
        self.event_handlers = {}
        self.processing_status = {}
        self.max_retry_delay = 300  # 5 minutes max retry delay
        self.processing_timeout = 30  # 30 seconds processing timeout
        self.max_concurrent_processes = 10
        
        # Processing statistics
        self.stats = {
            "total_processed": 0,
            "total_succeeded": 0,
            "total_failed": 0,
            "total_retries": 0,
            "processing_time_avg": 0.0
        }
        
    def register_handler(self, event_type: EventType, handler: Callable):
        """
        Register an event handler for a specific event type
        
        Args:
            event_type: Event type to handle
            handler: Handler function
        """
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        
        self.event_handlers[event_type].append(handler)
        self.logger.info(f"Registered handler for {event_type.value}")
    
    async def submit_event(self, event: Event, priority: EventPriority = None) -> bool:
        """
        Submit an event for processing
        
        Args:
            event: Event to process
            priority: Processing priority (overrides event priority)
            
        Returns:
            bool: True if event was submitted successfully
        """
        try:
            # Set processing priority
            if priority:
                event.priority = priority
            
            # Add to queue with priority ordering
            await self.event_queue.put(event)
            
            # Update processing status
            self.processing_status[event.id] = {
                "status": ProcessingStatus.PENDING,
                "submitted_at": datetime.now(),
                "started_at": None,
                "completed_at": None,
                "retry_count": 0
            }
            
            self.logger.info(f"Event {event.id} submitted for processing")
            return True
            
        except Exception as e:
            self.logger.error(f"Error submitting event {event.id}: {str(e)}")
            return False
    
    async def process_events(self):
        """Process events from the queue"""
        self.logger.info("Starting event processor")
        
        while True:
            try:
                # Get next event from queue
                event = await self.event_queue.get()
                
                # Check if we have capacity to process
                if len(self.processing_events) >= self.max_concurrent_processes:
                    # Put back in queue with small delay
                    await asyncio.sleep(0.1)
                    await self.event_queue.put(event)
                    continue
                
                # Process the event
                asyncio.create_task(self._process_event(event))
                
            except Exception as e:
                self.logger.error(f"Error in event processing loop: {str(e)}")
                await asyncio.sleep(1)
    
    async def _process_event(self, event: Event):
        """Process a single event"""
        event_id = event.id
        processing_info = self.processing_status.get(event_id)
        
        if not processing_info:
            self.logger.error(f"No processing info for event {event_id}")
            return
        
        try:
            # Update processing status
            processing_info["status"] = ProcessingStatus.PROCESSING
            processing_info["started_at"] = datetime.now()
            self.processing_events[event_id] = event
            
            self.logger.info(f"Processing event {event_id}: {event.event_type.value}")
            
            # Get handlers for this event type
            handlers = self.event_handlers.get(event.event_type, [])
            
            if not handlers:
                # No handler registered, try to route instead
                await self._route_event(event)
                processing_info["status"] = ProcessingStatus.COMPLETED
                self.stats["total_processed"] += 1
                self.stats["total_succeeded"] += 1
                return
            
            # Process with each handler
            for handler in handlers:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await asyncio.wait_for(
                            handler(event),
                            timeout=self.processing_timeout
                        )
                    else:
                        handler(event)
                        
                except asyncio.TimeoutError:
                    self.logger.warning(f"Handler timeout for event {event_id}")
                    raise Exception("Handler timeout")
                except Exception as e:
                    self.logger.error(f"Handler error for event {event_id}: {str(e)}")
                    raise
            
            # Event processed successfully
            processing_info["status"] = ProcessingStatus.COMPLETED
            processing_info["completed_at"] = datetime.now()
            
            # Remove from processing events
            if event_id in self.processing_events:
                del self.processing_events[event_id]
            
            # Add to completed events
            self.completed_events.append({
                "event_id": event_id,
                "event_type": event.event_type.value,
                "completed_at": datetime.now().isoformat(),
                "processing_time": (processing_info["completed_at"] - processing_info["started_at"]).total_seconds()
            })
            
            # Update stats
            self.stats["total_processed"] += 1
            self.stats["total_succeeded"] += 1
            
            # Clean up old completed events
            await self._cleanup_completed_events()
            
            self.logger.info(f"Event {event_id} processed successfully")
            
        except Exception as e:
            # Event processing failed
            self.logger.error(f"Event {event_id} processing failed: {str(e)}")
            
            # Check if we should retry
            if event.should_retry():
                await self._retry_event(event, processing_info)
            else:
                # Mark as failed
                processing_info["status"] = ProcessingStatus.FAILED
                processing_info["completed_at"] = datetime.now()
                
                # Add to failed events
                self.failed_events.append({
                    "event_id": event_id,
                    "event_type": event.event_type.value,
                    "error": str(e),
                    "failed_at": datetime.now().isoformat(),
                    "retry_count": event.retry_count
                })
                
                # Remove from processing events
                if event_id in self.processing_events:
                    del self.processing_events[event_id]
                
                # Update stats
                self.stats["total_processed"] += 1
                self.stats["total_failed"] += 1
                
                # Publish failure event
                await self.publisher.publish_system_event(
                    event_type=EventType.RESOURCE_ALERT,
                    source="event_processor",
                    data={
                        "failed_event_id": event_id,
                        "event_type": event.event_type.value,
                        "error": str(e),
                        "retry_count": event.retry_count
                    },
                    priority=EventPriority.HIGH,
                    channel="error_events"
                )
    
    async def _retry_event(self, event: Event, processing_info: Dict[str, Any]):
        """Retry a failed event"""
        processing_info["retry_count"] += 1
        processing_info["status"] = ProcessingStatus.RETRYING
        
        # Calculate retry delay with exponential backoff
        base_delay = 1  # 1 second base delay
        max_delay = min(self.max_retry_delay, base_delay * (2 ** processing_info["retry_count"]))
        retry_delay = min(max_delay, base_delay * (2 ** processing_info["retry_count"]))
        
        self.logger.info(f"Retrying event {event.id} in {retry_delay} seconds (attempt {processing_info['retry_count']})")
        
        # Schedule retry
        await asyncio.sleep(retry_delay)
        
        # Reset event retry count
        event.increment_retry()
        
        # Put back in queue
        await self.event_queue.put(event)
        
        # Update stats
        self.stats["total_retries"] += 1
        
        # Reset processing status
        processing_info["status"] = ProcessingStatus.PENDING
    
    async def _route_event(self, event: Event):
        """Route event if no handler is registered"""
        # This could be extended with more sophisticated routing logic
        self.logger.info(f"Routing event {event.id} (no handler registered)")
        
        # For now, just publish to a default channel
        await self.publisher.publish_event(event, "unprocessed_events")
    
    async def _cleanup_completed_events(self, max_age_hours: int = 24):
        """Clean up old completed events"""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        
        # Clean up completed events
        self.completed_events = [
            e for e in self.completed_events
            if datetime.fromisoformat(e["completed_at"]) >= cutoff_time
        ]
        
        # Clean up failed events
        self.failed_events = [
            f for f in self.failed_events
            if datetime.fromisoformat(f["failed_at"]) >= cutoff_time
        ]
        
        # Clean up old processing statuses
        old_statuses = [
            event_id for event_id, status in self.processing_status.items()
            if status["status"] in [ProcessingStatus.COMPLETED, ProcessingStatus.FAILED]
            and status["completed_at"]
            and status["completed_at"] < cutoff_time
        ]
        
        for event_id in old_statuses:
            del self.processing_status[event_id]
        
        self.logger.info(f"Cleaned up old events. Remaining: {len(self.completed_events)} completed, {len(self.failed_events)} failed")
    
    async def cancel_event(self, event_id: str) -> bool:
        """
        Cancel an event being processed
        
        Args:
            event_id: Event ID to cancel
            
        Returns:
            bool: True if event was cancelled successfully
        """
        processing_info = self.processing_status.get(event_id)
        
        if not processing_info:
            return False
        
        if processing_info["status"] == ProcessingStatus.PENDING:
            # Remove from queue (this is tricky with asyncio.Queue)
            processing_info["status"] = ProcessingStatus.CANCELLED
            return True
        
        elif processing_info["status"] == ProcessingStatus.PROCESSING:
            # Mark as cancelled, but it might still be processing
            processing_info["status"] = ProcessingStatus.CANCELLED
            return True
        
        return False
    
    def get_processing_status(self, event_id: str) -> Optional[Dict[str, Any]]:
        """Get processing status for an event"""
        return self.processing_status.get(event_id)
    
    def get_queue_size(self) -> int:
        """Get current queue size"""
        return self.event_queue.qsize()
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get processing statistics"""
        return {
            **self.stats,
            "queue_size": self.get_queue_size(),
            "currently_processing": len(self.processing_events),
            "completed_events": len(self.completed_events),
            "failed_events": len(self.failed_events),
            "processing_status": len(self.processing_status)
        }
    
    async def create_system_processor(self):
        """Create and register system event handlers"""
        # System startup handler
        async def handle_system_startup(event: Event):
            self.logger.info(f"System startup detected: {event.data}")
            # Here you could add system initialization logic
        
        # System shutdown handler
        async def handle_system_shutdown(event: Event):
            self.logger.info(f"System shutdown detected: {event.data}")
            # Here you could add system cleanup logic
        
        # Resource alert handler
        async def handle_resource_alert(event: Event):
            self.logger.warning(f"Resource alert: {event.data}")
            # Here you could add resource alert handling logic
        
        # Register handlers
        self.register_handler(EventType.SYSTEM_STARTUP, handle_system_startup)
        self.register_handler(EventType.SYSTEM_SHUTDOWN, handle_system_shutdown)
        self.register_handler(EventType.RESOURCE_ALERT, handle_resource_alert)
        
        self.logger.info("System event processor created")
    
    async def create_agent_processor(self):
        """Create and register agent event handlers"""
        # Task submitted handler
        async def handle_task_submitted(event: Event):
            self.logger.info(f"Agent task submitted: {event.data}")
            # Here you could add task initialization logic
        
        # Task completed handler
        async def handle_task_completed(event: Event):
            self.logger.info(f"Agent task completed: {event.data}")
            # Here you could add task completion logic
        
        # Task failed handler
        async def handle_task_failed(event: Event):
            self.logger.error(f"Agent task failed: {event.data}")
            # Here you could add task failure handling logic
        
        # Register handlers
        self.register_handler(EventType.AGENT_TASK_SUBMITTED, handle_task_submitted)
        self.register_handler(EventType.AGENT_TASK_COMPLETED, handle_task_completed)
        self.register_handler(EventType.AGENT_TASK_FAILED, handle_task_failed)
        
        self.logger.info("Agent event processor created")
    
    async def create_memory_processor(self):
        """Create and register memory event handlers"""
        # Memory stored handler
        async def handle_memory_stored(event: Event):
            self.logger.info(f"Memory stored: {event.data}")
            # Here you could add memory storage completion logic
        
        # Memory retrieved handler
        async def handle_memory_retrieved(event: Event):
            self.logger.info(f"Memory retrieved: {event.data}")
            # Here you could add memory retrieval logic
        
        # Register handlers
        self.register_handler(EventType.MEMORY_STORED, handle_memory_stored)
        self.register_handler(EventType.MEMORY_RETRIEVED, handle_memory_retrieved)
        
        self.logger.info("Memory event processor created")