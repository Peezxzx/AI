"""
CI/CD Pipeline Integration - Automated build, test, and deployment pipeline
"""

import os
import json
import subprocess
import yaml
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import asyncio
import tempfile
import shutil
from pathlib import Path


class PipelineStatus(Enum):
    """Pipeline status"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Environment(Enum):
    """Environment types"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class BuildStatus(Enum):
    """Build status"""
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class DeploymentStatus(Enum):
    """Deployment status"""
    SUCCESS = "success"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"
    PENDING = "pending"


@dataclass
class BuildConfig:
    """Build configuration"""
    build_id: str
    project_name: str
    commit_hash: str
    branch: str
    build_number: int
    build_status: BuildStatus
    build_log: List[str]
    artifacts: List[str]
    created_at: datetime
    completed_at: Optional[datetime] = None
    duration: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "build_id": self.build_id,
            "project_name": self.project_name,
            "commit_hash": self.commit_hash,
            "branch": self.branch,
            "build_number": self.build_number,
            "build_status": self.build_status.value,
            "build_log": self.build_log,
            "artifacts": self.artifacts,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration": self.duration
        }


@dataclass
class DeploymentConfig:
    """Deployment configuration"""
    deployment_id: str
    project_name: str
    environment: Environment
    build_id: str
    deployment_status: DeploymentStatus
    deployment_log: List[str]
    created_at: datetime
    completed_at: Optional[datetime] = None
    duration: Optional[float] = None
    rollback_info: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "deployment_id": self.deployment_id,
            "project_name": self.project_name,
            "environment": self.environment.value,
            "build_id": self.build_id,
            "deployment_status": self.deployment_status.value,
            "deployment_log": self.deployment_log,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration": self.duration,
            "rollback_info": self.rollback_info
        }


@dataclass
class PipelineConfig:
    """Pipeline configuration"""
    pipeline_id: str
    project_name: str
    name: str
    trigger: str  # manual, push, pull_request, schedule
    branch: str
    environment: Environment
    build_config: Dict[str, Any]
    test_config: Dict[str, Any]
    deploy_config: Dict[str, Any]
    notifications: Dict[str, Any]
    created_at: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "pipeline_id": self.pipeline_id,
            "project_name": self.project_name,
            "name": self.name,
            "trigger": self.trigger,
            "branch": self.branch,
            "environment": self.environment.value,
            "build_config": self.build_config,
            "test_config": self.test_config,
            "deploy_config": self.deploy_config,
            "notifications": self.notifications,
            "created_at": self.created_at.isoformat()
        }


class BuildExecutor:
    """Build execution engine"""
    
    def __init__(self, workspace_path: str = "/tmp/workspace"):
        self.workspace_path = workspace_path
        self.build_configs: Dict[str, BuildConfig] = {}
        self.build_counter: Dict[str, int] = {}
        
        # Ensure workspace exists
        os.makedirs(workspace_path, exist_ok=True)
    
    async def execute_build(self, project_name: str, repo_path: str, 
                          commit_hash: str, branch: str, 
                          build_config: Dict[str, Any]) -> Optional[BuildConfig]:
        """Execute a build"""
        # Generate build ID
        build_id = f"build_{project_name}_{int(datetime.now(timezone.utc).timestamp())}"
        
        # Get next build number
        build_number = self.build_counter.get(project_name, 0) + 1
        self.build_counter[project_name] = build_number
        
        # Create build configuration
        build_config_obj = BuildConfig(
            build_id=build_id,
            project_name=project_name,
            commit_hash=commit_hash,
            branch=branch,
            build_number=build_number,
            build_status=BuildStatus.RUNNING,
            build_log=[],
            artifacts=[],
            created_at=datetime.now(timezone.utc)
        )
        
        self.build_configs[build_id] = build_config_obj
        
        # Execute build
        try:
            # Create workspace for build
            build_workspace = os.path.join(self.workspace_path, project_name, f"build_{build_number}")
            os.makedirs(build_workspace, exist_ok=True)
            
            # Log start
            build_config_obj.build_log.append(f"Starting build {build_id}")
            
            # Copy repository to workspace
            subprocess.run(
                ["cp", "-r", repo_path, build_workspace],
                check=True,
                capture_output=True,
                text=True
            )
            
            build_config_obj.build_log.append(f"Copied repository to {build_workspace}")
            
            # Change to build directory
            original_cwd = os.getcwd()
            os.chdir(build_workspace)
            
            # Install dependencies
            if "install_dependencies" in build_config:
                await self._install_dependencies(build_config_obj, build_config["install_dependencies"])
            
            # Build project
            if "build_commands" in build_config:
                await self._execute_build_commands(build_config_obj, build_config["build_commands"])
            
            # Collect artifacts
            artifacts = await self._collect_artifacts(build_config_obj, build_config.get("artifacts", []))
            build_config_obj.artifacts.extend(artifacts)
            
            # Mark as successful
            build_config_obj.build_status = BuildStatus.SUCCESS
            build_config_obj.build_log.append("Build completed successfully")
            
        except Exception as e:
            build_config_obj.build_status = BuildStatus.FAILED
            build_config_obj.build_log.append(f"Build failed: {str(e)}")
        
        finally:
            # Change back to original directory
            os.chdir(original_cwd)
            
            # Update completion time and duration
            build_config_obj.completed_at = datetime.now(timezone.utc)
            if build_config_obj.created_at:
                build_config_obj.duration = (
                    build_config_obj.completed_at - build_config_obj.created_at
                ).total_seconds()
        
        return build_config_obj
    
    async def _install_dependencies(self, build_config: BuildConfig, 
                                 dependency_config: Dict[str, Any]):
        """Install project dependencies"""
        build_config.build_log.append("Installing dependencies...")
        
        package_manager = dependency_config.get("package_manager", "pip")
        
        if package_manager == "pip":
            requirements_file = dependency_config.get("requirements_file", "requirements.txt")
            if os.path.exists(requirements_file):
                result = subprocess.run(
                    ["pip", "install", "-r", requirements_file],
                    capture_output=True,
                    text=True
                )
                build_config.build_log.append(f"Pip install result: {result.stdout}")
                if result.stderr:
                    build_config.build_log.append(f"Pip install errors: {result.stderr}")
        
        elif package_manager == "npm":
            package_json = dependency_config.get("package_json", "package.json")
            if os.path.exists(package_json):
                result = subprocess.run(
                    ["npm", "install"],
                    capture_output=True,
                    text=True
                )
                build_config.build_log.append(f"NPM install result: {result.stdout}")
                if result.stderr:
                    build_config.build_log.append(f"NPM install errors: {result.stderr}")
        
        elif package_manager == "maven":
            pom_file = dependency_config.get("pom_file", "pom.xml")
            if os.path.exists(pom_file):
                result = subprocess.run(
                    ["mvn", "install"],
                    capture_output=True,
                    text=True
                )
                build_config.build_log.append(f"Maven install result: {result.stdout}")
                if result.stderr:
                    build_config.build_log.append(f"Maven install errors: {result.stderr}")
    
    async def _execute_build_commands(self, build_config: BuildConfig, 
                                    build_commands: List[str]):
        """Execute build commands"""
        build_config.build_log.append("Executing build commands...")
        
        for command in build_commands:
            try:
                build_config.build_log.append(f"Executing: {command}")
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=300  # 5 minutes timeout
                )
                build_config.build_log.append(f"Command result: {result.stdout}")
                if result.stderr:
                    build_config.build_log.append(f"Command errors: {result.stderr}")
            except subprocess.TimeoutExpired:
                build_config.build_log.append(f"Command timed out: {command}")
                raise
            except Exception as e:
                build_config.build_log.append(f"Command failed: {command} - {str(e)}")
                raise
    
    async def _collect_artifacts(self, build_config: BuildConfig, 
                               artifact_patterns: List[str]) -> List[str]:
        """Collect build artifacts"""
        artifacts = []
        
        for pattern in artifact_patterns:
            if pattern == "dist":
                if os.path.exists("dist"):
                    artifacts.extend(["dist"])
            elif pattern == "build":
                if os.path.exists("build"):
                    artifacts.extend(["build"])
            elif pattern == "target":
                if os.path.exists("target"):
                    artifacts.extend(["target"])
            elif pattern.endswith("*"):
                # Simple pattern matching
                import glob
                matches = glob.glob(pattern)
                artifacts.extend(matches)
        
        build_config.build_log.append(f"Collected artifacts: {artifacts}")
        return artifacts
    
    def get_build_config(self, build_id: str) -> Optional[BuildConfig]:
        """Get build configuration"""
        return self.build_configs.get(build_id)
    
    def get_builds_by_project(self, project_name: str) -> List[BuildConfig]:
        """Get builds by project"""
        return [build for build in self.build_configs.values() 
                if build.project_name == project_name]
    
    def get_latest_build(self, project_name: str) -> Optional[BuildConfig]:
        """Get latest build for project"""
        builds = self.get_builds_by_project(project_name)
        if not builds:
            return None
        
        return max(builds, key=lambda b: b.build_number)


class DeploymentExecutor:
    """Deployment execution engine"""
    
    def __init__(self, workspace_path: str = "/tmp/workspace"):
        self.workspace_path = workspace_path
        self.deployment_configs: Dict[str, DeploymentConfig] = {}
        self.deployment_counter: Dict[str, int] = {}
    
    async def execute_deployment(self, project_name: str, environment: Environment,
                               build_id: str, deploy_config: Dict[str, Any]) -> Optional[DeploymentConfig]:
        """Execute a deployment"""
        # Generate deployment ID
        deployment_id = f"deploy_{project_name}_{environment.value}_{int(datetime.now(timezone.utc).timestamp())}"
        
        # Get build information
        # In real implementation, this would fetch from build executor
        build_info = {
            "build_id": build_id,
            "project_name": project_name,
            "status": "success"
        }
        
        # Create deployment configuration
        deployment_config = DeploymentConfig(
            deployment_id=deployment_id,
            project_name=project_name,
            environment=environment,
            build_id=build_id,
            deployment_status=DeploymentStatus.RUNNING,
            deployment_log=[],
            created_at=datetime.now(timezone.utc)
        )
        
        self.deployment_configs[deployment_id] = deployment_config
        
        # Execute deployment
        try:
            deployment_config.deployment_log.append(f"Starting deployment {deployment_id} to {environment.value}")
            
            # Pre-deployment checks
            await self._pre_deployment_checks(deployment_config, deploy_config)
            
            # Backup current deployment
            backup_path = await self._create_backup(deployment_config, project_name, environment)
            if backup_path:
                deployment_config.deployment_log.append(f"Created backup: {backup_path}")
            
            # Deploy artifacts
            await self._deploy_artifacts(deployment_config, build_id, deploy_config)
            
            # Post-deployment verification
            await self._post_deployment_verification(deployment_config, deploy_config)
            
            # Mark as successful
            deployment_config.deployment_status = DeploymentStatus.SUCCESS
            deployment_config.deployment_log.append("Deployment completed successfully")
            
        except Exception as e:
            deployment_config.deployment_status = DeploymentStatus.FAILED
            deployment_config.deployment_log.append(f"Deployment failed: {str(e)}")
            
            # Attempt rollback
            try:
                await self._rollback_deployment(deployment_config, backup_path)
                deployment_config.deployment_status = DeploymentStatus.ROLLED_BACK
                deployment_config.rollback_info = {
                    "backup_path": backup_path,
                    "rollback_time": datetime.now(timezone.utc).isoformat()
                }
            except Exception as rollback_error:
                deployment_config.deployment_log.append(f"Rollback failed: {str(rollback_error)}")
        
        finally:
            # Update completion time and duration
            deployment_config.completed_at = datetime.now(timezone.utc)
            if deployment_config.created_at:
                deployment_config.duration = (
                    deployment_config.completed_at - deployment_config.created_at
                ).total_seconds()
        
        return deployment_config
    
    async def _pre_deployment_checks(self, deployment_config: DeploymentConfig,
                                   deploy_config: Dict[str, Any]):
        """Pre-deployment checks"""
        deployment_config.deployment_log.append("Running pre-deployment checks...")
        
        # Check if target environment is available
        if "environment_checks" in deploy_config:
            for check in deploy_config["environment_checks"]:
                if check["type"] == "disk_space":
                    # Check disk space
                    result = subprocess.run(
                        ["df", "-h", deploy_config.get("deploy_path", "/")],
                        capture_output=True,
                        text=True
                    )
                    deployment_config.deployment_log.append(f"Disk space check: {result.stdout}")
                
                elif check["type"] == "port_availability":
                    # Check port availability
                    port = check.get("port", 80)
                    result = subprocess.run(
                        ["netstat", "-tuln", "|", "grep", f":{port}"],
                        shell=True,
                        capture_output=True,
                        text=True
                    )
                    if result.returncode == 0:
                        deployment_config.deployment_log.append(f"Port {port} is not available")
                        raise Exception(f"Port {port} is not available")
                    else:
                        deployment_config.deployment_log.append(f"Port {port} is available")
    
    async def _create_backup(self, deployment_config: DeploymentConfig,
                           project_name: str, environment: Environment) -> Optional[str]:
        """Create backup of current deployment"""
        deployment_config.deployment_log.append("Creating backup...")
        
        deploy_path = f"/opt/{project_name}/{environment.value}"
        backup_path = f"/opt/{project_name}/backups/{project_name}_{environment.value}_{int(datetime.now(timezone.utc).timestamp())}"
        
        try:
            if os.path.exists(deploy_path):
                os.makedirs(f"/opt/{project_name}/backups", exist_ok=True)
                subprocess.run(
                    ["cp", "-r", deploy_path, backup_path],
                    check=True,
                    capture_output=True,
                    text=True
                )
                return backup_path
        except Exception as e:
            deployment_config.deployment_log.append(f"Backup creation failed: {str(e)}")
        
        return None
    
    async def _deploy_artifacts(self, deployment_config: DeploymentConfig,
                              build_id: str, deploy_config: Dict[str, Any]):
        """Deploy build artifacts"""
        deployment_config.deployment_log.append("Deploying artifacts...")
        
        deploy_path = deploy_config.get("deploy_path", f"/opt/{deployment_config.project_name}/{deployment_config.environment.value}")
        
        # Create deployment directory
        os.makedirs(deploy_path, exist_ok=True)
        
        # Copy artifacts (simplified - in real implementation, fetch from artifacts storage)
        artifacts = deploy_config.get("artifacts", ["dist", "build"])
        
        for artifact in artifacts:
            artifact_path = os.path.join(deploy_path, artifact)
            if os.path.exists(artifact):
                subprocess.run(
                    ["cp", "-r", artifact, artifact_path],
                    check=True,
                    capture_output=True,
                    text=True
                )
                deployment_config.deployment_log.append(f"Copied {artifact} to {artifact_path}")
        
        # Set permissions
        user = deploy_config.get("user", "www-data")
        group = deploy_config.get("group", "www-data")
        
        subprocess.run(
            ["chown", "-R", f"{user}:{group}", deploy_path],
            check=True,
            capture_output=True,
            text=True
        )
        
        deployment_config.deployment_log.append(f"Set permissions for {deploy_path}")
    
    async def _post_deployment_verification(self, deployment_config: DeploymentConfig,
                                         deploy_config: Dict[str, Any]):
        """Post-deployment verification"""
        deployment_config.deployment_log.append("Running post-deployment verification...")
        
        # Health check
        health_check_url = deploy_config.get("health_check_url", "http://localhost:80/health")
        
        try:
            import requests
            response = requests.get(health_check_url, timeout=30)
            if response.status_code != 200:
                raise Exception(f"Health check failed: {response.status_code}")
            deployment_config.deployment_log.append(f"Health check passed: {response.status_code}")
        except Exception as e:
            deployment_config.deployment_log.append(f"Health check failed: {str(e)}")
            raise
        
        # Service restart
        service_name = deploy_config.get("service_name", f"{deployment_config.project_name}")
        
        if deploy_config.get("restart_service", True):
            result = subprocess.run(
                ["systemctl", "restart", service_name],
                capture_output=True,
                text=True
            )
            deployment_config.deployment_log.append(f"Restarted service {service_name}: {result.stdout}")
            if result.stderr:
                deployment_config.deployment_log.append(f"Service restart errors: {result.stderr}")
    
    async def _rollback_deployment(self, deployment_config: DeploymentConfig,
                                 backup_path: Optional[str]):
        """Rollback deployment"""
        if not backup_path or not os.path.exists(backup_path):
            raise Exception("No backup available for rollback")
        
        deployment_config.deployment_log.append("Rolling back deployment...")
        
        deploy_path = f"/opt/{deployment_config.project_name}/{deployment_config.environment.value}"
        
        # Remove current deployment
        if os.path.exists(deploy_path):
            subprocess.run(
                ["rm", "-rf", deploy_path],
                check=True,
                capture_output=True,
                text=True
            )
        
        # Restore from backup
        subprocess.run(
            ["cp", "-r", backup_path, deploy_path],
            check=True,
            capture_output=True,
            text=True
        )
        
        deployment_config.deployment_log.append("Rollback completed")
    
    def get_deployment_config(self, deployment_id: str) -> Optional[DeploymentConfig]:
        """Get deployment configuration"""
        return self.deployment_configs.get(deployment_id)
    
    def get_deployments_by_project(self, project_name: str) -> List[DeploymentConfig]:
        """Get deployments by project"""
        return [deploy for deploy in self.deployment_configs.values() 
                if deploy.project_name == project_name]
    
    def get_deployments_by_environment(self, project_name: str, 
                                     environment: Environment) -> List[DeploymentConfig]:
        """Get deployments by environment"""
        return [deploy for deploy in self.deployment_configs.values() 
                if deploy.project_name == project_name and deploy.environment == environment]


class CICDPipeline:
    """Main CI/CD Pipeline orchestrator"""
    
    def __init__(self, workspace_path: str = "/tmp/workspace"):
        self.workspace_path = workspace_path
        self.build_executor = BuildExecutor(workspace_path)
        self.deployment_executor = DeploymentExecutor(workspace_path)
        self.pipeline_configs: Dict[str, PipelineConfig] = {}
        self.pipeline_counter: Dict[str, int] = {}
        
        # Ensure workspace exists
        os.makedirs(workspace_path, exist_ok=True)
    
    def create_pipeline_config(self, project_name: str, name: str, trigger: str,
                             branch: str, environment: Environment,
                             build_config: Dict[str, Any],
                             test_config: Dict[str, Any],
                             deploy_config: Dict[str, Any],
                             notifications: Dict[str, Any] = None) -> str:
        """Create a new pipeline configuration"""
        if notifications is None:
            notifications = {}
        
        # Generate pipeline ID
        pipeline_id = f"pipeline_{project_name}_{int(datetime.now(timezone.utc).timestamp())}"
        
        # Create pipeline configuration
        pipeline_config = PipelineConfig(
            pipeline_id=pipeline_id,
            project_name=project_name,
            name=name,
            trigger=trigger,
            branch=branch,
            environment=environment,
            build_config=build_config,
            test_config=test_config,
            deploy_config=deploy_config,
            notifications=notifications,
            created_at=datetime.now(timezone.utc)
        )
        
        self.pipeline_configs[pipeline_id] = pipeline_config
        return pipeline_id
    
    async def run_pipeline(self, project_name: str, repo_path: str,
                         commit_hash: str, branch: str,
                         pipeline_config: PipelineConfig) -> Dict[str, Any]:
        """Run a CI/CD pipeline"""
        pipeline_result = {
            "pipeline_id": pipeline_config.pipeline_id,
            "project_name": project_name,
            "status": PipelineStatus.RUNNING.value,
            "build_result": None,
            "test_result": None,
            "deployment_result": None,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "completed_at": None
        }
        
        try:
            # Build phase
            pipeline_result["status"] = PipelineStatus.RUNNING.value
            build_result = await self.build_executor.execute_build(
                project_name, repo_path, commit_hash, branch,
                pipeline_config.build_config
            )
            
            if not build_result or build_result.build_status == BuildStatus.FAILED:
                pipeline_result["status"] = PipelineStatus.FAILED.value
                pipeline_result["build_result"] = build_result.to_dict() if build_result else None
                return pipeline_result
            
            pipeline_result["build_result"] = build_result.to_dict()
            
            # Test phase (simplified)
            test_result = await self._execute_tests(project_name, build_result, pipeline_config.test_config)
            pipeline_result["test_result"] = test_result
            
            if not test_result.get("success", False):
                pipeline_result["status"] = PipelineStatus.FAILED.value
                return pipeline_result
            
            # Deployment phase
            if pipeline_config.environment != Environment.DEVELOPMENT:
                deployment_result = await self.deployment_executor.execute_deployment(
                    project_name, pipeline_config.environment,
                    build_result.build_id, pipeline_config.deploy_config
                )
                
                if not deployment_result or deployment_result.deployment_status == DeploymentStatus.FAILED:
                    pipeline_result["status"] = PipelineStatus.FAILED.value
                    pipeline_result["deployment_result"] = deployment_result.to_dict() if deployment_result else None
                    return pipeline_result
                
                pipeline_result["deployment_result"] = deployment_result.to_dict()
            
            # Mark as successful
            pipeline_result["status"] = PipelineStatus.SUCCESS.value
            
        except Exception as e:
            pipeline_result["status"] = PipelineStatus.FAILED.value
            pipeline_result["error"] = str(e)
        
        finally:
            pipeline_result["completed_at"] = datetime.now(timezone.utc).isoformat()
        
        return pipeline_result
    
    async def _execute_tests(self, project_name: str, build_config: BuildConfig,
                           test_config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute tests"""
        test_result = {
            "success": True,
            "test_results": [],
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "skipped_tests": 0,
            "duration": 0
        }
        
        try:
            start_time = datetime.now(timezone.utc)
            
            # Run test commands
            if "test_commands" in test_config:
                for command in test_config["test_commands"]:
                    try:
                        result = subprocess.run(
                            command,
                            shell=True,
                            capture_output=True,
                            text=True,
                            timeout=300  # 5 minutes timeout
                        )
                        
                        test_result["test_results"].append({
                            "command": command,
                            "return_code": result.returncode,
                            "stdout": result.stdout,
                            "stderr": result.stderr,
                            "passed": result.returncode == 0
                        })
                        
                        if result.returncode == 0:
                            test_result["passed_tests"] += 1
                        else:
                            test_result["failed_tests"] += 1
                            test_result["success"] = False
                            
                    except Exception as e:
                        test_result["test_results"].append({
                            "command": command,
                            "error": str(e),
                            "passed": False
                        })
                        test_result["failed_tests"] += 1
                        test_result["success"] = False
            
            # Test coverage
            if "coverage_command" in test_config:
                try:
                    result = subprocess.run(
                        test_config["coverage_command"],
                        shell=True,
                        capture_output=True,
                        text=True
                    )
                    test_result["coverage"] = result.stdout
                except Exception as e:
                    test_result["coverage_error"] = str(e)
            
            test_result["total_tests"] = (
                test_result["passed_tests"] + test_result["failed_tests"] + test_result["skipped_tests"]
            )
            
            end_time = datetime.now(timezone.utc)
            test_result["duration"] = (end_time - start_time).total_seconds()
            
        except Exception as e:
            test_result["success"] = False
            test_result["error"] = str(e)
        
        return test_result
    
    def get_pipeline_config(self, pipeline_id: str) -> Optional[PipelineConfig]:
        """Get pipeline configuration"""
        return self.pipeline_configs.get(pipeline_id)
    
    def get_pipeline_configs_by_project(self, project_name: str) -> List[PipelineConfig]:
        """Get pipeline configurations by project"""
        return [config for config in self.pipeline_configs.values() 
                if config.project_name == project_name]
    
    def get_pipeline_history(self, project_name: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get pipeline execution history"""
        # In real implementation, this would fetch from a database
        # For now, return empty list
        return []
    
    def get_pipeline_metrics(self, project_name: str) -> Dict[str, Any]:
        """Get pipeline metrics"""
        builds = self.build_executor.get_builds_by_project(project_name)
        deployments = self.deployment_executor.get_deployments_by_project(project_name)
        
        if not builds:
            return {}
        
        # Calculate success rate
        successful_builds = [b for b in builds if b.build_status == BuildStatus.SUCCESS]
        successful_deployments = [d for d in deployments if d.deployment_status == DeploymentStatus.SUCCESS]
        
        build_success_rate = len(successful_builds) / len(builds) if builds else 0
        deployment_success_rate = len(successful_deployments) / len(deployments) if deployments else 0
        
        # Average build time
        avg_build_time = sum(b.duration or 0 for b in builds) / len(builds) if builds else 0
        
        # Average deployment time
        avg_deployment_time = sum(d.duration or 0 for d in deployments) / len(deployments) if deployments else 0
        
        return {
            "total_builds": len(builds),
            "successful_builds": len(successful_builds),
            "build_success_rate": build_success_rate,
            "total_deployments": len(deployments),
            "successful_deployments": len(successful_deployments),
            "deployment_success_rate": deployment_success_rate,
            "average_build_time": avg_build_time,
            "average_deployment_time": avg_deployment_time,
            "total_pipelines": len(self.get_pipeline_configs_by_project(project_name))
        }