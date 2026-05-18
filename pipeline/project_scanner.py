"""
Autonomous Coding Pipeline - Project Scanner

Analyzes project structure to provide context for autonomous coding:
  - File inventory with type detection
  - Import/dependency extraction
  - Complexity scoring
  - Entry point identification
  - Git info (if available)

This is a lightweight, standalone scanner for the pipeline.
The existing ai_core/agents/project_scanner.py provides deeper AST analysis.

Usage:
    from pipeline.project_scanner import ProjectScanner
    scanner = ProjectScanner("/root/Atsawin-AI-Core")
    report = scanner.scan()
    print(report.summary())
"""

import os
import re
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from datetime import datetime, timezone

from pipeline import PipelineConfig
from pipeline.logger import get_logger

logger = get_logger("project_scanner")


class ProjectScanner:
    """
    Scans a project directory and produces a structured report
    suitable for autonomous coding decisions.
    """

    # File extension -> language mapping
    EXT_MAP = {
        ".py": "python", ".js": "javascript", ".ts": "typescript",
        ".jsx": "javascript", ".tsx": "typescript", ".java": "java",
        ".cpp": "cpp", ".cc": "cpp", ".cxx": "cpp", ".h": "cpp", ".hpp": "cpp",
        ".go": "go", ".rs": "rust", ".html": "html", ".css": "css",
        ".scss": "css", ".yml": "yaml", ".yaml": "yaml", ".json": "json",
        ".toml": "toml", ".ini": "ini", ".cfg": "cfg", ".md": "markdown",
        ".sh": "bash", ".txt": "text",
    }

    DEFAULT_IGNORE = {
        "__pycache__", ".git", ".venv", "venv", "node_modules",
        ".mypy_cache", ".pytest_cache", "dist", "build", "target",
        ".idea", ".vscode", ".DS_Store",
    }

    def __init__(self, root_path: str, config: Optional[PipelineConfig] = None):
        self.root = Path(root_path).resolve()
        self.config = config or PipelineConfig()
        self.ignore = set(self.config.scan_ignore) | self.DEFAULT_IGNORE
        logger.info(f"ProjectScanner initialized for: {self.root}")

    # ------------------------------------------------------------------
    # Main scan
    # ------------------------------------------------------------------
    def scan(self) -> "ScanReport":
        """Run a full project scan and return a ScanReport."""
        logger.info(f"Starting project scan: {self.root}")
        start = datetime.now(timezone.utc)

        files = self._collect_files()
        file_infos = [self._analyze_file(f) for f in files]
        git_info = self._get_git_info()

        duration = (datetime.now(timezone.utc) - start).total_seconds()
        report = ScanReport(
            root=str(self.root),
            project_name=self.root.name,
            total_files=len(file_infos),
            total_lines=sum(f["lines"] for f in file_infos),
            languages=self._count_languages(file_infos),
            directories=self._collect_directories(files),
            entry_points=self._find_entry_points(file_infos),
            config_files=self._find_config_files(file_infos),
            test_files=self._find_test_files(file_infos),
            git_info=git_info,
            scan_duration_seconds=duration,
            files=file_infos,
        )
        logger.info(
            f"Scan complete: {report.total_files} files, "
            f"{report.total_lines} lines in {duration:.2f}s"
        )
        return report

    # ------------------------------------------------------------------
    # File collection
    # ------------------------------------------------------------------
    def _collect_files(self) -> List[Path]:
        """Walk the project tree and collect file paths."""
        files = []
        for dirpath, dirnames, filenames in os.walk(self.root):
            # Filter ignored directories in-place
            dirnames[:] = [d for d in dirnames if d not in self.ignore and not d.startswith(".")]
            for fn in filenames:
                if fn.startswith(".") or fn.endswith((".pyc", ".pyo")):
                    continue
                fp = Path(dirpath) / fn
                # Skip files in ignored directories
                parts = set(fp.relative_to(self.root).parts)
                if parts & self.ignore:
                    continue
                files.append(fp)
        return files

    # ------------------------------------------------------------------
    # File analysis
    # ------------------------------------------------------------------
    def _analyze_file(self, path: Path) -> Dict[str, Any]:
        """Analyze a single file and return metadata dict."""
        ext = path.suffix.lower()
        language = self.EXT_MAP.get(ext, "unknown")
        stat = path.stat()

        content = ""
        lines = 0
        imports = []
        functions = []
        classes = []

        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
            lines = content.count("\n") + 1

            if language == "python":
                imports = self._extract_py_imports(content)
                functions = re.findall(r"^def\s+(\w+)", content, re.MULTILINE)
                classes = re.findall(r"^class\s+(\w+)", content, re.MULTILINE)
            elif language in ("javascript", "typescript"):
                imports = re.findall(r"""import\s+.*?from\s+['"]([^'"]+)""", content)
                functions = re.findall(r"(?:function|const|let|var)\s+(\w+)\s*(?:=|\()", content)
                classes = re.findall(r"class\s+(\w+)", content)
        except Exception:
            pass

        return {
            "path": str(path),
            "relative": str(path.relative_to(self.root)),
            "name": path.name,
            "extension": ext,
            "language": language,
            "size_bytes": stat.st_size,
            "lines": lines,
            "imports": imports,
            "functions": functions,
            "classes": classes,
        }

    @staticmethod
    def _extract_py_imports(content: str) -> List[str]:
        """Extract Python import module names."""
        imports = []
        for m in re.finditer(r"^(?:from\s+(\w+)|import\s+(\w+))", content, re.MULTILINE):
            imports.append(m.group(1) or m.group(2))
        return [i for i in imports if i]

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _count_languages(self, file_infos: List[Dict]) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for fi in file_infos:
            lang = fi["language"]
            if lang != "unknown":
                counts[lang] = counts.get(lang, 0) + 1
        return dict(sorted(counts.items(), key=lambda x: x[1], reverse=True))

    def _collect_directories(self, files: List[Path]) -> List[str]:
        dirs: Set[str] = set()
        for f in files:
            rel = f.relative_to(self.root)
            if len(rel.parts) > 1:
                dirs.add(str(rel.parent))
        return sorted(dirs)

    def _find_entry_points(self, file_infos: List[Dict]) -> List[str]:
        entry_names = {"main.py", "app.py", "index.js", "index.ts", "server.py", "manage.py"}
        return [fi["relative"] for fi in file_infos if fi["name"] in entry_names]

    def _find_config_files(self, file_infos: List[Dict]) -> List[str]:
        config_names = {"pyproject.toml", "setup.py", "setup.cfg", "package.json",
                        "docker-compose.yml", "Dockerfile", ".env", "config.yaml",
                        "config.json", "Makefile", "requirements.txt"}
        return [fi["relative"] for fi in file_infos if fi["name"] in config_names]

    def _find_test_files(self, file_infos: List[Dict]) -> List[str]:
        return [fi["relative"] for fi in file_infos
                if fi["name"].startswith("test_") or fi["name"].endswith("_test.py")
                or "/tests/" in fi["relative"]]

    def _get_git_info(self) -> Dict[str, Any]:
        """Get basic git information if available."""
        git_dir = self.root / ".git"
        if not git_dir.exists():
            return {"is_repo": False}
        try:
            branch = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                capture_output=True, text=True, cwd=str(self.root), timeout=5
            ).stdout.strip()
            last_commit = subprocess.run(
                ["git", "log", "-1", "--format=%H|%an|%s|%ar"],
                capture_output=True, text=True, cwd=str(self.root), timeout=5
            ).stdout.strip()
            parts = last_commit.split("|", 3) if last_commit else []
            return {
                "is_repo": True,
                "branch": branch,
                "last_commit_hash": parts[0] if len(parts) > 0 else None,
                "last_commit_author": parts[1] if len(parts) > 1 else None,
                "last_commit_message": parts[2] if len(parts) > 2 else None,
                "last_commit_relative": parts[3] if len(parts) > 3 else None,
            }
        except Exception as e:
            return {"is_repo": True, "error": str(e)}


# ------------------------------------------------------------------
# Scan report
# ------------------------------------------------------------------
class ScanReport:
    """Immutable-ish scan result with summary and query methods."""

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def summary(self) -> Dict[str, Any]:
        """Return a compact summary dict."""
        return {
            "project": self.project_name,
            "root": self.root,
            "total_files": self.total_files,
            "total_lines": self.total_lines,
            "languages": self.languages,
            "entry_points": self.entry_points,
            "config_files": self.config_files,
            "test_files": self.test_files,
            "directories_count": len(self.directories),
            "git_branch": self.git_info.get("branch") if self.git_info else None,
            "scan_duration_seconds": self.scan_duration_seconds,
        }

    def to_dict(self) -> Dict[str, Any]:
        return self.__dict__.copy()

    def get_files_by_language(self, language: str) -> List[Dict]:
        return [f for f in self.files if f["language"] == language]

    def get_files_by_extension(self, ext: str) -> List[Dict]:
        return [f for f in self.files if f["extension"] == ext]
