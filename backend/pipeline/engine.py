"""
Pipeline Orchestrator - Coordinates the autonomous coding pipeline
"""
import asyncio
import uuid
from datetime import datetime
from pathlib import Path
from .models import (
    PipelineRequest, PipelineResult, PipelineReport,
    PipelinePhase, PipelineStatus, FileAction,
)
from .scanner import scan_project
from .quality import analyze_quality
from .git_manager import get_git_status, git_commit
from .cicd import trigger_cicd
from .testing import run_tests


# In-memory store for pipeline runs
_pipeline_runs: dict[str, PipelineResult] = {}
_pipeline_reports: dict[str, PipelineReport] = {}


async def run_pipeline(request: PipelineRequest) -> PipelineResult:
    """Execute the autonomous coding pipeline."""
    pipeline_id = str(uuid.uuid4())[:12]
    result = PipelineResult(
        pipeline_id=pipeline_id,
        status=PipelineStatus.STARTED,
        phase=PipelinePhase.IDLE,
        started_at=datetime.utcnow(),
    )
    _pipeline_runs[pipeline_id] = result

    # Execute pipeline asynchronously
    asyncio.create_task(_execute_pipeline(pipeline_id, request))

    return result


async def _execute_pipeline(pipeline_id: str, request: PipelineRequest):
    """Execute pipeline phases."""
    result = _pipeline_runs[pipeline_id]
    report = PipelineReport(pipeline_id=pipeline_id)
    report.tasks_total = len(request.plan)

    try:
        # Phase 1: Scanning
        result.phase = PipelinePhase.SCANNING
        result.progress = 0.1
        scan_result = scan_project(".")
        report.scan_summary = {
            "total_files": scan_result.total_files,
            "languages": scan_result.languages,
            "total_lines": scan_result.total_lines,
        }

        if request.scan_only:
            result.phase = PipelinePhase.COMPLETED
            result.status = PipelineStatus.COMPLETED
            result.progress = 1.0
            result.completed_at = datetime.utcnow()
            report.success = True
            report.phase_reached = "scanning"
            _pipeline_reports[pipeline_id] = report
            return

        # Phase 2: Planning (validate plan)
        result.phase = PipelinePhase.PLANNING
        result.progress = 0.2
        for item in request.plan:
            if item.action == FileAction.PATCH:
                if not item.old_string or not item.new_string:
                    result.errors.append(f"Patch action requires old_string and new_string for {item.path}")
            elif item.action in (FileAction.CREATE, FileAction.MODIFY, FileAction.APPEND):
                if item.content is None and item.action != FileAction.APPEND:
                    result.errors.append(f"Create/Modify action requires content for {item.path}")

        if result.errors:
            result.phase = PipelinePhase.FAILED
            result.status = PipelineStatus.FAILED
            result.completed_at = datetime.utcnow()
            report.phase_reached = "planning"
            report.errors = result.errors
            _pipeline_reports[pipeline_id] = report
            return

        # Phase 3: Coding (execute plan)
        result.phase = PipelinePhase.CODING
        result.progress = 0.4

        for item in request.plan:
            try:
                if request.dry_run:
                    report.tasks_completed += 1
                    continue

                file_result = _execute_file_action(item)
                if file_result:
                    if item.action == FileAction.CREATE:
                        result.files_created += 1
                    else:
                        result.files_modified += 1
                    report.tasks_completed += 1
                else:
                    report.tasks_failed += 1
                    result.errors.append(f"Failed to execute {item.action} on {item.path}")
            except Exception as e:
                report.tasks_failed += 1
                result.errors.append(f"Error on {item.path}: {str(e)}")

        # Phase 4: Validation
        result.phase = PipelinePhase.VALIDATING
        result.progress = 0.7

        # Run quality checks
        quality = analyze_quality(".", checks=["syntax", "style", "security"])
        if any(i.severity.value in ("error", "critical") for i in quality.issues):
            result.errors.append("Quality check found critical issues")

        # Run tests
        test_result = await run_tests(".", test_type="unit")
        if test_result.failed > 0:
            result.errors.append(f"Tests failed: {test_result.failed} failures")

        # Phase 5: Update memory (if requested)
        if request.update_memory:
            result.phase = PipelinePhase.UPDATING_MEMORY
            result.progress = 0.9
            # Memory update is handled by the caller via the report

        # Complete
        result.phase = PipelinePhase.COMPLETED
        result.status = PipelineStatus.COMPLETED
        result.progress = 1.0
        result.completed_at = datetime.utcnow()
        result.duration_seconds = (result.completed_at - result.started_at).total_seconds()

        report.success = len(result.errors) == 0
        report.phase_reached = "completed"
        report.files_created = result.files_created
        report.files_modified = result.files_modified
        report.errors = result.errors
        report.duration_seconds = result.duration_seconds

    except Exception as e:
        result.phase = PipelinePhase.FAILED
        result.status = PipelineStatus.FAILED
        result.completed_at = datetime.utcnow()
        result.errors.append(str(e))
        report.phase_reached = result.phase.value
        report.errors = result.errors

    _pipeline_reports[pipeline_id] = report


def _execute_file_action(item) -> bool:
    """Execute a single file action. Returns True on success."""
    filepath = Path(item.path)

    if item.action == FileAction.CREATE:
        if filepath.exists() and not item.overwrite:
            return False
        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.write_text(item.content or "", encoding="utf-8")
        return True

    elif item.action == FileAction.MODIFY:
        if not filepath.exists():
            return False
        if item.overwrite:
            filepath.write_text(item.content or "", encoding="utf-8")
        else:
            existing = filepath.read_text(encoding="utf-8")
            filepath.write_text(existing + "\n" + (item.content or ""), encoding="utf-8")
        return True

    elif item.action == FileAction.APPEND:
        filepath.parent.mkdir(parents=True, exist_ok=True)
        if filepath.exists():
            existing = filepath.read_text(encoding="utf-8")
            filepath.write_text(existing + "\n" + (item.content or ""), encoding="utf-8")
        else:
            filepath.write_text(item.content or "", encoding="utf-8")
        return True

    elif item.action == FileAction.PATCH:
        if not filepath.exists():
            return False
        content = filepath.read_text(encoding="utf-8")
        if item.old_string not in content:
            return False
        if item.replace_all:
            content = content.replace(item.old_string, item.new_string)
        else:
            content = content.replace(item.old_string, item.new_string, 1)
        filepath.write_text(content, encoding="utf-8")
        return True

    elif item.action == FileAction.DELETE:
        if filepath.exists():
            filepath.unlink()
            return True
        return False

    return False


def get_pipeline_status(pipeline_id: str) -> PipelineResult | None:
    """Get pipeline run status."""
    return _pipeline_runs.get(pipeline_id)


def get_pipeline_report(pipeline_id: str) -> PipelineReport | None:
    """Get pipeline run report."""
    return _pipeline_reports.get(pipeline_id)


def list_pipelines() -> list[PipelineResult]:
    """List all pipeline runs."""
    return list(_pipeline_runs.values())
