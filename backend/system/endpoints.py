from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from system.resource_manager import (
    SystemTask, TaskPriority, TaskStatus, ResourceType,
    resource_manager, ResourceManager
)
from auth import get_current_user, admin_required, trader_required

router = APIRouter(prefix="/system", tags=["system"])

@router.get("/status")
async def get_system_status(current_user: dict = Depends(get_current_user)):
    """Get overall system status"""
    try:
        status = resource_manager.get_system_status()
        return status
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get system status: {str(e)}"
        )

@router.get("/resources/history")
async def get_resource_history(
    hours: int = 24,
    current_user: dict = Depends(get_current_user)
):
    """Get resource usage history"""
    try:
        history = resource_manager.get_resource_history(hours=hours)
        return {
            "history": history,
            "total_entries": len(history),
            "time_range_hours": hours
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get resource history: {str(e)}"
        )

@router.post("/tasks/submit")
async def submit_task(
    task_data: dict,
    current_user: dict = Depends(trader_required)
):
    """Submit a system task"""
    try:
        # Validate task data
        required_fields = ["id", "name", "description", "priority", "required_resources"]
        for field in required_fields:
            if field not in task_data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing required field: {field}"
                )
        
        # Parse priority
        try:
            priority = TaskPriority(task_data["priority"])
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid priority value"
            )
        
        # Parse required resources
        required_resources = {}
        for resource_name, amount in task_data["required_resources"].items():
            try:
                resource_type = ResourceType(resource_name)
                required_resources[resource_type] = float(amount)
            except (ValueError, TypeError):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid resource type or amount: {resource_name}"
                )
        
        # Create task
        task = SystemTask(
            id=task_data["id"],
            name=task_data["name"],
            description=task_data["description"],
            priority=priority,
            required_resources=required_resources,
            max_duration=task_data.get("max_duration"),
            status=TaskStatus.PENDING
        )
        
        # Submit task
        task_id = resource_manager.submit_task(task)
        
        return {
            "task_id": task_id,
            "status": "submitted",
            "message": f"Task {task_id} submitted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit task: {str(e)}"
        )

@router.get("/tasks/{task_id}")
async def get_task_status(
    task_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get task status"""
    try:
        task = resource_manager.get_task_status(task_id)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        return {
            "task_id": task.id,
            "name": task.name,
            "description": task.description,
            "priority": task.priority.value,
            "status": task.status.value,
            "required_resources": {
                resource_type.value: amount 
                for resource_type, amount in task.required_resources.items()
            },
            "created_at": task.created_at.isoformat(),
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "result": task.result,
            "error": task.error
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get task status: {str(e)}"
        )

@router.post("/tasks/{task_id}/cancel")
async def cancel_task(
    task_id: str,
    current_user: dict = Depends(trader_required)
):
    """Cancel a task"""
    try:
        success = resource_manager.cancel_task(task_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found or cannot be cancelled"
            )
        
        return {
            "task_id": task_id,
            "status": "cancelled",
            "message": f"Task {task_id} cancelled successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel task: {str(e)}"
        )

@router.get("/tasks")
async def list_tasks(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    limit: int = 100,
    current_user: dict = Depends(get_current_user)
):
    """List all tasks"""
    try:
        tasks = []
        
        # Get all tasks (running + completed)
        for task in list(resource_manager.running_tasks.values()):
            if status and task.status.value != status:
                continue
            if priority and task.priority.value != int(priority):
                continue
            
            tasks.append({
                "task_id": task.id,
                "name": task.name,
                "description": task.description,
                "priority": task.priority.value,
                "status": task.status.value,
                "created_at": task.created_at.isoformat(),
                "started_at": task.started_at.isoformat() if task.started_at else None,
                "completed_at": task.completed_at.isoformat() if task.completed_at else None
            })
        
        # Add completed tasks
        for task in resource_manager.completed_tasks[-limit:]:
            if status and task.status.value != status:
                continue
            if priority and task.priority.value != int(priority):
                continue
            
            tasks.append({
                "task_id": task.id,
                "name": task.name,
                "description": task.description,
                "priority": task.priority.value,
                "status": task.status.value,
                "created_at": task.created_at.isoformat(),
                "started_at": task.started_at.isoformat() if task.started_at else None,
                "completed_at": task.completed_at.isoformat() if task.completed_at else None
            })
        
        # Sort by creation time (newest first)
        tasks.sort(key=lambda x: x["created_at"], reverse=True)
        
        return {
            "tasks": tasks[:limit],
            "total": len(tasks),
            "limit": limit
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list tasks: {str(e)}"
        )

@router.post("/tasks/schedule")
async def schedule_tasks(
    current_user: dict = Depends(admin_required)
):
    """Manually trigger task scheduling"""
    try:
        resource_manager.schedule_tasks()
        return {
            "status": "scheduled",
            "message": "Tasks scheduled successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to schedule tasks: {str(e)}"
        )

@router.post("/resources/optimize")
async def optimize_resources(
    current_user: dict = Depends(admin_required)
):
    """Optimize resource allocation"""
    try:
        resource_manager.optimize_resources()
        return {
            "status": "optimized",
            "message": "Resources optimized successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to optimize resources: {str(e)}"
        )

@router.post("/tasks/cleanup")
async def cleanup_completed_tasks(
    max_age_hours: int = 24,
    current_user: dict = Depends(admin_required)
):
    """Clean up completed tasks"""
    try:
        before_count = len(resource_manager.completed_tasks)
        resource_manager.cleanup_completed_tasks(max_age_hours=max_age_hours)
        after_count = len(resource_manager.completed_tasks)
        
        return {
            "status": "cleaned",
            "before_count": before_count,
            "after_count": after_count,
            "cleaned_count": before_count - after_count,
            "message": f"Cleaned up {before_count - after_count} completed tasks"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cleanup tasks: {str(e)}"
        )

@router.get("/manager/overview")
async def get_system_overview(current_user: dict = Depends(get_current_user)):
    """Get complete system overview"""
    try:
        overview = system_manager.get_system_overview()
        return overview
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get system overview: {str(e)}"
        )

@router.post("/manager/start")
async def start_system_manager(current_user: dict = Depends(admin_required)):
    """Start the system manager"""
    try:
        system_manager.start()
        return {
            "status": "started",
            "message": "System manager started successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start system manager: {str(e)}"
        )

@router.post("/manager/stop")
async def stop_system_manager(current_user: dict = Depends(admin_required)):
    """Stop the system manager"""
    try:
        system_manager.stop()
        return {
            "status": "stopped",
            "message": "System manager stopped successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stop system manager: {str(e)}"
        )

@router.post("/manager/execute-task")
async def execute_system_task(
    task_data: dict,
    current_user: dict = Depends(trader_required)
):
    """Execute a system task"""
    try:
        result = system_manager.execute_system_task(task_data)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute system task: {str(e)}"
        )

@router.get("/manager/status")
async def get_manager_status(current_user: dict = Depends(get_current_user)):
    """Get system manager status"""
    try:
        return {
            "is_running": system_manager.is_running,
            "components_registered": list(system_manager.components.keys()),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get manager status: {str(e)}"
        )

@router.get("/health")
async def get_system_health(current_user: dict = Depends(get_current_user)):
    """Get detailed system health"""
    try:
        status = resource_manager.get_system_status()
        
        # Calculate health score
        health_score = 100
        alerts = []
        
        if status["resource_usage"]:
            usage = status["resource_usage"]
            
            if usage["cpu_percent"] > 90:
                health_score -= 20
                alerts.append("Critical CPU usage")
            elif usage["cpu_percent"] > 80:
                health_score -= 10
                alerts.append("High CPU usage")
            
            if usage["memory_percent"] > 90:
                health_score -= 20
                alerts.append("Critical memory usage")
            elif usage["memory_percent"] > 80:
                health_score -= 10
                alerts.append("High memory usage")
            
            if usage["disk_percent"] > 95:
                health_score -= 30
                alerts.append("Critical disk usage")
            elif usage["disk_percent"] > 90:
                health_score -= 15
                alerts.append("High disk usage")
        
        # Check task queue
        if status["pending_tasks"] > 100:
            health_score -= 10
            alerts.append("Large task queue")
        
        if status["running_tasks"] > 50:
            health_score -= 15
            alerts.append("Many running tasks")
        
        return {
            "health_score": max(0, health_score),
            "status": "healthy" if health_score > 80 else "warning" if health_score > 50 else "critical",
            "alerts": alerts,
            "system_status": status,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get system health: {str(e)}"
        )