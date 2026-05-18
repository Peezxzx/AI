"""
Git Integration Manager - Handles git operations
"""
import subprocess
from pathlib import Path
from datetime import datetime
from .models import GitStatus


def _run_git(*args, cwd: str | None = None) -> tuple[str, str, int]:
    """Run a git command and return (stdout, stderr, returncode)."""
    cmd = ["git"] + list(args)
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=30,
        )
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except FileNotFoundError:
        return "", "git not found", 127
    except subprocess.TimeoutExpired:
        return "", "git command timed out", 124


def get_git_status(repo_path: str = ".") -> GitStatus:
    """Get current git repository status."""
    status = GitStatus()

    # Check if this is a git repo
    _, _, rc = _run_git("rev-parse", "--git-dir", cwd=repo_path)
    if rc != 0:
        status.branch = "not a git repository"
        return status

    # Get current branch
    stdout, _, rc = _run_git("branch", "--show-current", cwd=repo_path)
    if rc == 0:
        status.branch = stdout

    # Get modified and untracked files
    stdout, _, rc = _run_git("status", "--porcelain", cwd=repo_path)
    if rc == 0 and stdout:
        status.clean = False
        for line in stdout.splitlines():
            if len(line) >= 3:
                index_status = line[0]
                work_status = line[1]
                filename = line[3:]
                if index_status == "?" and work_status == "?":
                    status.untracked_files.append(filename)
                else:
                    status.modified_files.append(filename)
    else:
        status.clean = True

    # Get last commit info
    stdout, _, rc = _run_git(
        "log", "-1", "--format=%H|%s|%an|%aI", cwd=repo_path
    )
    if rc == 0 and stdout:
        parts = stdout.split("|", 3)
        if len(parts) == 4:
            status.last_commit = {
                "hash": parts[0][:12],
                "message": parts[1],
                "author": parts[2],
                "timestamp": parts[3],
            }

    return status


def git_commit(message: str, files: list[str] | None = None,
               push: bool = False, repo_path: str = ".") -> dict:
    """Create a git commit."""
    result = {"commit_hash": "", "message": message, "files_committed": 0, "pushed": False}

    # Stage files
    if files:
        for f in files:
            _, stderr, rc = _run_git("add", f, cwd=repo_path)
            if rc != 0:
                result["error"] = f"Failed to stage {f}: {stderr}"
                return result
    else:
        _, stderr, rc = _run_git("add", "-A", cwd=repo_path)
        if rc != 0:
            result["error"] = f"Failed to stage files: {stderr}"
            return result

    # Commit
    stdout, stderr, rc = _run_git("commit", "-m", message, cwd=repo_path)
    if rc != 0:
        result["error"] = f"Commit failed: {stderr}"
        return result

    # Get commit hash
    stdout, _, rc = _run_git("rev-parse", "--short", "HEAD", cwd=repo_path)
    if rc == 0:
        result["commit_hash"] = stdout

    # Count committed files
    stdout, _, rc = _run_git("diff", "--cached", "--name-only", "HEAD~1", cwd=repo_path)
    if rc == 0 and stdout:
        result["files_committed"] = len(stdout.splitlines())

    # Push if requested
    if push:
        stdout, stderr, rc = _run_git("push", cwd=repo_path)
        if rc == 0:
            result["pushed"] = True
        else:
            result["push_error"] = stderr

    return result


def git_create_branch(branch_name: str, from_branch: str = "main",
                      checkout: bool = True, repo_path: str = ".") -> dict:
    """Create a new git branch."""
    result = {"branch_name": branch_name, "created": False, "checked_out": False}

    # Create branch
    stdout, stderr, rc = _run_git("branch", branch_name, from_branch, cwd=repo_path)
    if rc != 0:
        result["error"] = f"Failed to create branch: {stderr}"
        return result

    result["created"] = True

    # Checkout if requested
    if checkout:
        _, stderr, rc = _run_git("checkout", branch_name, cwd=repo_path)
        if rc == 0:
            result["checked_out"] = True
        else:
            result["checkout_error"] = stderr

    return result


def git_log(count: int = 20, repo_path: str = ".") -> list[dict]:
    """Get recent commit log."""
    stdout, _, rc = _run_git(
        "log", f"-{count}", "--format=%H|%s|%an|%aI", cwd=repo_path
    )
    if rc != 0 or not stdout:
        return []

    commits = []
    for line in stdout.splitlines():
        parts = line.split("|", 3)
        if len(parts) == 4:
            commits.append({
                "hash": parts[0][:12],
                "message": parts[1],
                "author": parts[2],
                "timestamp": parts[3],
            })
    return commits


def git_diff(repo_path: str = ".", cached: bool = False) -> str:
    """Get git diff output."""
    args = ["diff", "--cached"] if cached else ["diff"]
    stdout, _, rc = _run_git(*args, cwd=repo_path)
    return stdout if rc == 0 else ""
