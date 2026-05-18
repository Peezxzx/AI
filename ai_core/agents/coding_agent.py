"""
Enhanced Coding Agent - Specialized agent for coding tasks with communication capabilities
"""

import asyncio
import subprocess
import sys
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

from .enhanced_agent import EnhancedAgent, AgentCapability


class EnhancedCodingAgent(EnhancedAgent):
    """Enhanced coding agent with advanced capabilities"""
    
    def __init__(self, agent_id: str, communication_manager):
        capabilities = [
            AgentCapability.CODING.value,
            AgentCapability.DATA_ANALYSIS.value,
            AgentCapability.SYSTEM_ADMIN.value
        ]
        
        super().__init__(agent_id, capabilities, communication_manager)
        
        # Coding-specific attributes
        self.code_repository = "/tmp/coding_workspace"
        self.supported_languages = ["python", "javascript", "typescript", "java", "c++", "go", "rust"]
        self.testing_frameworks = ["pytest", "unittest", "jest", "mocha"]
        
        # Initialize workspace
        self._initialize_workspace()
    
    def _initialize_workspace(self):
        """Initialize coding workspace"""
        os.makedirs(self.code_repository, exist_ok=True)
        os.makedirs(f"{self.code_repository}/projects", exist_ok=True)
        os.makedirs(f"{self.code_repository}/temp", exist_ok=True)
    
    async def execute_task(self, task_id: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute coding task"""
        task_type = task_data.get("task_type", "unknown")
        
        try:
            if task_type == "code_generation":
                return await self._generate_code(task_data)
            elif task_type == "code_analysis":
                return await self._analyze_code(task_data)
            elif task_type == "code_review":
                return await self._review_code(task_data)
            elif task_type == "code_testing":
                return await self._test_code(task_data)
            elif task_type == "bug_fixing":
                return await self._fix_bugs(task_data)
            elif task_type == "refactoring":
                return await self._refactor_code(task_data)
            elif task_type == "deployment":
                return await self._deploy_code(task_data)
            else:
                return {"status": "error", "message": f"Unknown task type: {task_type}"}
        
        except Exception as e:
            raise Exception(f"Task execution failed: {str(e)}")
    
    async def _generate_code(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate code based on requirements"""
        requirements = task_data.get("requirements", "")
        language = task_data.get("language", "python")
        project_name = task_data.get("project_name", "generated_project")
        
        if not requirements:
            raise ValueError("Requirements are required for code generation")
        
        if language not in self.supported_languages:
            raise ValueError(f"Unsupported language: {language}")
        
        # Create project directory
        project_dir = f"{self.code_repository}/projects/{project_name}"
        os.makedirs(project_dir, exist_ok=True)
        
        # Generate code structure
        code_structure = self._analyze_requirements(requirements, language)
        
        # Generate code files
        generated_files = []
        for file_info in code_structure:
            file_path = os.path.join(project_dir, file_info["file_name"])
            
            with open(file_path, 'w') as f:
                f.write(file_info["content"])
            
            generated_files.append({
                "file_name": file_info["file_name"],
                "file_path": file_path,
                "size": len(file_info["content"])
            })
        
        # Generate README
        readme_content = self._generate_readme(requirements, project_name, language)
        with open(os.path.join(project_dir, "README.md"), 'w') as f:
            f.write(readme_content)
        
        return {
            "status": "success",
            "project_name": project_name,
            "project_path": project_dir,
            "generated_files": generated_files,
            "language": language,
            "requirements_summary": requirements[:200] + "..." if len(requirements) > 200 else requirements
        }
    
    def _analyze_requirements(self, requirements: str, language: str) -> List[Dict[str, Any]]:
        """Analyze requirements and generate code structure"""
        # This is a simplified version - in real implementation, use AI for analysis
        structure = []
        
        # Generate main file
        if language == "python":
            structure.append({
                "file_name": "main.py",
                "content": f"""
# {requirements}
import sys
import json
from datetime import datetime

def main():
    print(f"Starting application at {{datetime.now()}}")
    print(f"Requirements: {requirements}")
    
    # TODO: Implement based on requirements
    pass

if __name__ == "__main__":
    main()
"""
            })
            
            # Generate requirements.txt
            structure.append({
                "file_name": "requirements.txt",
                "content": "# Python dependencies\n"
            })
            
        elif language == "javascript":
            structure.append({
                "file_name": "index.js",
                "content": f"""
// {requirements}
const startTime = new Date();
console.log(`Starting application at ${{startTime.toISOString()}}`);
console.log(`Requirements: ${{requirements}}`);

// TODO: Implement based on requirements
"""
            })
            
            # Generate package.json
            structure.append({
                "file_name": "package.json",
                "content": """{
  "name": "generated-project",
  "version": "1.0.0",
  "description": "Generated project",
  "main": "index.js",
  "scripts": {
    "start": "node index.js",
    "test": "echo \\"Error: no test specified\\" && exit 1"
  },
  "keywords": [],
  "author": "",
  "license": "ISC"
}
"""
            })
        
        return structure
    
    def _generate_readme(self, requirements: str, project_name: str, language: str) -> str:
        """Generate README file"""
        return f"""# {project_name}

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Requirements

{requirements}

## Setup

### Prerequisites

- {language.capitalize()} {language.upper() if language == 'python' else 'runtime'}

### Installation

```bash
# Install dependencies
pip install -r requirements.txt  # Python
npm install                       # JavaScript
```

### Running

```bash
# Run the application
python main.py                    # Python
npm start                        # JavaScript
```

## Project Structure

This project was generated based on the specified requirements.

## Notes

- This is a generated template
- Implementation needs to be completed based on specific requirements
- Add proper error handling and testing
"""
    
    async def _analyze_code(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze code quality and structure"""
        file_path = task_data.get("file_path")
        if not file_path or not os.path.exists(file_path):
            raise ValueError("Invalid file path")
        
        try:
            with open(file_path, 'r') as f:
                code = f.read()
        except Exception as e:
            raise Exception(f"Failed to read file: {str(e)}")
        
        # Basic code analysis
        analysis = {
            "file_path": file_path,
            "file_size": len(code),
            "line_count": len(code.split('\n')),
            "functions": self._count_functions(code),
            "classes": self._count_classes(code),
            "complexity_score": self._calculate_complexity(code),
            "issues": self._find_issues(code)
        }
        
        return {
            "status": "success",
            "analysis": analysis
        }
    
    def _count_functions(self, code: str) -> int:
        """Count number of functions in code"""
        lines = code.split('\n')
        count = 0
        for line in lines:
            line = line.strip()
            if line.startswith('def ') or line.startswith('function ') or line.startswith('const '):
                count += 1
        return count
    
    def _count_classes(self, code: str) -> int:
        """Count number of classes in code"""
        lines = code.split('\n')
        count = 0
        for line in lines:
            line = line.strip()
            if line.startswith('class '):
                count += 1
        return count
    
    def _calculate_complexity(self, code: str) -> float:
        """Calculate code complexity score (simplified)"""
        lines = code.split('\n')
        complexity = 0.0
        
        for line in lines:
            line = line.strip()
            if line.count('if') + line.count('elif') + line.count('else'):
                complexity += 1
            if line.count('for') + line.count('while'):
                complexity += 1
            if line.count('try') + line.count('except') + line.count('catch'):
                complexity += 1
        
        return min(complexity / len(lines) * 10, 10.0)  # Normalize to 0-10
    
    def _find_issues(self, code: str) -> List[Dict[str, Any]]:
        """Find potential issues in code"""
        issues = []
        
        # Check for TODO comments
        lines = code.split('\n')
        for i, line in enumerate(lines, 1):
            if 'TODO' in line or 'FIXME' in line:
                issues.append({
                    "type": "todo_comment",
                    "line": i,
                    "message": f"Found {line.strip()}",
                    "severity": "low"
                })
        
        # Check for hardcoded values
        for i, line in enumerate(lines, 1):
            if 'localhost' in line or '127.0.0.1' in line:
                issues.append({
                    "type": "hardcoded_value",
                    "line": i,
                    "message": "Hardcoded localhost/127.0.0.1 found",
                    "severity": "medium"
                })
        
        return issues
    
    async def _review_code(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Review code for quality and best practices"""
        file_path = task_data.get("file_path")
        if not file_path or not os.path.exists(file_path):
            raise ValueError("Invalid file path")
        
        try:
            with open(file_path, 'r') as f:
                code = f.read()
        except Exception as e:
            raise Exception(f"Failed to read file: {str(e)}")
        
        review = {
            "file_path": file_path,
            "overall_score": 0.0,
            "categories": {},
            "suggestions": [],
            "strengths": []
        }
        
        # Code length review
        line_count = len(code.split('\n'))
        if line_count < 20:
            review["categories"]["length"] = {"score": 8.0, "comment": "Code is concise"}
        elif line_count > 500:
            review["categories"]["length"] = {"score": 4.0, "comment": "Code is very long, consider breaking down"}
        else:
            review["categories"]["length"] = {"score": 6.0, "comment": "Code length is acceptable"}
        
        # Documentation review
        docstring_count = code.count('"""') + code.count("'''")
        if docstring_count > 0:
            review["categories"]["documentation"] = {"score": 7.0, "comment": "Has some documentation"}
            review["strengths"].append("Contains docstrings/comments")
        else:
            review["categories"]["documentation"] = {"score": 3.0, "comment": "Missing documentation"}
            review["suggestions"].append("Add docstrings and comments")
        
        # Error handling review
        if 'try:' in code and ('except:' in code or 'catch:' in code):
            review["categories"]["error_handling"] = {"score": 7.0, "comment": "Has error handling"}
            review["strengths"].append("Includes error handling")
        else:
            review["categories"]["error_handling"] = {"score": 3.0, "comment": "Missing error handling"}
            review["suggestions"].append("Add try-catch blocks")
        
        # Calculate overall score
        scores = [cat["score"] for cat in review["categories"].values()]
        review["overall_score"] = sum(scores) / len(scores) if scores else 0.0
        
        return {
            "status": "success",
            "review": review
        }
    
    async def _test_code(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Test code using appropriate testing framework"""
        file_path = task_data.get("file_path")
        if not file_path or not os.path.exists(file_path):
            raise ValueError("Invalid file path")
        
        # Determine testing command based on language
        if file_path.endswith('.py'):
            command = ["python", "-m", "pytest", file_path, "-v"]
        elif file_path.endswith('.js'):
            command = ["npm", "test", file_path]
        else:
            return {
                "status": "error",
                "message": "Testing not supported for this file type"
            }
        
        try:
            # Run tests
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            return {
                "status": "success" if result.returncode == 0 else "failed",
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "command": " ".join(command)
            }
        
        except subprocess.TimeoutExpired:
            return {
                "status": "error",
                "message": "Test execution timed out"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Test execution failed: {str(e)}"
            }
    
    async def _fix_bugs(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fix bugs in code"""
        file_path = task_data.get("file_path")
        if not file_path or not os.path.exists(file_path):
            raise ValueError("Invalid file_path")
        
        try:
            with open(file_path, 'r') as f:
                code = f.read()
        except Exception as e:
            raise Exception(f"Failed to read file: {str(e)}")
        
        # Basic bug fixes (simplified)
        fixed_code = code
        
        # Fix common syntax issues
        fixed_code = fixed_code.replace('  ', ' ')  # Remove extra spaces
        fixed_code = fixed_code.replace('\t', '    ')  # Replace tabs with spaces
        
        # Write fixed code
        backup_path = file_path + '.backup'
        with open(backup_path, 'w') as f:
            f.write(code)
        
        with open(file_path, 'w') as f:
            f.write(fixed_code)
        
        return {
            "status": "success",
            "backup_path": backup_path,
            "changes_made": "Basic formatting and syntax fixes applied"
        }
    
    async def _refactor_code(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Refactor code for better structure"""
        file_path = task_data.get("file_path")
        if not file_path or not os.path.exists(file_path):
            raise ValueError("Invalid file_path")
        
        try:
            with open(file_path, 'r') as f:
                code = f.read()
        except Exception as e:
            raise Exception(f"Failed to read file: {str(e)}")
        
        # Basic refactoring (simplified)
        refactored_code = code
        
        # Add proper error handling
        if 'try:' not in refactored_code:
            refactored_code = refactored_code.replace(
                'function main()',
                """def main():
    try:"""
            )
            refactored_code += """
    except Exception as e:
        print(f"Error occurred: {e}")
        return 1
    return 0"""
        
        # Write refactored code
        backup_path = file_path + '.refactor_backup'
        with open(backup_path, 'w') as f:
            f.write(code)
        
        with open(file_path, 'w') as f:
            f.write(refactored_code)
        
        return {
            "status": "success",
            "backup_path": backup_path,
            "refactoring_applied": "Added error handling structure"
        }
    
    async def _deploy_code(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Deploy code to development environment"""
        project_path = task_data.get("project_path")
        if not project_path or not os.path.exists(project_path):
            raise ValueError("Invalid project path")
        
        try:
            # Run deployment commands
            commands = [
                ["git", "init"],
                ["git", "add", "."],
                ["git", "commit", "-m", "Initial commit"],
                ["pip", "install", "-r", "requirements.txt"] if os.path.exists("requirements.txt") else None,
                ["npm", "install"] if os.path.exists("package.json") else None
            ]
            
            results = []
            for cmd in commands:
                if cmd:
                    try:
                        result = subprocess.run(
                            cmd,
                            cwd=project_path,
                            capture_output=True,
                            text=True,
                            timeout=60
                        )
                        results.append({
                            "command": " ".join(cmd),
                            "success": result.returncode == 0,
                            "output": result.stdout + result.stderr
                        })
                    except Exception as e:
                        results.append({
                            "command": " ".join(cmd),
                            "success": False,
                            "output": str(e)
                        })
            
            return {
                "status": "success",
                "deployment_results": results,
                "project_path": project_path
            }
        
        except Exception as e:
            raise Exception(f"Deployment failed: {str(e)}")
    
    def get_coding_metrics(self) -> Dict[str, Any]:
        """Get coding-specific metrics"""
        projects = []
        projects_dir = f"{self.code_repository}/projects"
        
        if os.path.exists(projects_dir):
            for item in os.listdir(projects_dir):
                project_path = os.path.join(projects_dir, item)
                if os.path.isdir(project_path):
                    project_size = 0
                    file_count = 0
                    
                    for root, dirs, files in os.walk(project_path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            project_size += os.path.getsize(file_path)
                            file_count += 1
                    
                    projects.append({
                        "name": item,
                        "path": project_path,
                        "size": project_size,
                        "file_count": file_count
                    })
        
        return {
            "workspace_path": self.code_repository,
            "total_projects": len(projects),
            "projects": projects,
            "supported_languages": self.supported_languages,
            "testing_frameworks": self.testing_frameworks
        }