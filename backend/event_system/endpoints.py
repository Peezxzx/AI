"""
Event System API Endpoints for Atsawin AI Operating System
REST API endpoints for event system management
"""

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from typing import List, Dict, Any, Optional
from datetime import datetime
from ..auth import get_current_user, admin_required, trader_required
from .models import Event, EventType, EventPriority, EventFilter
from .event_system_manager import event_system_manager

router = APIRouter()

@router.get("/events/status")
async def get_event_system_status(current_user: dict = Depends(get_current_user)):
    """Get event system status"""
    try:
        status = await event_system_manager.get_system_status()
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/events")
async def create_event(
    event_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """Create and publish an event"""
    try:
        event = await event_system_manager.create_event_from_dict(event_data)
        success = await event_system_manager.publish_event(event)
        
        if success:
            return {"message": "Event published successfully", "event_id": event.id}
        else:
            raise HTTPException(status_code=500, detail="Failed to publish event")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/events/system")
async def create_system_event(
    event_type: str,
    source: str,
    data: dict = None,
    priority: str = "NORMAL",
    current_user: dict = Depends(get_current_user)
):
    """Create a system event"""
    try:
        event_type_enum = EventType(event_type.upper())
        priority_enum = EventPriority(priority.upper())
        
        success = await event_system_manager.create_system_event(
            event_type=event_type_enum,
            source=source,
            data=data or {},
            priority=priority_enum
        )
        
        if success:
            return {"message": "System event created successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to create system event")
            
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid event type or priority: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/events/agent-task")
async def create_agent_task_event(
    task_id: str,
    agent_type: str,
    status: str,
    result: Any = None,
    priority: str = "NORMAL",
    current_user: dict = Depends(trader_required)
):
    """Create an agent task event"""
    try:
        priority_enum = EventPriority(priority.upper())
        
        success = await event_system_manager.create_agent_task_event(
            task_id=task_id,
            agent_type=agent_type,
            status=status,
            result=result,
            priority=priority_enum
        )
        
        if success:
            return {"message": "Agent task event created successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to create agent task event")
            
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid priority: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/events/memory")
async def create_memory_event(
    operation: str,
    key: str,
    memory_type: str = None,
    user_id: str = None,
    result: Any = None,
    current_user: dict = Depends(get_current_user)
):
    """Create a memory event"""
    try:
        success = await event_system_manager.create_memory_event(
            operation=operation,
            key=key,
            memory_type=memory_type,
            user_id=user_id,
            result=result
        )
        
        if success:
            return {"message": "Memory event created successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to create memory event")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/events/api")
async def create_api_event(
    method: str,
    endpoint: str,
    status_code: int,
    response_time: float,
    user_id: str = None,
    current_user: dict = Depends(get_current_user)
):
    """Create an API event"""
    try:
        success = await event_system_manager.create_api_event(
            method=method,
            endpoint=endpoint,
            status_code=status_code,
            response_time=response_time,
            user_id=user_id
        )
        
        if success:
            return {"message": "API event created successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to create API event")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/events/resource-alert")
async def create_resource_alert(
    resource_type: str,
    current_usage: float,
    threshold: float,
    message: str,
    current_user: dict = Depends(admin_required)
):
    """Create a resource alert event"""
    try:
        success = await event_system_manager.create_resource_alert(
            resource_type=resource_type,
            current_usage=current_usage,
            threshold=threshold,
            message=message
        )
        
        if success:
            return {"message": "Resource alert created successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to create resource alert")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/events/health-check")
async def create_health_check(
    component: str,
    status: str,
    metrics: dict = None,
    current_user: dict = Depends(get_current_user)
):
    """Create a health check event"""
    try:
        success = await event_system_manager.create_health_check(
            component=component,
            status=status,
            metrics=metrics or {}
        )
        
        if success:
            return {"message": "Health check event created successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to create health check event")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/events")
async def get_events(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    event_type: str = None,
    source: str = None,
    priority: str = None,
    current_user: dict = Depends(get_current_user)
):
    """Get event history"""
    try:
        # Get all events first
        all_events = await event_system_manager.get_event_history(limit + offset)
        
        # Apply filters
        filtered_events = all_events[offset:]
        
        if event_type:
            filtered_events = [e for e in filtered_events if e.get("event_type") == event_type]
        
        if source:
            filtered_events = [e for e in filtered_events if source in e.get("source", "")]
        
        if priority:
            filtered_events = [e for e in filtered_events if e.get("priority") == priority]
        
        return {
            "events": filtered_events,
            "total": len(filtered_events),
            "offset": offset,
            "limit": limit
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/events/statistics")
async def get_event_statistics(current_user: dict = Depends(get_current_user)):
    """Get event statistics"""
    try:
        stats = await event_system_manager.get_event_statistics()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/events/routing-rules")
async def add_routing_rule(
    rule_name: str,
    event_types: List[str],
    target_channel: str,
    priority: str = "NORMAL",
    current_user: dict = Depends(admin_required)
):
    """Add a routing rule"""
    try:
        # Convert string types to enums
        event_type_enums = [EventType(event_type.upper()) for event_type in event_types]
        priority_enum = EventPriority(priority.upper())
        
        await event_system_manager.add_routing_rule(
            rule_name=rule_name,
            event_types=event_type_enums,
            target_channel=target_channel,
            priority=priority_enum
        )
        
        return {"message": "Routing rule added successfully"}
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid event type or priority: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/events/routing-rules")
async def get_routing_rules(current_user: dict = Depends(get_current_user)):
    """Get all routing rules"""
    try:
        rules = await event_system_manager.router.get_routing_rules()
        return rules
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/events/routing-rules/{rule_name}")
async def delete_routing_rule(
    rule_name: str,
    current_user: dict = Depends(admin_required)
):
    """Delete a routing rule"""
    try:
        # Note: This would require implementing delete functionality in EventRouter
        # For now, we'll just return a placeholder response
        return {"message": f"Routing rule '{rule_name}' deletion not yet implemented"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/events/processor-stats")
async def get_processor_stats(current_user: dict = Depends(get_current_user)):
    """Get event processor statistics"""
    try:
        stats = await event_system_manager.processor.get_processing_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/events/subscriptions")
async def get_subscriptions(current_user: dict = Depends(get_current_user)):
    """Get event subscription information"""
    try:
        info = await event_system_manager.subscriber.get_subscription_info()
        return info
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/events/submit")
async def submit_event_for_processing(
    event_data: dict,
    priority: str = "NORMAL",
    current_user: dict = Depends(get_current_user)
):
    """Submit an event for processing"""
    try:
        event = await event_system_manager.create_event_from_dict(event_data)
        priority_enum = EventPriority(priority.upper())
        
        success = await event_system_manager.submit_event_for_processing(
            event=event,
            priority=priority_enum
        )
        
        if success:
            return {"message": "Event submitted for processing", "event_id": event.id}
        else:
            raise HTTPException(status_code=500, detail="Failed to submit event for processing")
            
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid priority: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/events/broadcast")
async def broadcast_system_event(
    event_type: str,
    source: str,
    data: dict = None,
    priority: str = "NORMAL",
    current_user: dict = Depends(admin_required)
):
    """Broadcast a system event to multiple channels"""
    try:
        event_type_enum = EventType(event_type.upper())
        priority_enum = EventPriority(priority.upper())
        
        results = await event_system_manager.broadcast_system_event(
            event_type=event_type_enum,
            source=source,
            data=data or {},
            priority=priority_enum
        )
        
        return {
            "message": "System event broadcast",
            "results": results
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid event type or priority: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/event-types")
async def get_event_types(current_user: dict = Depends(get_current_user)):
    """Get all available event types"""
    try:
        event_types = [event_type.value for event_type in EventType]
        return {"event_types": event_types}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/event-priorities")
async def get_event_priorities(current_user: dict = Depends(get_current_user)):
    """Get all available event priorities"""
    try:
        priorities = [priority.value for priority in EventPriority]
        return {"priorities": priorities}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))