"""
Autonomous Coding Pipeline - Main Orchestrator

Ties all pipeline modules together into a cohesive execution flow:
  1. Scan project structure
  2. Plan changes (or execute provided plan)
  3. Write/modify files
  4. Validate changes
  5. Update memory (spec.md, hot.md)
  6. Generate report

Usage:
    from pipeline.pipeline import AutonomousPipeline
    pipeline = AutonomousPipeline()
    result = pipeline.run(plan=[{"action": "create", "path": "...", "content": "..."}])
    print(result.summary())
"""

import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

from pipeline import (
    PROJECT_ROOT, PipelineConfig, PipelineResult, PipelinePhase,
)
from pipeline.logger import get_logger, log_phase_transition
from pipeline.task_manager import TaskManager, TaskType, TaskPriority, task_manager
from pipeline.project_scanner import ProjectScanner
from pipeline.code_writer import CodeWriter
from pipeline.memory_updater import MemoryUpdater

logger = get_logger("pipeline")


class AutonomousPipeline:
    """
    Main orchestrator for the autonomous coding pipeline.

    Executes a full cycle: scan -> plan -> code -> validate -> update memory.
    Each phase is tracked via the task manager and logged.
    """

    def __init__(self, config: Optional[PipelineConfig] = None):
        self.config = config or PipelineConfig()
        self.root = PROJECT_ROOT

        # Initialize modules
        self.task_mgr = task_manager
        self.scanner = ProjectScanner(str(self.root), self.config)
        self.writer = CodeWriter(str(self.root), self.config)
        self.memory = MemoryUpdater(str(self.root))

        logger.info("AutonomousPipeline initialized")

    # ------------------------------------------------------------------
    # Main run
    # ------------------------------------------------------------------
    def run(
        self,
        plan: Optional[List[Dict[str, Any]]] = None,
        scan_only: bool = False,
    ) -> PipelineResult:
        """
        Execute the full pipeline.

        Args:
            plan: Optional list of file operations to execute.
                  Each item: {"action": "create|modify|patch|delete", "path": "...", ...}
            scan_only: If True, only scan and return report without writing.
        Returns:
            PipelineResult with execution summary.
        """
        start_time = datetime.now(timezone.utc)
        phase = PipelinePhase.IDLE
        errors: List[str] = []
        files_created = 0
        files_modified = 0

        logger.info("=" * 60)
        logger.info("AUTONOMOUS CODING PIPELINE - STARTING")
        logger.info("=" * 60)

        try:
            # ---- Phase 1: SCAN ----
            phase = PipelinePhase.SCANNING
            log_phase_transition(logger, "IDLE", "SCANNING")
            scan_task = self.task_mgr.create_task(TaskType.SCAN, "Scan project structure")
            self.task_mgr.start_task(scan_task)

            scan_report = self.scanner.scan()
            scan_summary = scan_report.summary()
            self.task_mgr.complete_task(scan_task, result=scan_summary)
            logger.info(f"Scan complete: {scan_summary['total_files']} files")

            if scan_only:
                phase = PipelinePhase.COMPLETED
                return self._build_result(
                    True, phase, start_time, files_created, files_modified,
                    scan_summary, errors
                )

            # ---- Phase 2: PLAN ----
            phase = PipelinePhase.PLANNING
            log_phase_transition(logger, "SCANNING", "PLANNING")
            plan_task = self.task_mgr.create_task(TaskType.PLAN, "Plan file operations")
            self.task_mgr.start_task(plan_task)

            if plan is None:
                plan = []  # No operations planned
                logger.info("No plan provided - running in scan-only mode with validation")

            self.task_mgr.complete_task(plan_task, result={"operations": len(plan)})

            # ---- Phase 3: CODE ----
            phase = PipelinePhase.CODING
            log_phase_transition(logger, "PLANNING", "CODING")

            for i, operation in enumerate(plan):
                action = operation.get("action", "create")
                rel_path = operation.get("path", "")

                code_task = self.task_mgr.create_task(
                    TaskType.WRITE_CODE,
                    f"{action}: {rel_path}",
                    priority=TaskPriority.NORMAL,
                    metadata={"operation_index": i, "action": action},
                )
                self.task_mgr.start_task(code_task)

                try:
                    result = self._execute_operation(operation)
                    if result.success:
                        self.task_mgr.complete_task(code_task, result=result.to_dict())
                        if result.action in ("created",):
                            files_created += 1
                        elif result.action in ("modified", "patched", "appended"):
                            files_modified += 1
                    else:
                        self.task_mgr.fail_task(code_task, result.error or "Unknown error")
                        errors.append(f"{rel_path}: {result.error}")
                except Exception as e:
                    self.task_mgr.fail_task(code_task, str(e))
                    errors.append(f"{rel_path}: {str(e)}")

            # ---- Phase 4: VALIDATE ----
            phase = PipelinePhase.VALIDATING
            log_phase_transition(logger, "CODING", "VALIDATING")
            val_task = self.task_mgr.create_task(TaskType.VALIDATE, "Validate changes")
            self.task_mgr.start_task(val_task)

            validation_errors = self._validate_changes()
            if validation_errors:
                for ve in validation_errors:
                    errors.append(f"Validation: {ve}")
                self.task_mgr.fail_task(val_task, f"{len(validation_errors)} validation errors")
            else:
                self.task_mgr.complete_task(val_task, result={"valid": True})

            # ---- Phase 5: UPDATE MEMORY ----
            phase = PipelinePhase.UPDATING_MEMORY
            log_phase_transition(logger, "VALIDATING", "UPDATING_MEMORY")
            mem_task = self.task_mgr.create_task(TaskType.UPDATE_MEMORY, "Update spec.md and hot.md")
            self.task_mgr.start_task(mem_task)

            if self.config.update_memory:
                self._update_memory(phase, plan, errors)

            self.task_mgr.complete_task(mem_task)

            # ---- DONE ----
            phase = PipelinePhase.COMPLETED
            log_phase_transition(logger, "UPDATING_MEMORY", "COMPLETED")

        except Exception as e:
            phase = PipelinePhase.FAILED
            errors.append(f"Pipeline error: {str(e)}")
            logger.error(f"Pipeline failed: {e}")

        return self._build_result(
            phase == PipelinePhase.COMPLETED,
            phase, start_time, files_created, files_modified,
            scan_summary, errors
        )

    # ------------------------------------------------------------------
    # Execute a single file operation
    # ------------------------------------------------------------------
    def _execute_operation(self, operation: Dict[str, Any]):
        """Execute a single file operation from the plan."""
        action = operation.get("action", "create")
        rel_path = operation.get("path", "")

        if action == "create":
            return self.writer.create_file(
                rel_path,
                operation.get("content", ""),
                overwrite=operation.get("overwrite", False),
            )
        elif action == "modify":
            return self.writer.create_file(
                rel_path,
                operation.get("content", ""),
                overwrite=True,
            )
        elif action == "patch":
            return self.writer.patch_file(
                rel_path,
                operation.get("old_string", ""),
                operation.get("new_string", ""),
                replace_all=operation.get("replace_all", False),
            )
        elif action == "append":
            return self.writer.append_to_file(
                rel_path,
                operation.get("content", ""),
            )
        elif action == "delete":
            return self.writer.delete_file(rel_path)
        else:
            from pipeline.code_writer import WriteResult
            return WriteResult(False, rel_path, "failed", error=f"Unknown action: {action}")

    # ------------------------------------------------------------------
    # Validate changes
    # ------------------------------------------------------------------
    def _validate_changes(self) -> List[str]:
        """Validate all files written in this run."""
        errors = []
        for wr in self.writer.write_log:
            if not wr.success:
                errors.append(f"Write failed: {wr.path} - {wr.error}")
        return errors

    # ------------------------------------------------------------------
    # Update memory files
    # ------------------------------------------------------------------
    def _update_memory(self, phase: PipelinePhase, plan: List[Dict], errors: List[str]):
        """Update spec.md and hot.md with pipeline results."""
        # Record the run
        stats = self.task_mgr.get_statistics()
        result = self._build_result(
            phase == PipelinePhase.COMPLETED,
            phase, datetime.now(timezone.utc), 0, 0, {}, errors
        )
        self.memory.record_run(result)

        # Update spec.md
        spec_changes = []
        for wr in self.writer.write_log:
            if wr.success:
                spec_changes.append({
                    "type": "added" if wr.action == "created" else "modified",
                    "component": wr.path,
                    "description": f"File {wr.action} by pipeline ({wr.lines_written} lines)",
                })
        if spec_changes:
            self.memory.update_spec(spec_changes)

        # Update hot.md
        recent = [f"{wr.action}: {wr.path}" for wr in self.writer.write_log if wr.success]
        if errors:
            recent.append(f"Errors: {len(errors)}")
        self.memory.update_hot(
            phase=phase.value,
            active_tasks=stats["running"],
            recent_changes=recent if recent else None,
            next_priorities=[
                "Review pipeline output",
                "Validate file changes",
                "Commit changes to Git",
            ],
        )

    # ------------------------------------------------------------------
    # Build result
    # ------------------------------------------------------------------
    def _build_result(
        self,
        success: bool,
        phase: PipelinePhase,
        start_time: datetime,
        files_created: int,
        files_modified: int,
        scan_summary: Dict[str, Any],
        errors: List[str],
    ) -> PipelineResult:
        end_time = datetime.now(timezone.utc)
        duration = (end_time - start_time).total_seconds()
        stats = self.task_mgr.get_statistics()

        result = PipelineResult(
            success=success,
            phase_reached=phase,
            tasks_total=stats["total"],
            tasks_completed=stats["completed"],
            tasks_failed=stats["failed"],
            files_created=files_created,
            files_modified=files_modified,
            scan_summary=scan_summary,
            errors=errors,
            start_time=start_time,
            end_time=end_time,
            duration_seconds=duration,
        )

        # Log summary
        logger.info("=" * 60)
        logger.info("PIPELINE COMPLETE")
        logger.info(f"  Success:   {success}")
        logger.info(f"  Phase:     {phase.value}")
        logger.info(f"  Duration:  {duration:.2f}s")
        logger.info(f"  Tasks:     {stats['completed']}/{stats['total']} completed")
        logger.info(f"  Files:     {files_created} created, {files_modified} modified")
        if errors:
            logger.info(f"  Errors:    {len(errors)}")
            for e in errors:
                logger.info(f"    - {e}")
        logger.info("=" * 60)

        # Generate report
        self.memory.generate_report(result)

        return result
