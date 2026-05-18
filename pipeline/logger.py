"""
Autonomous Coding Pipeline - Centralized Logger

Provides a unified logging interface that writes to:
  - Console (stdout) with color-coded levels
  - Rotating log files under AI/logs/pipeline/
  - JSON structured logs for machine parsing

Usage:
    from pipeline.logger import get_logger
    log = get_logger("pipeline")
    log.info("Pipeline started")
    log.task_event("task_123", "created", priority="high")
"""

import logging
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any

from pipeline import PIPELINE_LOG_DIR

# ---------------------------------------------------------------------------
# Formatters
# ---------------------------------------------------------------------------
class ConsoleFormatter(logging.Formatter):
    """Color-coded console output."""

    COLORS = {
        "DEBUG": "\033[36m",     # cyan
        "INFO": "\033[32m",      # green
        "WARNING": "\033[33m",   # yellow
        "ERROR": "\033[31m",     # red
        "CRITICAL": "\033[1;31m", # bold red
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, "")
        ts = datetime.fromtimestamp(record.created, tz=timezone.utc).strftime("%H:%M:%S")
        msg = f"{color}[{ts}] [{record.levelname:8s}] {record.message}{self.RESET}"
        return msg


class FileFormatter(logging.Formatter):
    """Plain text file output with full timestamp."""

    def format(self, record: logging.LogRecord) -> str:
        ts = datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat()
        return f"{ts} | {record.levelname:8s} | {record.name} | {record.message}"


class JSONFormatter(logging.Formatter):
    """Structured JSON log lines for machine parsing."""

    def format(self, record: logging.LogRecord) -> str:
        entry = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.message,
        }
        # Attach any extra fields
        for key in ("task_id", "event", "phase", "file", "duration"):
            if hasattr(record, key):
                entry[key] = getattr(record, key)
        return json.dumps(entry, default=str)


# ---------------------------------------------------------------------------
# Logger factory
# ---------------------------------------------------------------------------
_loggers: Dict[str, logging.Logger] = {}


def get_logger(
    name: str = "pipeline",
    level: int = logging.INFO,
    log_to_console: bool = True,
    log_to_file: bool = True,
) -> logging.Logger:
    """
    Get or create a named logger with console + file handlers.

    Args:
        name: Logger name (used for log file naming).
        level: Minimum log level.
        log_to_console: Enable stdout output.
        log_to_file: Enable file output.
    Returns:
        Configured logging.Logger instance.
    """
    if name in _loggers:
        return _loggers[name]

    logger = logging.getLogger(f"pipeline.{name}")
    logger.setLevel(level)
    logger.handlers.clear()

    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(ConsoleFormatter())
        logger.addHandler(console_handler)

    if log_to_file:
        # Plain text log
        file_handler = logging.FileHandler(
            PIPELINE_LOG_DIR / f"{name}.log", encoding="utf-8"
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(FileFormatter())
        logger.addHandler(file_handler)

        # JSON structured log
        json_handler = logging.FileHandler(
            PIPELINE_LOG_DIR / f"{name}.json.log", encoding="utf-8"
        )
        json_handler.setLevel(level)
        json_handler.setFormatter(JSONFormatter())
        logger.addHandler(json_handler)

    _loggers[name] = logger
    return logger


# ---------------------------------------------------------------------------
# Convenience helpers
# ---------------------------------------------------------------------------
def log_task_event(
    logger: logging.Logger,
    task_id: str,
    event: str,
    **extras: Any,
) -> None:
    """Log a structured task lifecycle event."""
    msg = f"Task {task_id}: {event}"
    extra = {"task_id": task_id, "event": event}
    extra.update(extras)
    logger.info(msg, extra=extra)


def log_phase_transition(
    logger: logging.Logger,
    from_phase: str,
    to_phase: str,
) -> None:
    """Log a pipeline phase transition."""
    logger.info(f"Phase transition: {from_phase} -> {to_phase}")
