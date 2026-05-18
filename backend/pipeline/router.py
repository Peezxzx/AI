"""
Pipeline API Router - REST endpoints for autonomous coding pipeline
"""
import json
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from datetime import datetime
from .models import (
    PipelineRequest, PipelineResult, PipelineReport,
    FileAction, TestType, CICDEnvironment,
)
from .engine import (
    run_pipeline, get_pipeline_status, get_pipeline_report, list_pipelines,
)
from .scanner import scan_project
from .quality import analyze_quality
from .git_manager import (
    get_git_status, git_commit, git_create_branch, git_log, git_diff,
)
from .cicd import trigger_cicd, get_cicd_status, list_cicd_runs
from .testing import run_tests, get_test_run, list_test_runs

router = APIRouter(prefix="/pipeline", tags=["pipeline"])


def _parse_file_plan_item(item: dict) -> dict:
    """Parse a file plan item from request JSON."""
    return {
        "action": FileAction(item.get("action", "create")),
        "path": item["path"],
        "content": item.get("content"),
        "old_string": item.get("old_string"),
        "new_string": item.get("new_string"),
        "overwrite": item.get("overwrite", False),
        "replace_all": item.get("replace_all", False),
    }


# ─── Pipeline Execution ─────────────────────────────────────

@router.post("/run")
async def pipeline_run(request: dict):
    """Run the autonomous coding pipeline."""
    try:
        plan_items = [_parse_file_plan_item(item) for item in request.get("plan", [])]
        pipeline_request = PipelineRequest(
            plan=plan_items,
            scan_only=request.get("scan_only", False),
            update_memory=request.get("update_memory", False),
            dry_run=request.get("dry_run", False),
        )
        result = await run_pipeline(pipeline_request)
        return {
            "pipeline_id": result.pipeline_id,
            "status": result.status.value,
            "submitted_at": result.started_at.isoformat() if result.started_at else None,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid plan format: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline error: {str(e)}")


@router.get("/status/{pipeline_id}")
async def pipeline_status(pipeline_id: str):
    """Get pipeline execution status."""
    result = get_pipeline_status(pipeline_id)
    if not result:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    return {
        "pipeline_id": result.pipeline_id,
        "status": result.status.value,
        "phase": result.phase.value,
        "progress": result.progress,
        "files_created": result.files_created,
        "files_modified": result.files_modified,
        "errors": result.errors,
        "started_at": result.started_at.isoformat() if result.started_at else None,
        "completed_at": result.completed_at.isoformat() if result.completed_at else None,
        "duration_seconds": result.duration_seconds,
    }


@router.get("/report/{pipeline_id}")
async def pipeline_report(pipeline_id: str):
    """Get pipeline execution report."""
    report = get_pipeline_report(pipeline_id)
    if not report:
        raise HTTPException(status_code=404, detail="Pipeline report not found")

    return {
        "pipeline_id": report.pipeline_id,
        "success": report.success,
        "phase_reached": report.phase_reached,
        "tasks_total": report.tasks_total,
        "tasks_completed": report.tasks_completed,
        "tasks_failed": report.tasks_failed,
        "files_created": report.files_created,
        "files_modified": report.files_modified,
        "scan_summary": report.scan_summary,
        "errors": report.errors,
        "duration_seconds": report.duration_seconds,
    }


@router.get("/list")
async def pipeline_list():
    """List all pipeline runs."""
    pipelines = list_pipelines()
    return [
        {
            "pipeline_id": p.pipeline_id,
            "status": p.status.value,
            "phase": p.phase.value,
            "progress": p.progress,
            "started_at": p.started_at.isoformat() if p.started_at else None,
        }
        for p in pipelines
    ]


# ─── Project Scan ───────────────────────────────────────────

@router.get("/scan")
async def project_scan(path: str = Query(default=".", description="Project root path")):
    """Scan project structure and analyze code."""
    try:
        result = scan_project(path)
        return {
            "total_files": result.total_files,
            "languages": result.languages,
            "total_lines": result.total_lines,
            "dependencies": result.dependencies,
            "structure": result.structure,
            "scanned_at": result.scanned_at.isoformat() if result.scanned_at else None,
        }
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Path not found: {path}")
    except NotADirectoryError:
        raise HTTPException(status_code=400, detail=f"Not a directory: {path}")


# ─── Code Quality ───────────────────────────────────────────

@router.post("/quality/analyze")
async def quality_analyze(request: dict):
    """Analyze code quality."""
    try:
        result = analyze_quality(
            path=request.get("path", "."),
            checks=request.get("checks", ["all"]),
        )
        return {
            "path": result.path,
            "overall_score": round(result.overall_score, 3),
            "issues": [
                {
                    "type": issue.type,
                    "severity": issue.severity.value,
                    "file": issue.file,
                    "line": issue.line,
                    "message": issue.message,
                    "suggestion": issue.suggestion,
                }
                for issue in result.issues
            ],
            "metrics": result.metrics,
        }
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Path not found: {request.get('path', '.')}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Quality check failed: {str(e)}")


# ─── Git Integration ────────────────────────────────────────

@router.get("/git/status")
async def git_status(repo_path: str = Query(default=".")):
    """Get git repository status."""
    try:
        result = get_git_status(repo_path)
        return {
            "branch": result.branch,
            "clean": result.clean,
            "modified_files": result.modified_files,
            "untracked_files": result.untracked_files,
            "last_commit": result.last_commit,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Git status failed: {str(e)}")


@router.post("/git/commit")
async def git_commit_endpoint(request: dict):
    """Create a git commit."""
    try:
        result = git_commit(
            message=request["message"],
            files=request.get("files"),
            push=request.get("push", False),
            repo_path=request.get("repo_path", "."),
        )
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Git commit failed: {str(e)}")


@router.post("/git/branch")
async def git_branch_endpoint(request: dict):
    """Create a new git branch."""
    try:
        result = git_create_branch(
            branch_name=request["branch_name"],
            from_branch=request.get("from_branch", "main"),
            checkout=request.get("checkout", True),
            repo_path=request.get("repo_path", "."),
        )
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Git branch failed: {str(e)}")


@router.get("/git/log")
async def git_log_endpoint(count: int = Query(default=20, le=100), repo_path: str = Query(default=".")):
    """Get recent git commit log."""
    return git_log(count=count, repo_path=repo_path)


@router.get("/git/diff")
async def git_diff_endpoint(cached: bool = Query(default=False), repo_path: str = Query(default=".")):
    """Get git diff."""
    return {"diff": git_diff(repo_path=repo_path, cached=cached)}


# ─── CI/CD ──────────────────────────────────────────────────

@router.post("/cicd/trigger")
async def cicd_trigger(request: dict):
    """Trigger a CI/CD pipeline run."""
    try:
        result = await trigger_cicd(
            environment=CICDEnvironment(request.get("environment", "development")),
            tests=request.get("tests", True),
            lint=request.get("lint", True),
            build=request.get("build", True),
            deploy=request.get("deploy", False),
            repo_path=request.get("repo_path", "."),
        )
        return {
            "run_id": result.run_id,
            "status": result.status,
            "environment": result.environment,
            "triggered_at": result.started_at.isoformat() if result.started_at else None,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"CI/CD trigger failed: {str(e)}")


@router.get("/cicd/status/{run_id}")
async def cicd_status(run_id: str):
    """Get CI/CD run status."""
    result = get_cicd_status(run_id)
    if not result:
        raise HTTPException(status_code=404, detail="CI/CD run not found")

    return {
        "run_id": result.run_id,
        "status": result.status,
        "environment": result.environment,
        "stages": [
            {"name": s.name, "status": s.status, "duration_seconds": s.duration_seconds}
            for s in result.stages
        ],
        "started_at": result.started_at.isoformat() if result.started_at else None,
        "completed_at": result.completed_at.isoformat() if result.completed_at else None,
    }


@router.get("/cicd/list")
async def cicd_list():
    """List all CI/CD runs."""
    runs = list_cicd_runs()
    return [
        {
            "run_id": r.run_id,
            "status": r.status,
            "environment": r.environment,
            "started_at": r.started_at.isoformat() if r.started_at else None,
        }
        for r in runs
    ]


# ─── Testing ────────────────────────────────────────────────

@router.post("/tests/run")
async def tests_run(request: dict):
    """Run tests."""
    try:
        result = await run_tests(
            path=request.get("path", "."),
            test_type=TestType(request.get("test_type", "all")),
            coverage=request.get("coverage", True),
            parallel=request.get("parallel", True),
        )
        return {
            "test_run_id": result.test_run_id,
            "status": result.status,
            "total_tests": result.total_tests,
            "passed": result.passed,
            "failed": result.failed,
            "skipped": result.skipped,
            "coverage_percentage": result.coverage_percentage,
            "duration_seconds": result.duration_seconds,
            "failures": [
                {"test_name": f.test_name, "file": f.file, "line": f.line, "error": f.error}
                for f in result.failures
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Test execution failed: {str(e)}")


@router.get("/tests/{test_run_id}")
async def tests_status(test_run_id: str):
    """Get test run status."""
    result = get_test_run(test_run_id)
    if not result:
        raise HTTPException(status_code=404, detail="Test run not found")

    return {
        "test_run_id": result.test_run_id,
        "status": result.status,
        "total_tests": result.total_tests,
        "passed": result.passed,
        "failed": result.failed,
        "skipped": result.skipped,
        "coverage_percentage": result.coverage_percentage,
        "duration_seconds": result.duration_seconds,
        "failures": [
            {"test_name": f.test_name, "file": f.file, "line": f.line, "error": f.error}
            for f in result.failures
        ],
    }


@router.get("/tests")
async def tests_list():
    """List all test runs."""
    runs = list_test_runs()
    return [
        {
            "test_run_id": r.test_run_id,
            "status": r.status,
            "total_tests": r.total_tests,
            "passed": r.passed,
            "failed": r.failed,
        }
        for r in runs
    ]
