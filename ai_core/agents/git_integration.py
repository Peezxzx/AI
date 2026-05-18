"""
Git Integration - Autonomous Coding Pipeline with Git version control
"""

import os
import subprocess
import json
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import tempfile
import shutil
import asyncio
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GitOperation(Enum):
    """Git operation types"""
    CLONE = "clone"
    PULL = "pull"
    ADD = "add"
    COMMIT = "commit"
    PUSH = "push"
    BRANCH = "branch"
    MERGE = "merge"
    STATUS = "status"
    DIFF = "diff"
    LOG = "log"
    TAG = "tag"
    RESET = "reset"


class GitStatus(Enum):
    """Git repository status"""
    CLEAN = "clean"
    DIRTY = "dirty"
    AHEAD = "ahead"
    BEHIND = "behind"
    DIVERGED = "diverged"


@dataclass
class GitRepository:
    """Git repository information"""
    repo_url: str
    local_path: str
    branch: str = "main"
    commit_hash: Optional[str] = None
    status: GitStatus = GitStatus.CLEAN
    last_updated: Optional[datetime] = None
    remote_url: Optional[str] = None
    description: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "repo_url": self.repo_url,
            "local_path": self.local_path,
            "branch": self.branch,
            "commit_hash": self.commit_hash,
            "status": self.status.value,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
            "remote_url": self.remote_url,
            "description": self.description
        }


@dataclass
class GitCommit:
    """Git commit information"""
    commit_hash: str
    author: str
    email: str
    timestamp: datetime
    message: str
    files_changed: List[str]
    insertions: int
    deletions: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "commit_hash": self.commit_hash,
            "author": self.author,
            "email": self.email,
            "timestamp": self.timestamp.isoformat(),
            "message": self.message,
            "files_changed": self.files_changed,
            "insertions": self.insertions,
            "deletions": self.deletions
        }


@dataclass
class GitDiff:
    """Git diff information"""
    commit_hash: str
    file_path: str
    diff_content: str
    change_type: str  # added, modified, deleted
    insertions: int
    deletions: int


class GitManager:
    """Git operations manager"""
    
    def __init__(self, workspace_path: str = "/tmp/git_workspace"):
        self.workspace_path = workspace_path
        self.repositories: Dict[str, GitRepository] = {}
        
        # Ensure workspace exists
        os.makedirs(workspace_path, exist_ok=True)
    
    def clone_repository(self, repo_url: str, repo_name: str = None, 
                        branch: str = "main") -> Optional[str]:
        """Clone a Git repository"""
        if repo_name is None:
            repo_name = repo_url.split('/')[-1].replace('.git', '')
        
        local_path = os.path.join(self.workspace_path, repo_name)
        
        try:
            # Clone repository
            subprocess.run(
                ["git", "clone", repo_url, local_path],
                check=True,
                capture_output=True,
                text=True
            )
            
            # Get repository info
            repo = GitRepository(
                repo_url=repo_url,
                local_path=local_path,
                branch=branch
            )
            
            self.repositories[repo_name] = repo
            logger.info(f"Successfully cloned repository: {repo_url}")
            
            return repo_name
        
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to clone repository {repo_url}: {e}")
            return None
    
    def get_repository_status(self, repo_name: str) -> Optional[GitStatus]:
        """Get repository status"""
        if repo_name not in self.repositories:
            return None
        
        repo = self.repositories[repo_name]
        local_path = repo.local_path
        
        try:
            # Change to repository directory
            original_cwd = os.getcwd()
            os.chdir(local_path)
            
            # Get status
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                check=True,
                capture_output=True,
                text=True
            )
            
            # Check if working directory is clean
            if not result.stdout.strip():
                repo.status = GitStatus.CLEAN
            else:
                repo.status = GitStatus.DIRTY
            
            # Get remote status
            result = subprocess.run(
                ["git", "log", "--oneline", "@{u}.."],
                check=True,
                capture_output=True,
                text=True
            )
            
            ahead_commits = len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0
            
            result = subprocess.run(
                ["git", "log", "--oneline", "..@{u}"],
                check=True,
                capture_output=True,
                text=True
            )
            
            behind_commits = len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0
            
            if ahead_commits > 0 and behind_commits > 0:
                repo.status = GitStatus.DIVERGED
            elif ahead_commits > 0:
                repo.status = GitStatus.AHEAD
            elif behind_commits > 0:
                repo.status = GitStatus.BEHIND
            
            # Update repository info
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                check=True,
                capture_output=True,
                text=True
            )
            repo.commit_hash = result.stdout.strip()
            
            result = subprocess.run(
                ["git", "remote", "get-url", "origin"],
                check=True,
                capture_output=True,
                text=True
            )
            repo.remote_url = result.stdout.strip()
            
            repo.last_updated = datetime.now(timezone.utc)
            
            # Change back to original directory
            os.chdir(original_cwd)
            
            return repo.status
        
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to get repository status for {repo_name}: {e}")
            os.chdir(original_cwd)
            return None
    
    def add_files(self, repo_name: str, file_patterns: List[str]) -> bool:
        """Add files to git staging area"""
        if repo_name not in self.repositories:
            return False
        
        repo = self.repositories[repo_name]
        local_path = repo.local_path
        
        try:
            original_cwd = os.getcwd()
            os.chdir(local_path)
            
            # Add files
            for pattern in file_patterns:
                subprocess.run(
                    ["git", "add", pattern],
                    check=True,
                    capture_output=True,
                    text=True
                )
            
            os.chdir(original_cwd)
            logger.info(f"Successfully added files to repository {repo_name}")
            return True
        
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to add files to repository {repo_name}: {e}")
            os.chdir(original_cwd)
            return False
    
    def commit_changes(self, repo_name: str, message: str, 
                      author_name: str = "AI Agent", 
                      author_email: str = "ai@agent.local") -> Optional[str]:
        """Commit staged changes"""
        if repo_name not in self.repositories:
            return None
        
        repo = self.repositories[repo_name]
        local_path = repo.local_path
        
        try:
            original_cwd = os.getcwd()
            os.chdir(local_path)
            
            # Configure git user
            subprocess.run(
                ["git", "config", "user.name", author_name],
                check=True,
                capture_output=True,
                text=True
            )
            
            subprocess.run(
                ["git", "config", "user.email", author_email],
                check=True,
                capture_output=True,
                text=True
            )
            
            # Commit changes
            result = subprocess.run(
                ["git", "commit", "-m", message],
                check=True,
                capture_output=True,
                text=True
            )
            
            # Get commit hash
            commit_hash = result.stdout.split()[-1] if result.stdout else None
            
            os.chdir(original_cwd)
            logger.info(f"Successfully committed changes to repository {repo_name}")
            
            return commit_hash
        
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to commit changes to repository {repo_name}: {e}")
            os.chdir(original_cwd)
            return None
    
    def push_changes(self, repo_name: str, branch: str = None) -> bool:
        """Push changes to remote repository"""
        if repo_name not in self.repositories:
            return False
        
        repo = self.repositories[repo_name]
        local_path = repo.local_path
        target_branch = branch or repo.branch
        
        try:
            original_cwd = os.getcwd()
            os.chdir(local_path)
            
            # Push changes
            subprocess.run(
                ["git", "push", "origin", target_branch],
                check=True,
                capture_output=True,
                text=True
            )
            
            os.chdir(original_cwd)
            logger.info(f"Successfully pushed changes to repository {repo_name}")
            return True
        
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to push changes to repository {repo_name}: {e}")
            os.chdir(original_cwd)
            return False
    
    def pull_changes(self, repo_name: str, branch: str = None) -> bool:
        """Pull changes from remote repository"""
        if repo_name not in self.repositories:
            return False
        
        repo = self.repositories[repo_name]
        local_path = repo.local_path
        target_branch = branch or repo.branch
        
        try:
            original_cwd = os.getcwd()
            os.chdir(local_path)
            
            # Pull changes
            subprocess.run(
                ["git", "pull", "origin", target_branch],
                check=True,
                capture_output=True,
                text=True
            )
            
            os.chdir(original_cwd)
            logger.info(f"Successfully pulled changes from repository {repo_name}")
            return True
        
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to pull changes from repository {repo_name}: {e}")
            os.chdir(original_cwd)
            return False
    
    def create_branch(self, repo_name: str, branch_name: str, 
                     start_point: str = None) -> bool:
        """Create a new branch"""
        if repo_name not in self.repositories:
            return False
        
        repo = self.repositories[repo_name]
        local_path = repo.local_path
        
        try:
            original_cwd = os.getcwd()
            os.chdir(local_path)
            
            if start_point:
                subprocess.run(
                    ["git", "checkout", "-b", branch_name, start_point],
                    check=True,
                    capture_output=True,
                    text=True
                )
            else:
                subprocess.run(
                    ["git", "checkout", "-b", branch_name],
                    check=True,
                    capture_output=True,
                    text=True
                )
            
            os.chdir(original_cwd)
            logger.info(f"Successfully created branch {branch_name} in repository {repo_name}")
            return True
        
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to create branch {branch_name} in repository {repo_name}: {e}")
            os.chdir(original_cwd)
            return False
    
    def merge_branch(self, repo_name: str, source_branch: str, 
                    target_branch: str = None) -> bool:
        """Merge branches"""
        if repo_name not in self.repositories:
            return False
        
        repo = self.repositories[repo_name]
        local_path = repo.local_path
        target_branch = target_branch or repo.branch
        
        try:
            original_cwd = os.getcwd()
            os.chdir(local_path)
            
            # Switch to target branch
            subprocess.run(
                ["git", "checkout", target_branch],
                check=True,
                capture_output=True,
                text=True
            )
            
            # Merge source branch
            subprocess.run(
                ["git", "merge", source_branch],
                check=True,
                capture_output=True,
                text=True
            )
            
            os.chdir(original_cwd)
            logger.info(f"Successfully merged {source_branch} into {target_branch} in repository {repo_name}")
            return True
        
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to merge {source_branch} into {target_branch} in repository {repo_name}: {e}")
            os.chdir(original_cwd)
            return False
    
    def get_commit_history(self, repo_name: str, limit: int = 10) -> List[GitCommit]:
        """Get commit history"""
        if repo_name not in self.repositories:
            return []
        
        repo = self.repositories[repo_name]
        local_path = repo.local_path
        
        try:
            original_cwd = os.getcwd()
            os.chdir(local_path)
            
            # Get commit history
            result = subprocess.run(
                ["git", "log", "--pretty=format:%H|%an|%ae|%ad|%s", "--date=iso", f"-{limit}"],
                check=True,
                capture_output=True,
                text=True
            )
            
            commits = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    parts = line.split('|')
                    if len(parts) >= 4:
                        commit = GitCommit(
                            commit_hash=parts[0],
                            author=parts[1],
                            email=parts[2],
                            timestamp=datetime.fromisoformat(parts[3]),
                            message=parts[4],
                            files_changed=[],
                            insertions=0,
                            deletions=0
                        )
                        commits.append(commit)
            
            os.chdir(original_cwd)
            return commits
        
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to get commit history for repository {repo_name}: {e}")
            os.chdir(original_cwd)
            return []
    
    def get_diff(self, repo_name: str, commit_hash: str = None, 
                file_path: str = None) -> List[GitDiff]:
        """Get git diff"""
        if repo_name not in self.repositories:
            return []
        
        repo = self.repositories[repo_name]
        local_path = repo.local_path
        
        try:
            original_cwd = os.getcwd()
            os.chdir(local_path)
            
            # Get diff
            if commit_hash:
                if file_path:
                    result = subprocess.run(
                        ["git", "show", f"{commit_hash}:{file_path}"],
                        check=True,
                        capture_output=True,
                        text=True
                    )
                    diff_content = result.stdout
                else:
                    result = subprocess.run(
                        ["git", "show", commit_hash],
                        check=True,
                        capture_output=True,
                        text=True
                    )
                    diff_content = result.stdout
            else:
                result = subprocess.run(
                    ["git", "diff", "--stat"],
                    check=True,
                    capture_output=True,
                    text=True
                )
                diff_content = result.stdout
            
            os.chdir(original_cwd)
            
            # Parse diff (simplified)
            diffs = []
            diff = GitDiff(
                commit_hash=commit_hash or "HEAD",
                file_path=file_path or "all",
                diff_content=diff_content,
                change_type="modified",
                insertions=0,
                deletions=0
            )
            diffs.append(diff)
            
            return diffs
        
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to get diff for repository {repo_name}: {e}")
            os.chdir(original_cwd)
            return []
    
    def get_repository_info(self, repo_name: str) -> Optional[GitRepository]:
        """Get repository information"""
        if repo_name not in self.repositories:
            return None
        
        repo = self.repositories[repo_name]
        self.get_repository_status(repo_name)
        return repo
    
    def list_repositories(self) -> List[str]:
        """List all managed repositories"""
        return list(self.repositories.keys())
    
    def remove_repository(self, repo_name: str) -> bool:
        """Remove a repository"""
        if repo_name not in self.repositories:
            return False
        
        repo = self.repositories[repo_name]
        
        try:
            # Remove local repository
            if os.path.exists(repo.local_path):
                shutil.rmtree(repo.local_path)
            
            # Remove from memory
            del self.repositories[repo_name]
            
            logger.info(f"Successfully removed repository {repo_name}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to remove repository {repo_name}: {e}")
            return False


class CodingPipeline:
    """Autonomous coding pipeline with Git integration"""
    
    def __init__(self, git_manager: GitManager):
        self.git_manager = git_manager
        self.pipeline_tasks: Dict[str, Dict[str, Any]] = {}
        self.pipeline_history: List[Dict[str, Any]] = []
        self.max_history = 1000
    
    def create_pipeline_task(self, repo_name: str, task_type: str, 
                            task_data: Dict[str, Any]) -> str:
        """Create a pipeline task"""
        task_id = str(uuid.uuid4())
        
        task = {
            "task_id": task_id,
            "repo_name": repo_name,
            "task_type": task_type,
            "task_data": task_data,
            "status": "pending",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "started_at": None,
            "completed_at": None,
            "result": None,
            "error": None
        }
        
        self.pipeline_tasks[task_id] = task
        logger.info(f"Created pipeline task: {task_id} for repository {repo_name}")
        
        return task_id
    
    async def execute_pipeline_task(self, task_id: str) -> bool:
        """Execute a pipeline task"""
        if task_id not in self.pipeline_tasks:
            return False
        
        task = self.pipeline_tasks[task_id]
        task["status"] = "running"
        task["started_at"] = datetime.now(timezone.utc).isoformat()
        
        try:
            repo_name = task["repo_name"]
            task_type = task["task_type"]
            task_data = task["task_data"]
            
            # Check if repository exists
            if repo_name not in self.git_manager.list_repositories():
                raise Exception(f"Repository {repo_name} not found")
            
            # Execute task based on type
            if task_type == "code_generation":
                result = await self._execute_code_generation(repo_name, task_data)
            elif task_type == "code_refactoring":
                result = await self._execute_code_refactoring(repo_name, task_data)
            elif task_type == "bug_fix":
                result = await self._execute_bug_fix(repo_name, task_data)
            elif task_type == "feature_addition":
                result = await self._execute_feature_addition(repo_name, task_data)
            elif task_type == "documentation_update":
                result = await self._execute_documentation_update(repo_name, task_data)
            else:
                result = {"status": "error", "message": f"Unknown task type: {task_type}"}
            
            task["result"] = result
            task["status"] = "completed"
            task["completed_at"] = datetime.now(timezone.utc).isoformat()
            
            # Add to history
            self.pipeline_history.append({
                "task_id": task_id,
                "repo_name": repo_name,
                "task_type": task_type,
                "status": "completed",
                "result": result,
                "timestamp": task["completed_at"]
            })
            
            # Limit history size
            if len(self.pipeline_history) > self.max_history:
                self.pipeline_history.pop(0)
            
            logger.info(f"Completed pipeline task: {task_id}")
            return True
        
        except Exception as e:
            task["error"] = str(e)
            task["status"] = "failed"
            task["completed_at"] = datetime.now(timezone.utc).isoformat()
            
            # Add to history
            self.pipeline_history.append({
                "task_id": task_id,
                "repo_name": task["repo_name"],
                "task_type": task["task_type"],
                "status": "failed",
                "error": str(e),
                "timestamp": task["completed_at"]
            })
            
            logger.error(f"Failed pipeline task: {task_id} - {str(e)}")
            return False
    
    async def _execute_code_generation(self, repo_name: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute code generation task"""
        # Pull latest changes
        self.git_manager.pull_changes(repo_name)
        
        # Generate code (simplified)
        files_created = []
        files_modified = []
        
        # Create files based on task_data
        for file_info in task_data.get("files", []):
            file_path = file_info.get("path")
            content = file_info.get("content")
            
            if file_path and content:
                full_path = os.path.join(self.git_manager.repositories[repo_name].local_path, file_path)
                
                # Create directory if needed
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                
                # Write file
                with open(full_path, 'w') as f:
                    f.write(content)
                
                files_created.append(file_path)
        
        # Commit changes
        commit_message = task_data.get("commit_message", "AI: Generated code")
        commit_hash = self.git_manager.commit_changes(repo_name, commit_message)
        
        # Push changes
        self.git_manager.push_changes(repo_name)
        
        return {
            "status": "success",
            "files_created": files_created,
            "files_modified": files_modified,
            "commit_hash": commit_hash,
            "message": "Code generation completed successfully"
        }
    
    async def _execute_code_refactoring(self, repo_name: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute code refactoring task"""
        # Pull latest changes
        self.git_manager.pull_changes(repo_name)
        
        # Perform refactoring (simplified)
        files_refactored = []
        
        # Refactor files based on task_data
        for file_info in task_data.get("files", []):
            file_path = file_info.get("path")
            refactoring_rules = file_info.get("rules", [])
            
            if file_path and refactoring_rules:
                full_path = os.path.join(self.git_manager.repositories[repo_name].local_path, file_path)
                
                if os.path.exists(full_path):
                    # Read file
                    with open(full_path, 'r') as f:
                        content = f.read()
                    
                    # Apply refactoring rules (simplified)
                    for rule in refactoring_rules:
                        if rule["type"] == "rename_variable":
                            content = content.replace(rule["old_name"], rule["new_name"])
                        elif rule["type"] == "extract_method":
                            # Simplified method extraction
                            pass
                    
                    # Write back
                    with open(full_path, 'w') as f:
                        f.write(content)
                    
                    files_refactored.append(file_path)
        
        # Commit changes
        commit_message = task_data.get("commit_message", "AI: Refactored code")
        commit_hash = self.git_manager.commit_changes(repo_name, commit_message)
        
        # Push changes
        self.git_manager.push_changes(repo_name)
        
        return {
            "status": "success",
            "files_refactored": files_refactored,
            "commit_hash": commit_hash,
            "message": "Code refactoring completed successfully"
        }
    
    async def _execute_bug_fix(self, repo_name: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute bug fix task"""
        # Pull latest changes
        self.git_manager.pull_changes(repo_name)
        
        # Fix bugs (simplified)
        files_fixed = []
        
        for bug_info in task_data.get("bugs", []):
            file_path = bug_info.get("file_path")
            bug_description = bug_info.get("description")
            fix_code = bug_info.get("fix_code")
            
            if file_path and fix_code:
                full_path = os.path.join(self.git_manager.repositories[repo_name].local_path, file_path)
                
                if os.path.exists(full_path):
                    # Read file
                    with open(full_path, 'r') as f:
                        content = f.read()
                    
                    # Apply fix (simplified)
                    # In real implementation, this would be more sophisticated
                    content = content.replace(bug_description, fix_code)
                    
                    # Write back
                    with open(full_path, 'w') as f:
                        f.write(content)
                    
                    files_fixed.append(file_path)
        
        # Commit changes
        commit_message = task_data.get("commit_message", "AI: Fixed bugs")
        commit_hash = self.git_manager.commit_changes(repo_name, commit_message)
        
        # Push changes
        self.git_manager.push_changes(repo_name)
        
        return {
            "status": "success",
            "files_fixed": files_fixed,
            "commit_hash": commit_hash,
            "message": "Bug fixes completed successfully"
        }
    
    async def _execute_feature_addition(self, repo_name: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute feature addition task"""
        # Pull latest changes
        self.git_manager.pull_changes(repo_name)
        
        # Create feature branch
        feature_name = task_data.get("feature_name", "feature")
        branch_name = f"feature/{feature_name}"
        
        self.git_manager.create_branch(repo_name, branch_name)
        
        # Add feature code
        files_added = []
        for file_info in task_data.get("files", []):
            file_path = file_info.get("path")
            content = file_info.get("content")
            
            if file_path and content:
                full_path = os.path.join(self.git_manager.repositories[repo_name].local_path, file_path)
                
                # Create directory if needed
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                
                # Write file
                with open(full_path, 'w') as f:
                    f.write(content)
                
                files_added.append(file_path)
        
        # Commit changes
        commit_message = f"AI: Added feature {feature_name}"
        commit_hash = self.git_manager.commit_changes(repo_name, commit_message)
        
        # Merge back to main branch
        self.git_manager.merge_branch(repo_name, branch_name)
        
        # Delete feature branch
        subprocess.run(
            ["git", "branch", "-D", branch_name],
            cwd=self.git_manager.repositories[repo_name].local_path,
            check=True,
            capture_output=True,
            text=True
        )
        
        # Push changes
        self.git_manager.push_changes(repo_name)
        
        return {
            "status": "success",
            "files_added": files_added,
            "commit_hash": commit_hash,
            "message": f"Feature {feature_name} added successfully"
        }
    
    async def _execute_documentation_update(self, repo_name: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute documentation update task"""
        # Pull latest changes
        self.git_manager.pull_changes(repo_name)
        
        # Update documentation
        files_updated = []
        
        for doc_info in task_data.get("documents", []):
            file_path = doc_info.get("path")
            content = doc_info.get("content")
            
            if file_path and content:
                full_path = os.path.join(self.git_manager.repositories[repo_name].local_path, file_path)
                
                # Create directory if needed
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                
                # Write file
                with open(full_path, 'w') as f:
                    f.write(content)
                
                files_updated.append(file_path)
        
        # Commit changes
        commit_message = task_data.get("commit_message", "AI: Updated documentation")
        commit_hash = self.git_manager.commit_changes(repo_name, commit_message)
        
        # Push changes
        self.git_manager.push_changes(repo_name)
        
        return {
            "status": "success",
            "files_updated": files_updated,
            "commit_hash": commit_hash,
            "message": "Documentation updated successfully"
        }
    
    def get_pipeline_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get pipeline task status"""
        return self.pipeline_tasks.get(task_id)
    
    def get_pipeline_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get pipeline history"""
        return self.pipeline_history[-limit:]
    
    def get_pipeline_metrics(self) -> Dict[str, Any]:
        """Get pipeline metrics"""
        total_tasks = len(self.pipeline_tasks)
        completed_tasks = len([t for t in self.pipeline_tasks.values() if t["status"] == "completed"])
        failed_tasks = len([t for t in self.pipeline_tasks.values() if t["status"] == "failed"])
        running_tasks = len([t for t in self.pipeline_tasks.values() if t["status"] == "running"])
        pending_tasks = len([t for t in self.pipeline_tasks.values() if t["status"] == "pending"])
        
        success_rate = completed_tasks / total_tasks if total_tasks > 0 else 0.0
        
        task_types = {}
        for task in self.pipeline_tasks.values():
            task_type = task["task_type"]
            task_types[task_type] = task_types.get(task_type, 0) + 1
        
        return {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "failed_tasks": failed_tasks,
            "running_tasks": running_tasks,
            "pending_tasks": pending_tasks,
            "success_rate": success_rate,
            "task_types": task_types,
            "repositories_managed": len(self.git_manager.list_repositories())
        }