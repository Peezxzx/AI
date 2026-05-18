"""
Autonomous Coding Pipeline - Code Writer

Safe file creation and modification engine:
  - Create new files with automatic directory creation
  - Modify existing files with backup
  - Patch files using find-and-replace
  - Validate Python syntax after writes
  - Dry-run mode for testing

Usage:
    from pipeline.code_writer import CodeWriter
    writer = CodeWriter("/root/Atsawin-AI-Core", dry_run=False)
    result = writer.create_file("new_module.py", "def hello(): pass")
    result = writer.patch_file("existing.py", old_string, new_string)
"""

import os
import shutil
import ast
from pathlib import Path
from typing import Dict, Optional, Any, List
from datetime import datetime, timezone

from pipeline import PipelineConfig
from pipeline.logger import get_logger

logger = get_logger("code_writer")


class WriteResult:
    """Result of a file write operation."""

    def __init__(self, success: bool, path: str, action: str,
                 backup_path: Optional[str] = None, error: Optional[str] = None,
                 lines_written: int = 0):
        self.success = success
        self.path = path
        self.action = action  # "created", "modified", "patched", "skipped"
        self.backup_path = backup_path
        self.error = error
        self.lines_written = lines_written
        self.timestamp = datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "path": self.path,
            "action": self.action,
            "backup_path": self.backup_path,
            "error": self.error,
            "lines_written": self.lines_written,
            "timestamp": self.timestamp.isoformat(),
        }

    def __repr__(self):
        status = "OK" if self.success else "FAIL"
        return f"WriteResult({status}, {self.action}, {self.path})"


class CodeWriter:
    """
    Safe file creation and modification engine for the autonomous pipeline.

    Features:
    - Automatic parent directory creation
    - Backup before modification
    - Python syntax validation
    - Dry-run mode
    - Detailed result reporting
    """

    def __init__(self, root_path: str, config: Optional[PipelineConfig] = None):
        self.root = Path(root_path).resolve()
        self.config = config or PipelineConfig()
        self.dry_run = self.config.dry_run
        self._write_log: List[WriteResult] = []
        logger.info(f"CodeWriter initialized (dry_run={self.dry_run})")

    @property
    def write_log(self) -> List[WriteResult]:
        """Return the log of all write operations."""
        return list(self._write_log)

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------
    def create_file(self, relative_path: str, content: str,
                    overwrite: bool = False) -> WriteResult:
        """
        Create a new file with the given content.

        Args:
            relative_path: Path relative to project root.
            content: File content to write.
            overwrite: If True, overwrite existing files.
        Returns:
            WriteResult with operation details.
        """
        full_path = self.root / relative_path
        action = "created"

        if full_path.exists() and not overwrite:
            msg = f"File already exists: {relative_path}"
            logger.warning(msg)
            result = WriteResult(False, relative_path, "skipped", error=msg)
            self._write_log.append(result)
            return result

        if full_path.exists():
            action = "modified"
            backup = self._backup(full_path)
        else:
            backup = None

        if self.dry_run:
            logger.info(f"[DRY RUN] Would create: {relative_path}")
            result = WriteResult(True, relative_path, action,
                                backup_path=str(backup) if backup else None,
                                lines_written=content.count("\n") + 1)
            self._write_log.append(result)
            return result

        try:
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content, encoding="utf-8")

            # Validate Python syntax
            if full_path.suffix == ".py":
                syntax_ok, syntax_err = self._validate_python(full_path)
                if not syntax_ok:
                    # Restore backup on syntax error
                    if backup:
                        shutil.copy2(backup, full_path)
                        logger.warning(f"Syntax error, restored backup: {syntax_err}")
                    else:
                        full_path.unlink(missing_ok=True)
                    result = WriteResult(False, relative_path, "failed",
                                        error=f"Syntax error: {syntax_err}")
                    self._write_log.append(result)
                    return result

            lines = content.count("\n") + 1
            logger.info(f"File {action}: {relative_path} ({lines} lines)")
            result = WriteResult(True, relative_path, action,
                                backup_path=str(backup) if backup else None,
                                lines_written=lines)
            self._write_log.append(result)
            return result

        except Exception as e:
            logger.error(f"Failed to create {relative_path}: {e}")
            result = WriteResult(False, relative_path, "failed", error=str(e))
            self._write_log.append(result)
            return result

    # ------------------------------------------------------------------
    # Modify (patch)
    # ------------------------------------------------------------------
    def patch_file(self, relative_path: str, old_string: str,
                   new_string: str, replace_all: bool = False) -> WriteResult:
        """
        Find-and-replace within an existing file.

        Args:
            relative_path: Path relative to project root.
            old_string: Text to find.
            new_string: Replacement text.
            replace_all: Replace all occurrences (default: first only).
        Returns:
            WriteResult with operation details.
        """
        full_path = self.root / relative_path

        if not full_path.exists():
            msg = f"File not found: {relative_path}"
            logger.error(msg)
            result = WriteResult(False, relative_path, "failed", error=msg)
            self._write_log.append(result)
            return result

        try:
            content = full_path.read_text(encoding="utf-8")

            if old_string not in content:
                msg = f"Pattern not found in {relative_path}"
                logger.warning(msg)
                result = WriteResult(False, relative_path, "skipped", error=msg)
                self._write_log.append(result)
                return result

            backup = self._backup(full_path)

            if replace_all:
                new_content = content.replace(old_string, new_string)
            else:
                new_content = content.replace(old_string, new_string, 1)

            if self.dry_run:
                logger.info(f"[DRY RUN] Would patch: {relative_path}")
                result = WriteResult(True, relative_path, "patched",
                                    backup_path=str(backup))
                self._write_log.append(result)
                return result

            full_path.write_text(new_content, encoding="utf-8")

            # Validate Python syntax
            if full_path.suffix == ".py":
                syntax_ok, syntax_err = self._validate_python(full_path)
                if not syntax_ok:
                    shutil.copy2(backup, full_path)
                    result = WriteResult(False, relative_path, "failed",
                                        error=f"Syntax error after patch: {syntax_err}")
                    self._write_log.append(result)
                    return result

            logger.info(f"File patched: {relative_path}")
            result = WriteResult(True, relative_path, "patched",
                                backup_path=str(backup))
            self._write_log.append(result)
            return result

        except Exception as e:
            logger.error(f"Failed to patch {relative_path}: {e}")
            result = WriteResult(False, relative_path, "failed", error=str(e))
            self._write_log.append(result)
            return result

    # ------------------------------------------------------------------
    # Append
    # ------------------------------------------------------------------
    def append_to_file(self, relative_path: str, content: str) -> WriteResult:
        """Append content to an existing file."""
        full_path = self.root / relative_path

        if not full_path.exists():
            return self.create_file(relative_path, content)

        try:
            backup = self._backup(full_path)
            existing = full_path.read_text(encoding="utf-8")
            new_content = existing + content

            if self.dry_run:
                logger.info(f"[DRY RUN] Would append to: {relative_path}")
                result = WriteResult(True, relative_path, "appended",
                                    backup_path=str(backup))
                self._write_log.append(result)
                return result

            full_path.write_text(new_content, encoding="utf-8")
            lines = content.count("\n") + 1
            logger.info(f"Appended to {relative_path} ({lines} lines)")
            result = WriteResult(True, relative_path, "appended",
                                backup_path=str(backup), lines_written=lines)
            self._write_log.append(result)
            return result

        except Exception as e:
            logger.error(f"Failed to append to {relative_path}: {e}")
            result = WriteResult(False, relative_path, "failed", error=str(e))
            self._write_log.append(result)
            return result

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------
    def delete_file(self, relative_path: str) -> WriteResult:
        """Delete a file (with backup)."""
        full_path = self.root / relative_path

        if not full_path.exists():
            result = WriteResult(False, relative_path, "skipped",
                                error="File not found")
            self._write_log.append(result)
            return result

        backup = self._backup(full_path)

        if self.dry_run:
            logger.info(f"[DRY RUN] Would delete: {relative_path}")
            result = WriteResult(True, relative_path, "deleted",
                                backup_path=str(backup))
            self._write_log.append(result)
            return result

        full_path.unlink()
        logger.info(f"File deleted: {relative_path}")
        result = WriteResult(True, relative_path, "deleted",
                            backup_path=str(backup))
        self._write_log.append(result)
        return result

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _backup(self, path: Path) -> Path:
        """Create a .bak backup of a file."""
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        backup = path.with_suffix(f"{path.suffix}.{ts}.bak")
        shutil.copy2(path, backup)
        return backup

    @staticmethod
    def _validate_python(path: Path) -> tuple:
        """Validate Python file syntax. Returns (ok, error_message)."""
        try:
            source = path.read_text(encoding="utf-8")
            ast.parse(source)
            return True, ""
        except SyntaxError as e:
            return False, f"Line {e.lineno}: {e.msg}"
        except Exception as e:
            return False, str(e)

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    def get_summary(self) -> Dict[str, Any]:
        """Summary of all write operations in this session."""
        created = sum(1 for r in self._write_log if r.action == "created" and r.success)
        modified = sum(1 for r in self._write_log if r.action in ("modified", "patched", "appended") and r.success)
        failed = sum(1 for r in self._write_log if not r.success)
        total_lines = sum(r.lines_written for r in self._write_log if r.success)
        return {
            "total_operations": len(self._write_log),
            "created": created,
            "modified": modified,
            "failed": failed,
            "total_lines_written": total_lines,
        }
