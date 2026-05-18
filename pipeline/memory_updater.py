"""
Autonomous Coding Pipeline - Memory Updater

Updates spec.md and hot.md after pipeline execution:
  - Append structured log entries to AI/logs/
  - Update spec.md with architecture changes
  - Update hot.md with current state and recent changes
  - Generate pipeline run reports

Usage:
    from pipeline.memory_updater import MemoryUpdater
    updater = MemoryUpdater("/root/Atsawin-AI-Core")
    updater.record_run(pipeline_result)
    updater.update_hot(phase="coding", active_tasks=3)
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone

from pipeline import PROJECT_ROOT, SPEC_FILE, HOT_FILE, PIPELINE_LOG_DIR, PipelineResult
from pipeline.logger import get_logger

logger = get_logger("memory_updater")


class MemoryUpdater:
    """
    Updates project memory files (spec.md, hot.md) and generates
    structured pipeline run logs.
    """

    def __init__(self, root_path: str = str(PROJECT_ROOT)):
        self.root = Path(root_path)
        self.spec_path = self.root / "spec.md"
        self.hot_path = self.root / "hot.md"
        self.log_dir = PIPELINE_LOG_DIR
        logger.info(f"MemoryUpdater initialized for: {self.root}")

    # ------------------------------------------------------------------
    # Record a pipeline run
    # ------------------------------------------------------------------
    def record_run(self, result: PipelineResult) -> str:
        """
        Save a structured pipeline run report to AI/logs/pipeline/runs/.

        Returns the path to the saved report.
        """
        run_dir = self.log_dir / "runs"
        run_dir.mkdir(parents=True, exist_ok=True)

        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        run_file = run_dir / f"run_{ts}.json"

        report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "result": result.to_dict(),
        }

        run_file.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
        logger.info(f"Pipeline run recorded: {run_file}")
        return str(run_file)

    # ------------------------------------------------------------------
    # Update spec.md
    # ------------------------------------------------------------------
    def update_spec(self, changes: List[Dict[str, str]]) -> bool:
        """
        Append architecture changes to spec.md.

        Args:
            changes: List of {"type": "added|modified|removed", "component": "...", "description": "..."}
        Returns:
            True if successful.
        """
        if not self.spec_path.exists():
            logger.error(f"spec.md not found: {self.spec_path}")
            return False

        try:
            content = self.spec_path.read_text(encoding="utf-8")
            ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

            section = f"\n### Pipeline Changes ({ts})\n"
            for change in changes:
                ctype = change.get("type", "modified").upper()
                component = change.get("component", "unknown")
                desc = change.get("description", "")
                section += f"- **[{ctype}]** {component}: {desc}\n"

            # Insert before the "---" separator at the end, or append
            if "\n---\n" in content:
                # Insert before the last separator block
                last_sep = content.rfind("\n---\n")
                new_content = content[:last_sep] + "\n" + section + "\n" + content[last_sep:]
            else:
                new_content = content + "\n" + section

            # Backup
            backup = self.spec_path.with_suffix(f".md.{ts.replace(' ', '_').replace(':', '')}.bak")
            self.spec_path.rename(backup)
            self.spec_path.write_text(new_content, encoding="utf-8")

            logger.info(f"spec.md updated with {len(changes)} changes (backup: {backup.name})")
            return True

        except Exception as e:
            logger.error(f"Failed to update spec.md: {e}")
            return False

    # ------------------------------------------------------------------
    # Update hot.md
    # ------------------------------------------------------------------
    def update_hot(self, phase: str = "idle", active_tasks: int = 0,
                   recent_changes: Optional[List[str]] = None,
                   next_priorities: Optional[List[str]] = None) -> bool:
        """
        Update hot.md with current pipeline state.

        Args:
            phase: Current pipeline phase.
            active_tasks: Number of active tasks.
            recent_changes: List of recent change descriptions.
            next_priorities: List of next priority items.
        Returns:
            True if successful.
        """
        if not self.hot_path.exists():
            logger.error(f"hot.md not found: {self.hot_path}")
            return False

        try:
            content = self.hot_path.read_text(encoding="utf-8")
            ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

            # Update "Current Task" section
            new_task_line = f"Building AI Operating System - Pipeline phase: {phase}"
            if "Current Task" in content:
                # Replace the line after "## Current Task"
                lines = content.split("\n")
                new_lines = []
                for i, line in enumerate(lines):
                    new_lines.append(line)
                    if line.strip() == "## Current Task" and i + 1 < len(lines):
                        new_lines.append(new_task_line)
                        # Skip the old task line
                        continue
                    elif line.strip().startswith("Building AI Operating System") and i > 0 and lines[i-1].strip() == "## Current Task":
                        continue
                content = "\n".join(new_lines)

            # Append to Recent Achievements
            if recent_changes:
                achievement_header = "## Recent Achievements"
                if achievement_header in content:
                    insert_pos = content.find(achievement_header)
                    # Find the next section header
                    next_section = content.find("\n## ", insert_pos + len(achievement_header))
                    ts_short = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
                    achievement_block = f"\n### Pipeline Update ({ts_short})\n"
                    for change in recent_changes:
                        achievement_block += f"- {change}\n"
                    if next_section > 0:
                        content = content[:next_section] + achievement_block + content[next_section:]
                    else:
                        content += achievement_block

            # Update Next Priority
            if next_priorities:
                priority_header = "Next Priority"
                if priority_header in content:
                    lines = content.split("\n")
                    new_lines = []
                    in_priority = False
                    skipped_old = False
                    for line in lines:
                        if priority_header in line:
                            in_priority = True
                            new_lines.append(line)
                            for p in next_priorities:
                                new_lines.append(f"{p}")
                            skipped_old = False
                            continue
                        if in_priority:
                            if line.strip().startswith("### ") or line.strip().startswith("---"):
                                in_priority = False
                                new_lines.append(line)
                            # Skip old priority lines
                            continue
                        new_lines.append(line)
                    content = "\n".join(new_lines)

            # Backup and write
            backup = self.hot_path.with_suffix(f".md.{ts.replace(' ', '_').replace(':', '')}.bak")
            self.hot_path.rename(backup)
            self.hot_path.write_text(content, encoding="utf-8")

            logger.info(f"hot.md updated (phase={phase}, active_tasks={active_tasks})")
            return True

        except Exception as e:
            logger.error(f"Failed to update hot.md: {e}")
            return False

    # ------------------------------------------------------------------
    # Generate a run report
    # ------------------------------------------------------------------
    def generate_report(self, result: PipelineResult) -> str:
        """Generate a human-readable pipeline run report."""
        lines = [
            "=" * 60,
            "AUTONOMOUS CODING PIPELINE - RUN REPORT",
            "=" * 60,
            f"Timestamp:  {datetime.now(timezone.utc).isoformat()}",
            f"Success:    {result.success}",
            f"Phase:      {result.phase_reached}",
            f"Duration:   {result.duration_seconds:.2f}s",
            "",
            "--- Tasks ---",
            f"  Total:     {result.tasks_total}",
            f"  Completed: {result.tasks_completed}",
            f"  Failed:    {result.tasks_failed}",
            "",
            "--- Files ---",
            f"  Created:   {result.files_created}",
            f"  Modified:  {result.files_modified}",
        ]

        if result.scan_summary:
            lines.extend([
                "",
                "--- Scan Summary ---",
                f"  Project:   {result.scan_summary.get('project', 'N/A')}",
                f"  Files:     {result.scan_summary.get('total_files', 'N/A')}",
                f"  Lines:     {result.scan_summary.get('total_lines', 'N/A')}",
                f"  Languages: {result.scan_summary.get('languages', {})}",
            ])

        if result.errors:
            lines.extend(["", "--- Errors ---"])
            for err in result.errors:
                lines.append(f"  - {err}")

        lines.append("=" * 60)
        report = "\n".join(lines)

        # Save to file
        report_dir = self.log_dir / "reports"
        report_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        report_file = report_dir / f"report_{ts}.txt"
        report_file.write_text(report, encoding="utf-8")

        logger.info(f"Report generated: {report_file}")
        return report
