from typing import Dict, Any, Optional
import requests
import asyncio
import json
from datetime import datetime
from fastapi import HTTPException
import subprocess
import os

class HermesIntegration:
    """Integration layer between Hermes Agent and Atsawin Core"""
    
    def __init__(self):
        self.api_url = "http://localhost:8000"
        self.hermes_config_path = "/root/.hermes/config.yaml"
        self.enabled = True
    
    async def execute_autonomous_task(self, task: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Execute task autonomously using Hermes Agent"""
        if not self.enabled:
            raise HTTPException(status_code=503, detail="Hermes integration disabled")
        
        try:
            # Prepare task for Hermes
            task_payload = {
                "task": task,
                "timestamp": datetime.now().isoformat(),
                "context": context or {},
                "system": "atsawin-ai-core"
            }
            
            # Use hermes CLI to execute task
            result = await self._run_hermes_command(task)
            
            return {
                "success": True,
                "task": task,
                "result": result,
                "timestamp": datetime.now().isoformat(),
                "executor": "hermes-agent"
            }
            
        except Exception as e:
            return {
                "success": False,
                "task": task,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "executor": "hermes-agent"
            }
    
    async def _run_hermes_command(self, task: str) -> str:
        """Execute command through Hermes CLI"""
        try:
            # Use subprocess to run hermes command
            cmd = ["hermes", "-q", task]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
                cwd="/root/Atsawin-AI-Core"
            )
            
            if result.returncode == 0:
                return result.stdout
            else:
                return f"Error: {result.stderr}"
                
        except subprocess.TimeoutExpired:
            return "Error: Task execution timeout"
        except Exception as e:
            return f"Error: {str(e)}"
    
    async def list_available_skills(self) -> Dict[str, Any]:
        """List available Hermes skills"""
        try:
            result = subprocess.run(
                ["hermes", "skills", "list"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                return {"skills": result.stdout}
            else:
                return {"error": result.stderr}
                
        except Exception as e:
            return {"error": str(e)}
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status"""
        try:
            # Check Hermes Agent status
            hermes_status = "unknown"
            try:
                result = subprocess.run(
                    ["hermes", "--version"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    hermes_status = "running"
                else:
                    hermes_status = "error"
            except:
                hermes_status = "not_running"
            
            # Check backend API
            api_status = "unknown"
            try:
                response = requests.get(f"{self.api_url}/health", timeout=5)
                if response.status_code == 200:
                    api_status = "running"
                else:
                    api_status = "error"
            except:
                api_status = "not_running"
            
            # Check Docker services
            docker_status = "unknown"
            try:
                result = subprocess.run(
                    ["docker", "ps"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    docker_status = "running"
                else:
                    docker_status = "error"
            except:
                docker_status = "not_running"
            
            return {
                "hermes_agent": hermes_status,
                "backend_api": api_status,
                "docker_services": docker_status,
                "integration_enabled": self.enabled,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

# Global instance
hermes_integration = HermesIntegration()