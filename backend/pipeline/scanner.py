"""
Project Scanner - Analyzes project structure and code metrics
"""
import os
from pathlib import Path
from datetime import datetime
from .models import ScanResult

# File extensions mapped to languages
LANGUAGE_MAP = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".jsx": "javascript",
    ".tsx": "typescript",
    ".go": "go",
    ".rs": "rust",
    ".java": "java",
    ".c": "c",
    ".cpp": "cpp",
    ".h": "c",
    ".rb": "ruby",
    ".php": "php",
    ".sh": "shell",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".json": "json",
    ".toml": "toml",
    ".md": "markdown",
    ".html": "html",
    ".css": "css",
    ".sql": "sql",
}

# Directories to skip
SKIP_DIRS = {
    ".git", "node_modules", "__pycache__", ".venv", "venv",
    "env", ".env", ".tox", ".mypy_cache", ".pytest_cache",
    "dist", "build", ".next", ".nuxt", "target", "vendor",
    ".idea", ".vscode", "coverage", "htmlcov",
}

# Dependency files
DEPENDENCY_FILES = {
    "requirements.txt": "python",
    "package.json": "javascript",
    "go.mod": "go",
    "Cargo.toml": "rust",
    "pom.xml": "java",
    "Gemfile": "ruby",
    "composer.json": "php",
    "pyproject.toml": "python",
    "Pipfile": "python",
    "poetry.lock": "python",
}


def scan_project(root_path: str) -> ScanResult:
    """Scan a project directory and return comprehensive analysis."""
    root = Path(root_path)
    if not root.exists():
        raise FileNotFoundError(f"Path not found: {root_path}")
    if not root.is_dir():
        raise NotADirectoryError(f"Not a directory: {root_path}")

    result = ScanResult()
    languages = {}
    total_lines = 0
    total_files = 0
    max_depth = 0
    dir_count = 0
    largest_files = []

    for dirpath, dirnames, filenames in os.walk(root):
        # Skip unwanted directories
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]

        # Calculate depth
        rel_path = os.path.relpath(dirpath, root)
        depth = 0 if rel_path == "." else rel_path.count(os.sep) + 1
        max_depth = max(max_depth, depth)
        dir_count += len(dirnames)

        for filename in filenames:
            filepath = Path(dirpath) / filename
            ext = filepath.suffix.lower()
            rel_filepath = str(filepath.relative_to(root))

            total_files += 1

            # Track language stats
            lang = LANGUAGE_MAP.get(ext, "other")
            if lang not in languages:
                languages[lang] = {"files": 0, "lines": 0}

            # Count lines
            try:
                line_count = _count_lines(filepath)
                languages[lang]["lines"] += line_count
                total_lines += line_count
            except (OSError, UnicodeDecodeError):
                line_count = 0

            languages[lang]["files"] += 1
            largest_files.append({"path": rel_filepath, "lines": line_count})

    # Sort largest files
    largest_files.sort(key=lambda x: x["lines"], reverse=True)

    # Find dependencies
    dependencies = _find_dependencies(root)

    result.total_files = total_files
    result.languages = languages
    result.total_lines = total_lines
    result.dependencies = dependencies
    result.structure = {
        "directories": dir_count,
        "max_depth": max_depth,
        "largest_files": largest_files[:10],
    }
    result.scanned_at = datetime.utcnow()

    return result


def _count_lines(filepath: Path) -> int:
    """Count lines in a file."""
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            return sum(1 for _ in f)
    except OSError:
        return 0


def _find_dependencies(root: Path) -> list[str]:
    """Find project dependencies from known dependency files."""
    deps = []
    for dep_file, ecosystem in DEPENDENCY_FILES.items():
        dep_path = root / dep_file
        if dep_path.exists():
            deps.append(f"{ecosystem}:{dep_file}")
    return deps
