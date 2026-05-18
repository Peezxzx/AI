"""
Enhanced Multi-Agent Communication System with Full Integration
"""

import asyncio
import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone, timedelta
import pydantic

from ai_core.agents import (
    CommunicationManager, EnhancedAgent, AgentCapability,
    EnhancedCodingAgent, TaskCoordinator
)

from ai_core.agents.coordinator import (
    CrossAgentCoordinator, TaskPriority, TaskStatus
)

from ai_core.agents.state_manager import (
    AgentStateSynchronizer, AgentStatePersistence
)

from ai_core.agents.conflict_resolution import (
    ConflictManager
)

from ai_core.agents.git_integration import (
    GitManager, CodingPipeline
)

from ai_core.agents.code_quality import (
    CodeQualityAnalyzer, CodeQualityController
)

from ai_core.agents.cicd_pipeline import (
    CICDPipeline, Environment, PipelineStatus
)

from ai_core.agents.automated_testing import (
    TestFramework, TestType, TestStatus
)

# Initialize FastAPI app
app = FastAPI(
    title="Atsawin AI Core - Enhanced Multi-Agent Communication",
    description="Multi-agent coordination system with task delegation, Git integration, CI/CD pipeline, code quality control, and automated testing",
    version="3.4.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables
communication_manager = CommunicationManager()
coding_agent = None
task_coordinator = None
cross_agent_coordinator = None

# State management
state_persistence = AgentStatePersistence()
state_synchronizer = AgentStateSynchronizer(state_persistence)

# Conflict resolution
conflict_manager = ConflictManager()

# Git integration
git_manager = GitManager()
coding_pipeline = CodingPipeline(git_manager)

# Code quality
code_quality_analyzer = CodeQualityAnalyzer()
code_quality_controller = CodeQualityController()

# CI/CD pipeline
cicd_pipeline = CICDPipeline()

# Automated testing
test_framework = TestFramework()
automated_testing_controller = None  # Will be initialized in startup

# Pydantic models
class TaskSubmissionRequest(pydantic.BaseModel):
    task_type: str
    required_capabilities: List[str]
    task_data: Dict[str, Any]
    priority: str = "NORMAL"
    deadline_minutes: Optional[int] = None
    dependencies: Optional[List[str]] = None

class TaskDependencyRequest(pydantic.BaseModel):
    task_id: str
    depends_on: List[str]

class GitRepositoryRequest(pydantic.BaseModel):
    repo_url: str
    repo_name: Optional[str] = None
    branch: str = "main"

class CodingPipelineRequest(pydantic.BaseModel):
    repo_name: str
    task_type: str
    task_data: Dict[str, Any]

class CodeQualityRequest(pydantic.BaseModel):
    project_path: str
    output_format: str = "json"

class PipelineConfigRequest(pydantic.BaseModel):
    project_name: str
    name: str
    trigger: str
    branch: str
    environment: str
    build_config: Dict[str, Any]
    test_config: Dict[str, Any]
    deploy_config: Dict[str, Any]
    notifications: Optional[Dict[str, Any]] = None

class PipelineRunRequest(pydantic.BaseModel):
    project_name: str
    repo_path: str
    commit_hash: str
    branch: str
    pipeline_id: str

class TestRunRequest(pydantic.BaseModel):
    project_path: str
    project_name: str
    test_types: List[str] = None
    output_format: str = "json"

@app.on_event("startup")
async def startup_event():
    """Initialize the system on startup"""
    global coding_agent, task_coordinator, cross_agent_coordinator, automated_testing_controller
    
    print("[System] Starting Enhanced Multi-Agent Communication System...")
    
    # Initialize agents
    coding_agent = EnhancedCodingAgent("coding_agent", communication_manager)
    task_coordinator = TaskCoordinator(communication_manager)
    cross_agent_coordinator = CrossAgentCoordinator(communication_manager)
    
    # Initialize automated testing controller
    from ai_core.agents.automated_testing import AutomatedTestingController
    automated_testing_controller = AutomatedTestingController()
    
    # Register agents with state synchronizer
    if coding_agent:
        state_synchronizer.register_agent(
            coding_agent.agent_id,
            coding_agent.state
        )
    
    # Start background services
    cross_agent_coordinator.start()
    conflict_manager.start()
    state_synchronizer.start_sync()
    
    # Create sample CI/CD pipeline configuration
    sample_pipeline_config = {
        "install_dependencies": {
            "package_manager": "pip",
            "requirements_file": "requirements.txt"
        },
        "build_commands": [
            "python -m pytest tests/",
            "python setup.py sdist bdist_wheel"
        ],
        "artifacts": ["dist", "build"],
        "environment_checks": [
            {
                "type": "disk_space",
                "min_gb": 5
            }
        ],
        "health_check_url": "http://localhost:8000/health",
        "service_name": "atsawin-ai-core",
        "restart_service": True,
        "deploy_path": "/opt/atsawin-ai-core/production",
        "user": "www-data",
        "group": "www-data"
    }
    
    # Test configuration
    test_config = {
        "test_commands": [
            "python -m pytest tests/ -v",
            "python -m flake8 .",
            "python -m black --check ."
        ],
        "coverage_command": "python -m pytest --cov=. --cov-report=xml"
    }
    
    # Create sample pipeline
    cicd_pipeline.create_pipeline_config(
        project_name="atsawin-ai-core",
        name="Main CI/CD Pipeline",
        trigger="push",
        branch="main",
        environment=Environment.PRODUCTION,
        build_config=sample_pipeline_config,
        test_config=test_config,
        deploy_config=sample_pipeline_config,
        notifications={
            "email": ["admin@atsawin.com"],
            "slack": "#devops"
        }
    )
    
    print("[System] System started successfully")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on shutdown"""
    global coding_agent, cross_agent_coordinator, conflict_manager
    
    if coding_agent:
        await coding_agent.stop()
    
    if cross_agent_coordinator:
        cross_agent_coordinator.stop()
    
    if conflict_manager:
        conflict_manager.stop()
    
    state_synchronizer.stop_sync()
    
    print("[System] System shutdown complete")

# API Endpoints

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Atsawin AI Core - Enhanced Multi-Agent Communication",
        "version": "3.4.0",
        "status": "operational"
    }

@app.get("/system/status")
async def get_system_status():
    """Get overall system status"""
    status = communication_manager.get_system_status()
    
    # Add cross-agent coordinator metrics
    if cross_agent_coordinator:
        status["coordination_metrics"] = cross_agent_coordinator.get_system_metrics()
    
    # Add state management metrics
    status["state_metrics"] = state_synchronizer.get_system_metrics()
    
    # Add conflict resolution metrics
    status["conflict_metrics"] = conflict_manager.get_system_metrics()
    
    # Add Git integration metrics
    status["git_metrics"] = {
        "repositories_managed": len(git_manager.list_repositories()),
        "pipeline_metrics": coding_pipeline.get_pipeline_metrics()
    }
    
    # Add code quality metrics
    status["code_quality_metrics"] = {
        "analyzer_available": True,
        "controller_available": True
    }
    
    # Add CI/CD pipeline metrics
    status["cicd_metrics"] = cicd_pipeline.get_pipeline_metrics("atsawin-ai-core")
    
    # Add testing metrics
    status["testing_metrics"] = automated_testing_controller.get_test_metrics("atsawin-ai-core")
    
    return status

@app.get("/system/communication/stats")
async def get_communication_stats():
    """Get communication statistics"""
    return communication_manager.get_message_statistics()

@app.get("/system/coordination/metrics")
async def get_coordination_metrics():
    """Get coordination system metrics"""
    if not cross_agent_coordinator:
        raise HTTPException(status_code=500, detail="Cross-agent coordinator not available")
    
    return cross_agent_coordinator.get_system_metrics()

@app.get("/system/state/metrics")
async def get_state_metrics():
    """Get state management metrics"""
    return state_synchronizer.get_system_metrics()

@app.get("/system/conflict/metrics")
async def get_conflict_metrics():
    """Get conflict resolution metrics"""
    return conflict_manager.get_system_metrics()

@app.get("/system/git/metrics")
async def get_git_metrics():
    """Get Git integration metrics"""
    return {
        "repositories": len(git_manager.list_repositories()),
        "pipeline": coding_pipeline.get_pipeline_metrics()
    }

@app.get("/system/code_quality/metrics")
async def get_code_quality_metrics():
    """Get code quality metrics"""
    return {
        "analyzer_available": True,
        "controller_available": True,
        "supported_languages": ["python", "javascript", "typescript", "java", "c++", "go", "rust"]
    }

@app.get("/system/cicd/metrics")
async def get_cicd_metrics():
    """Get CI/CD pipeline metrics"""
    return cicd_pipeline.get_pipeline_metrics("atsawin-ai-core")

@app.get("/system/testing/metrics")
async def get_testing_metrics():
    """Get testing metrics"""
    return automated_testing_controller.get_test_metrics("atsawin-ai-core")

# Task management endpoints
@app.post("/tasks/submit")
async def submit_task(task_request: TaskSubmissionRequest):
    """Submit a task to the cross-agent coordinator"""
    if not cross_agent_coordinator:
        raise HTTPException(status_code=500, detail="Cross-agent coordinator not available")
    
    try:
        # Convert priority string to enum
        priority = TaskPriority[task_request.priority.upper()]
    except KeyError:
        raise HTTPException(status_code=400, detail="Invalid priority")
    
    # Parse deadline
    deadline = None
    if task_request.deadline_minutes:
        deadline = datetime.now(timezone.utc) + timedelta(minutes=task_request.deadline_minutes)
    
    # Submit task
    task_id = cross_agent_coordinator.submit_task(
        task_type=task_request.task_type,
        required_capabilities=task_request.required_capabilities,
        task_data=task_request.task_data,
        priority=priority,
        deadline=deadline,
        dependencies=task_request.dependencies
    )
    
    return {
        "status": "success",
        "task_id": task_id,
        "message": "Task submitted to coordinator",
        "priority": task_request.priority,
        "deadline": deadline.isoformat() if deadline else None
    }

@app.get("/tasks/{task_id}/status")
async def get_task_status(task_id: str):
    """Get task status from cross-agent coordinator"""
    if not cross_agent_coordinator:
        raise HTTPException(status_code=500, detail="Cross-agent coordinator not available")
    
    task_status = cross_agent_coordinator.get_task_status(task_id)
    
    if not task_status:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return task_status

@app.get("/tasks/all")
async def get_all_tasks():
    """Get all tasks in the system"""
    if not cross_agent_coordinator:
        raise HTTPException(status_code=500, detail="Cross-agent coordinator not available")
    
    # Get tasks from dependency manager
    all_tasks = []
    for task_id, task in cross_agent_coordinator.dependency_manager.tasks.items():
        all_tasks.append({
            "task_id": task.task_id,
            "task_type": task.task_type,
            "status": task.status.value,
            "priority": task.priority.name,
            "assigned_agent": task.assigned_agent,
            "created_at": task.created_at.isoformat(),
            "deadline": task.deadline.isoformat() if task.deadline else None,
            "dependencies": task.dependencies,
            "retry_count": task.retry_count,
            "progress": task.progress
        })
    
    return {
        "total_tasks": len(all_tasks),
        "tasks": all_tasks
    }

@app.post("/tasks/{task_id}/cancel")
async def cancel_task(task_id: str):
    """Cancel a task"""
    if not cross_agent_coordinator:
        raise HTTPException(status_code=500, detail="Cross-agent coordinator not available")
    
    # Find and cancel task
    task = cross_agent_coordinator.dependency_manager.tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
        raise HTTPException(status_code=400, detail="Cannot cancel completed or failed task")
    
    # Cancel task
    task.status = TaskStatus.CANCELLED
    task.assigned_agent = None
    
    # Remove from active tasks if present
    if task_id in cross_agent_coordinator.active_tasks:
        del cross_agent_coordinator.active_tasks[task_id]
    
    return {
        "status": "success",
        "task_id": task_id,
        "message": "Task cancelled successfully"
    }

# Git integration endpoints
@app.post("/git/clone")
async def clone_repository(request: GitRepositoryRequest):
    """Clone a Git repository"""
    repo_name = git_manager.clone_repository(
        repo_url=request.repo_url,
        repo_name=request.repo_name,
        branch=request.branch
    )
    
    if not repo_name:
        raise HTTPException(status_code=400, detail="Failed to clone repository")
    
    return {
        "status": "success",
        "repo_name": repo_name,
        "message": "Repository cloned successfully"
    }

@app.get("/git/repositories")
async def list_repositories():
    """List all managed Git repositories"""
    repositories = []
    for repo_name in git_manager.list_repositories():
        repo_info = git_manager.get_repository_info(repo_name)
        if repo_info:
            repositories.append(repo_info.to_dict())
    
    return {
        "repositories": repositories,
        "count": len(repositories)
    }

@app.get("/git/repositories/{repo_name}/status")
async def get_repository_status(repo_name: str):
    """Get repository status"""
    repo_info = git_manager.get_repository_info(repo_name)
    if not repo_info:
        raise HTTPException(status_code=404, detail="Repository not found")
    
    status = git_manager.get_repository_status(repo_name)
    if status is None:
        raise HTTPException(status_code=400, detail="Failed to get repository status")
    
    return {
        "repo_name": repo_name,
        "status": status.value,
        "commit_hash": repo_info.commit_hash,
        "last_updated": repo_info.last_updated.isoformat() if repo_info.last_updated else None
    }

@app.get("/git/repositories/{repo_name}/history")
async def get_commit_history(repo_name: str, limit: int = 10):
    """Get commit history"""
    if repo_name not in git_manager.list_repositories():
        raise HTTPException(status_code=404, detail="Repository not found")
    
    commits = git_manager.get_commit_history(repo_name, limit)
    return {
        "repo_name": repo_name,
        "commits": [commit.to_dict() for commit in commits],
        "count": len(commits)
    }

# Coding pipeline endpoints
@app.post("/pipeline/execute")
async def execute_pipeline_task(request: CodingPipelineRequest):
    """Execute a coding pipeline task"""
    task_id = coding_pipeline.create_pipeline_task(
        repo_name=request.repo_name,
        task_type=request.task_type,
        task_data=request.task_data
    )
    
    # Execute task in background
    asyncio.create_task(coding_pipeline.execute_pipeline_task(task_id))
    
    return {
        "status": "success",
        "task_id": task_id,
        "message": "Pipeline task submitted for execution"
    }

@app.get("/pipeline/tasks/{task_id}/status")
async def get_pipeline_task_status(task_id: str):
    """Get pipeline task status"""
    task_status = coding_pipeline.get_pipeline_status(task_id)
    
    if not task_status:
        raise HTTPException(status_code=404, detail="Pipeline task not found")
    
    return task_status

@app.get("/pipeline/history")
async def get_pipeline_history(limit: int = 50):
    """Get pipeline execution history"""
    return coding_pipeline.get_pipeline_history(limit)

@app.get("/pipeline/metrics")
async def get_pipeline_metrics():
    """Get pipeline metrics"""
    return coding_pipeline.get_pipeline_metrics()

# Conflict management endpoints
@app.get("/conflicts")
async def get_conflicts(resolved: Optional[bool] = None):
    """Get conflicts, optionally filtered by resolution status"""
    conflicts = conflict_manager.get_conflicts(resolved)
    
    return {
        "conflicts": [conflict.to_dict() for conflict in conflicts.values()],
        "count": len(conflicts)
    }

@app.post("/conflicts/{conflict_id}/resolve")
async def resolve_conflict(conflict_id: str):
    """Manually resolve a conflict"""
    success = conflict_manager.resolve_conflict(conflict_id)
    
    if not success:
        raise HTTPException(status_code=400, detail="Failed to resolve conflict")
    
    return {
        "status": "success",
        "conflict_id": conflict_id,
        "message": "Conflict resolved successfully"
    }

@app.get("/conflicts/history")
async def get_conflict_history(limit: int = 100):
    """Get conflict history"""
    history = conflict_manager.get_conflict_history(limit)
    return {
        "history": [conflict.to_dict() for conflict in history],
        "count": len(history)
    }

# Code quality endpoints
@app.post("/code_quality/analyze")
async def analyze_code_quality(request: CodeQualityRequest):
    """Analyze code quality for a project"""
    try:
        result = code_quality_controller.analyze_project(
            request.project_path,
            request.output_format
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Code quality analysis failed: {str(e)}")

@app.get("/code_quality/analyze/{project_path}")
async def analyze_project_quality(project_path: str):
    """Analyze code quality for a specific project"""
    try:
        result = code_quality_controller.analyze_project(project_path, "json")
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Code quality analysis failed: {str(e)}")

@app.get("/code_quality/supported_languages")
async def get_supported_languages():
    """Get supported languages for code quality analysis"""
    return {
        "supported_languages": [
            "python", "javascript", "typescript", 
            "java", "c++", "go", "rust"
        ]
    }

# CI/CD pipeline endpoints
@app.post("/cicd/pipelines")
async def create_pipeline_config(request: PipelineConfigRequest):
    """Create a new CI/CD pipeline configuration"""
    try:
        environment = Environment(request.environment.lower())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid environment")
    
    pipeline_id = cicd_pipeline.create_pipeline_config(
        project_name=request.project_name,
        name=request.name,
        trigger=request.trigger,
        branch=request.branch,
        environment=environment,
        build_config=request.build_config,
        test_config=request.test_config,
        deploy_config=request.deploy_config,
        notifications=request.notifications
    )
    
    return {
        "status": "success",
        "pipeline_id": pipeline_id,
        "message": "Pipeline configuration created successfully"
    }

@app.get("/cicd/pipelines/{pipeline_id}")
async def get_pipeline_config(pipeline_id: str):
    """Get CI/CD pipeline configuration"""
    pipeline_config = cicd_pipeline.get_pipeline_config(pipeline_id)
    
    if not pipeline_config:
        raise HTTPException(status_code=404, detail="Pipeline configuration not found")
    
    return pipeline_config.to_dict()

@app.get("/cicd/pipelines")
async def list_pipeline_configs():
    """List all CI/CD pipeline configurations"""
    # In real implementation, this would fetch all pipelines
    return {
        "pipelines": [],
        "count": 0
    }

@app.post("/cicd/pipelines/run")
async def run_pipeline(request: PipelineRunRequest):
    """Run a CI/CD pipeline"""
    pipeline_config = cicd_pipeline.get_pipeline_config(request.pipeline_id)
    
    if not pipeline_config:
        raise HTTPException(status_code=404, detail="Pipeline configuration not found")
    
    # Run pipeline in background
    asyncio.create_task(
        cicd_pipeline.run_pipeline(
            request.project_name,
            request.repo_path,
            request.commit_hash,
            request.branch,
            pipeline_config
        )
    )
    
    return {
        "status": "success",
        "pipeline_id": request.pipeline_id,
        "message": "Pipeline execution started"
    }

@app.get("/cicd/pipelines/history")
async def get_pipeline_history(project_name: str = "atsawin-ai-core", limit: int = 50):
    """Get CI/CD pipeline execution history"""
    history = cicd_pipeline.get_pipeline_history(project_name, limit)
    return {
        "project_name": project_name,
        "history": history,
        "count": len(history)
    }

@app.get("/cicd/pipelines/metrics")
async def get_pipeline_metrics():
    """Get CI/CD pipeline metrics"""
    return cicd_pipeline.get_pipeline_metrics("atsawin-ai-core")

# Testing endpoints
@app.post("/testing/run")
async def run_tests(request: TestRunRequest):
    """Run automated tests"""
    try:
        # Convert test types to enum
        test_types = []
        for test_type_str in request.test_types or []:
            try:
                test_types.append(TestType(test_type_str.lower()))
            except ValueError:
                pass
        
        # Run tests
        test_report = await automated_testing_controller.run_project_tests(
            request.project_path,
            request.project_name,
            test_types
        )
        
        # Generate report in requested format
        report_content = automated_testing_controller.generate_test_report(
            test_report,
            request.output_format
        )
        
        return {
            "status": "success",
            "report_id": test_report.report_id,
            "report_content": report_content,
            "message": "Tests completed successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Test execution failed: {str(e)}")

@app.get("/testing/reports/{report_id}")
async def get_test_report(report_id: str):
    """Get test report by ID"""
    test_report = automated_testing_controller.framework.get_test_report(report_id)
    
    if not test_report:
        raise HTTPException(status_code=404, detail="Test report not found")
    
    return test_report.to_dict()

@app.get("/testing/history")
async def get_test_history(project_name: str = "atsawin-ai-core", limit: int = 50):
    """Get test history"""
    history = automated_testing_controller.get_test_history(project_name, limit)
    return {
        "project_name": project_name,
        "history": [report.to_dict() for report in history],
        "count": len(history)
    }

@app.get("/testing/metrics")
async def get_test_metrics():
    """Get testing metrics"""
    return automated_testing_controller.get_test_metrics("atsawin-ai-core")

@app.get("/testing/supported_types")
async def get_supported_test_types():
    """Get supported test types"""
    return {
        "supported_types": [test_type.value for test_type in TestType]
    }

# State management endpoints
@app.get("/agents/state/{agent_id}")
async def get_agent_state(agent_id: str):
    """Get agent state"""
    agent_state = state_synchronizer.get_agent_state(agent_id)
    
    if not agent_state:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return agent_state.to_dict() if hasattr(agent_state, 'to_dict') else agent_state.__dict__

@app.get("/agents/state/all")
async def get_all_agent_states():
    """Get all agent states"""
    agents = state_synchronizer.get_all_agents()
    return {
        "agents": [agent.__dict__ for agent in agents.values()],
        "count": len(agents)
    }

@app.get("/agents/state/by-status/{status}")
async def get_agents_by_status(status: str):
    """Get agents by status"""
    try:
        from ai_core.agents import AgentStatus
        agent_status = AgentStatus(status.lower())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid status")
    
    agents = state_synchronizer.get_agents_by_status(agent_status)
    return {
        "status": status,
        "agents": [agent.__dict__ for agent in agents],
        "count": len(agents)
    }

@app.get("/agents/state/history/{agent_id}")
async def get_agent_history(agent_id: str, limit: int = 100):
    """Get agent event history"""
    history = state_synchronizer.get_agent_history(agent_id, limit)
    return {
        "agent_id": agent_id,
        "history": [event.to_dict() for event in history],
        "count": len(history)
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "services": {
            "communication_manager": "running",
            "coding_agent": "running" if coding_agent else "not_available",
            "task_coordinator": "running" if task_coordinator else "not_available",
            "cross_agent_coordinator": "running" if cross_agent_coordinator else "not_available",
            "state_synchronizer": "running",
            "conflict_manager": "running",
            "git_manager": "running",
            "coding_pipeline": "running",
            "code_quality_analyzer": "running",
            "code_quality_controller": "running",
            "cicd_pipeline": "running",
            "test_framework": "running",
            "automated_testing_controller": "running"
        }
    }

if __name__ == "__main__":
    print("[System] Starting Enhanced Multi-Agent Communication System...")
    print("[System] API Server will be available at: http://localhost:8000")
    print("[System] Documentation available at: http://localhost:8000/docs")
    
    uvicorn.run(
        "main_enhanced_communication:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )