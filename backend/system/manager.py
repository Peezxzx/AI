import asyncio
import threading
import time
from typing import Dict, Any, List
from datetime import datetime
import logging
from .resource_manager import resource_manager

class SystemManager:
    """Central system coordinator for AI Operating System"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.is_running = False
        self.manager_thread = None
        
        # System components
        self.components = {
            "resource_manager": resource_manager,
            "multi_agent_coordinator": None,  # Will be set later
            "memory_manager": None,  # Will be set later
            "hermes_integration": None  # Will be set later
        }
        
        self.logger.info("System Manager initialized")

    def start(self):
        """Start the system manager"""
        if not self.is_running:
            self.is_running = True
            self.manager_thread = threading.Thread(target=self._run_system)
            self.manager_thread.daemon = True
            self.manager_thread.start()
            
            # Start resource monitoring
            resource_manager.start_monitoring()
            
            self.logger.info("System Manager started")

    def stop(self):
        """Stop the system manager"""
        self.is_running = False
        if self.manager_thread:
            self.manager_thread.join()
        
        # Stop resource monitoring
        resource_manager.stop_monitoring()
        
        self.logger.info("System Manager stopped")

    def _run_system(self):
        """Main system loop"""
        while self.is_running:
            try:
                # Schedule tasks every 10 seconds
                resource_manager.schedule_tasks()
                
                # Optimize resources every 30 seconds
                if int(time.time()) % 30 == 0:
                    resource_manager.optimize_resources()
                
                # Cleanup completed tasks every hour
                if int(time.time()) % 3600 == 0:
                    resource_manager.cleanup_completed_tasks()
                
                time.sleep(10)
                
            except Exception as e:
                self.logger.error(f"System manager error: {e}")
                time.sleep(60)  # Wait longer on error

    def get_system_overview(self) -> Dict[str, Any]:
        """Get complete system overview"""
        overview = {
            "timestamp": datetime.now().isoformat(),
            "status": "running" if self.is_running else "stopped",
            "components": {}
        }
        
        # Get resource manager status
        try:
            overview["components"]["resource_manager"] = resource_manager.get_system_status()
        except Exception as e:
            overview["components"]["resource_manager"] = {"error": str(e)}
        
        # Add component health checks
        for component_name, component in self.components.items():
            if component:
                try:
                    if hasattr(component, 'get_system_status'):
                        overview["components"][component_name] = component.get_system_status()
                    elif hasattr(component, 'get_status'):
                        overview["components"][component_name] = component.get_status()
                    else:
                        overview["components"][component_name] = "active"
                except Exception as e:
                    overview["components"][component_name] = {"error": str(e)}
        
        return overview

    def register_component(self, name: str, component: Any):
        """Register a system component"""
        self.components[name] = component
        self.logger.info(f"Component registered: {name}")

    def execute_system_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a system task"""
        from .resource_manager import SystemTask, TaskPriority, ResourceType
        
        # Create system task
        task = SystemTask(
            id=task_data.get("id", f"system_{int(time.time())}"),
            name=task_data.get("name", "System Task"),
            description=task_data.get("description", "System execution task"),
            priority=TaskPriority(task_data.get("priority", 3)),
            required_resources=task_data.get("required_resources", {}),
            max_duration=task_data.get("max_duration")
        )
        
        # Submit task
        task_id = resource_manager.submit_task(task)
        
        return {
            "task_id": task_id,
            "status": "submitted",
            "message": f"System task {task_id} submitted"
        }

# Global instance
system_manager = SystemManager()