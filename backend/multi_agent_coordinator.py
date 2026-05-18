import asyncio
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import requests

class AgentType(Enum):
    CODING = "coding"
    TRADING = "trading"
    MONITORING = "monitoring"
    RESEARCH = "research"
    COORDINATION = "coordination"

@dataclass
class AgentTask:
    id: str
    type: AgentType
    description: str
    priority: int
    status: str = "pending"
    result: Optional[str] = None
    error: Optional[str] = None
    created_at: str = None
    completed_at: Optional[str] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()

class MultiAgentCoordinator:
    """Orchestrates multiple AI agents for coordinated task execution"""
    
    def __init__(self, api_url: str = "http://localhost:8000"):
        self.api_url = api_url
        self.agents: Dict[AgentType, Dict[str, Any]] = {}
        self.task_queue: List[AgentTask] = []
        self.completed_tasks: List[AgentTask] = []
        self.logger = self._setup_logger()
        self._initialize_agents()
    
    def _setup_logger(self):
        logger = logging.getLogger("multi_agent_coordinator")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _initialize_agents(self):
        """Initialize available agents with their capabilities"""
        self.agents = {
            AgentType.CODING: {
                "name": "Coding Agent",
                "skills": ["codebase-inspection", "python-debugpy", "github-pr-workflow"],
                "capabilities": ["code_analysis", "debugging", "refactoring"],
                "model": "coding"
            },
            AgentType.TRADING: {
                "name": "Trading Agent",
                "skills": [],
                "capabilities": ["market_analysis", "signal_generation", "backtesting"],
                "model": "reasoning"
            },
            AgentType.MONITORING: {
                "name": "Monitoring Agent",
                "skills": ["dogfood", "webhook-subscriptions"],
                "capabilities": ["system_health", "performance_monitoring", "alerting"],
                "model": "cheap"
            },
            AgentType.RESEARCH: {
                "name": "Research Agent",
                "skills": ["arxiv", "blogwatcher", "llm-wiki"],
                "capabilities": ["paper_analysis", "market_research", "knowledge_synthesis"],
                "model": "reasoning"
            },
            AgentType.COORDINATION: {
                "name": "Coordination Agent",
                "skills": ["kanban-orchestrator", "writing-plans"],
                "capabilities": ["task_planning", "resource_allocation", "progress_tracking"],
                "model": "planning"
            }
        }
        
        self.logger.info("Multi-agent coordinator initialized")
        self.logger.info(f"Available agents: {list(self.agents.keys())}")
    
    async def submit_task(self, task_description: str, agent_type: AgentType, priority: int = 1) -> str:
        """Submit a task to the appropriate agent"""
        task_id = f"{agent_type.value}_{int(datetime.now().timestamp())}"
        
        task = AgentTask(
            id=task_id,
            type=agent_type,
            description=task_description,
            priority=priority
        )
        
        self.task_queue.append(task)
        self.task_queue.sort(key=lambda x: x.priority, reverse=True)
        
        self.logger.info(f"Task submitted: {task_id} - {task_description}")
        
        # Start processing asynchronously
        asyncio.create_task(self._process_task(task))
        
        return task_id
    
    async def _process_task(self, task: AgentTask):
        """Process a single task"""
        try:
            task.status = "processing"
            self.logger.info(f"Processing task: {task.id}")
            
            # Select appropriate agent
            agent = self.agents.get(task.type)
            if not agent:
                raise Exception(f"No agent available for type: {task.type}")
            
            # Execute task through Hermes integration
            result = await self._execute_with_agent(task, agent)
            
            task.result = result
            task.status = "completed"
            task.completed_at = datetime.now().isoformat()
            
            self.logger.info(f"Task completed: {task.id}")
            
        except Exception as e:
            task.status = "failed"
            task.error = str(e)
            task.completed_at = datetime.now().isoformat()
            
            self.logger.error(f"Task failed: {task.id} - {str(e)}")
        
        finally:
            # Move to completed tasks
            self.task_queue.remove(task)
            self.completed_tasks.append(task)
    
    async def _execute_with_agent(self, task: AgentType, agent: Dict[str, Any]) -> str:
        """Execute task using the specified agent"""
        # Use the backend API to route through appropriate model
        route_response = requests.get(
            f"{self.api_url}/route/{task.description}"
        )
        
        if route_response.status_code != 200:
            raise Exception(f"Failed to route task: {route_response.text}")
        
        routing_result = route_response.json()
        model = routing_result.get("model", agent["model"])
        
        # Execute the task
        prompt = f"""
        You are the {agent['name']} with capabilities: {', '.join(agent['capabilities'])}
        
        TASK: {task.description}
        
        Available skills: {', '.join(agent.get('skills', []))}
        
        Please execute this task using your available capabilities and skills.
        Provide a detailed and accurate response.
        """
        
        ask_response = requests.get(
            f"{self.api_url}/ask/{prompt}"
        )
        
        if ask_response.status_code != 200:
            raise Exception(f"Failed to execute task: {ask_response.text}")
        
        result = ask_response.json()
        return result.get("response", "No response received")
    
    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific task"""
        # Check in queue
        for task in self.task_queue:
            if task.id == task_id:
                return {
                    "id": task.id,
                    "type": task.type.value,
                    "description": task.description,
                    "status": task.status,
                    "priority": task.priority,
                    "created_at": task.created_at
                }
        
        # Check completed tasks
        for task in self.completed_tasks:
            if task.id == task_id:
                return {
                    "id": task.id,
                    "type": task.type.value,
                    "description": task.description,
                    "status": task.status,
                    "priority": task.priority,
                    "created_at": task.created_at,
                    "completed_at": task.completed_at,
                    "result": task.result,
                    "error": task.error
                }
        
        return None
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get overall multi-agent system status"""
        return {
            "agents": {
                agent_type.value: {
                    "name": agent["name"],
                    "capabilities": agent["capabilities"],
                    "skills": agent["skills"],
                    "active_tasks": len([t for t in self.task_queue if t.type == agent_type])
                }
                for agent_type, agent in self.agents.items()
            },
            "queue_status": {
                "pending": len([t for t in self.task_queue if t.status == "pending"]),
                "processing": len([t for t in self.task_queue if t.status == "processing"]),
                "completed": len(self.completed_tasks),
                "failed": len([t for t in self.completed_tasks if t.status == "failed"])
            },
            "timestamp": datetime.now().isoformat()
        }
    
    async def execute_coordinated_task(self, main_task: str, sub_tasks: List[Dict[str, Any]]) -> str:
        """Execute a coordinated task with multiple sub-tasks"""
        try:
            # Plan the coordinated execution
            coordination_prompt = f"""
            Coordinated Task Planning:
            
            Main Task: {main_task}
            
            Sub-tasks: {json.dumps(sub_tasks, indent=2)}
            
            Please plan the execution order and dependencies for these tasks.
            """
            
            # Use coordination agent to plan
            plan_result = await self._execute_with_agent(
                AgentTask(
                    id="coordination_plan",
                    type=AgentType.COORDINATION,
                    description=coordination_prompt,
                    priority=1
                ),
                self.agents[AgentType.COORDINATION]
            )
            
            # Execute sub-tasks in planned order
            results = []
            for sub_task in sub_tasks:
                task_id = await self.submit_task(
                    sub_task["description"],
                    AgentType(sub_task["agent_type"]),
                    sub_task.get("priority", 1)
                )
                results.append({"task_id": task_id, "description": sub_task["description"]})
            
            return {
                "plan": plan_result,
                "sub_tasks": results,
                "main_task": main_task,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "main_task": main_task,
                "timestamp": datetime.now().isoformat()
            }

# Global instance
multi_agent_coordinator = MultiAgentCoordinator()