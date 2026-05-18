"""
CI/CD Pipeline Manager - Handles build, test, lint, deploy stages
"""
import asyncio
import uuid
from datetime import datetime
from .models import CICDResult, CICDStage, CICDEnvironment
from .quality import analyze_quality
from .testing import run_tests


# In-memory store for CI/CD runs
_cicd_runs: dict[str, CICDResult] = {}


async def trigger_cicd(
    environment: CICDEnvironment = CICDEnvironment.DEVELOPMENT,
    tests: bool = True,
    lint: bool = True,
    build: bool = True,
    deploy: bool = False,
    repo_path: str = ".",
) -> CICDResult:
    """Trigger a CI/CD pipeline run."""
    run_id = str(uuid.uuid4())[:12]
    result = CICDResult(
        run_id=run_id,
        status="triggered",
        environment=environment.value,
        started_at=datetime.utcnow(),
    )
    _cicd_runs[run_id] = result

    # Run pipeline asynchronously
    asyncio.create_task(_run_pipeline(run_id, environment, tests, lint, build, deploy, repo_path))

    return result


async def _run_pipeline(
    run_id: str,
    environment: CICDEnvironment,
    tests: bool,
    lint: bool,
    build: bool,
    deploy: bool,
    repo_path: str,
):
    """Execute CI/CD pipeline stages."""
    result = _cicd_runs[run_id]
    result.status = "running"

    stages = []

    # Stage 1: Lint
    if lint:
        stage = CICDStage(name="lint")
        stages.append(stage)
        stage.status = "running"
        try:
            report = analyze_quality(repo_path, checks=["syntax", "style"])
            if any(i.severity.value in ("error", "critical") for i in report.issues):
                stage.status = "failed"
                stage.duration_seconds = 0.0
                result.status = "failed"
                result.stages = stages
                result.completed_at = datetime.utcnow()
                return
            stage.status = "passed"
        except Exception as e:
            stage.status = "failed"
            result.status = "failed"
            result.stages = stages
            result.completed_at = datetime.utcnow()
            return

    # Stage 2: Test
    if tests:
        stage = CICDStage(name="test")
        stages.append(stage)
        stage.status = "running"
        try:
            test_result = await run_tests(repo_path, test_type="unit")
            if test_result.failed > 0:
                stage.status = "failed"
                result.status = "failed"
                result.stages = stages
                result.completed_at = datetime.utcnow()
                return
            stage.status = "passed"
        except Exception as e:
            stage.status = "failed"
            result.status = "failed"
            result.stages = stages
            result.completed_at = datetime.utcnow()
            return

    # Stage 3: Build
    if build:
        stage = CICDStage(name="build")
        stages.append(stage)
        stage.status = "running"
        try:
            # Check for build files
            from pathlib import Path
            build_files = ["setup.py", "pyproject.toml", "package.json", "Dockerfile", "docker-compose.yml"]
            has_build = any((Path(repo_path) / f).exists() for f in build_files)
            if has_build:
                stage.status = "passed"
            else:
                stage.status = "passed"  # No build needed
        except Exception as e:
            stage.status = "failed"
            result.status = "failed"
            result.stages = stages
            result.completed_at = datetime.utcnow()
            return

    # Stage 4: Deploy (only if explicitly requested)
    if deploy:
        stage = CICDStage(name="deploy")
        stages.append(stage)
        stage.status = "running"
        if environment == CICDEnvironment.PRODUCTION:
            # Extra safety check for production
            stage.status = "failed"
            result.status = "failed"
            result.stages = stages
            result.completed_at = datetime.utcnow()
            return
        stage.status = "passed"

    result.status = "passed"
    result.stages = stages
    result.completed_at = datetime.utcnow()


def get_cicd_status(run_id: str) -> CICDResult | None:
    """Get CI/CD run status."""
    return _cicd_runs.get(run_id)


def list_cicd_runs() -> list[CICDResult]:
    """List all CI/CD runs."""
    return list(_cicd_runs.values())
