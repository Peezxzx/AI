"""
Autonomous Coding Pipeline - Project Scanner
Analyzes project structure, identifies files, dependencies, and code patterns for autonomous development.
"""

import os
import ast
import json
import logging
from typing import Dict, List, Optional, Any, Set, Tuple
from datetime import datetime, timezone
from dataclasses import dataclass, asdict
from enum import Enum
import asyncio
import subprocess
from pathlib import Path
import re

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))
try:
    from memory_manager import memory_manager
except ImportError:
    memory_manager = None


class FileType(Enum):
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    JAVA = "java"
    CPP = "cpp"
    GO = "go"
    RUST = "rust"
    HTML = "html"
    CSS = "css"
    YAML = "yaml"
    JSON = "json"
    XML = "xml"
    CONFIG = "config"
    DOCUMENTATION = "documentation"
    UNKNOWN = "unknown"


class ProjectType(Enum):
    WEB_APP = "web_app"
    API_SERVICE = "api_service"
    LIBRARY = "library"
    SCRIPT = "script"
    MONOLITH = "monolith"
    MICROSERVICES = "microservices"
    DATA_SCIENCE = "data_science"
    AI_ML = "ai_ml"
    DEVOPS = "devops"
    UNKNOWN = "unknown"


@dataclass
class FileInfo:
    path: str
    name: str
    extension: str
    file_type: FileType
    size: int
    lines_count: int
    language: str
    dependencies: List[str]
    imports: List[str]
    functions: List[str]
    classes: List[str]
    complexity_score: float
    last_modified: datetime
    created_at: datetime


@dataclass
class ProjectStructure:
    root_path: str
    project_name: str
    project_type: ProjectType
    total_files: int
    total_lines: int
    languages: Dict[str, int]  # language -> file count
    file_types: Dict[FileType, int]
    directories: List[str]
    files: List[FileInfo]
    main_files: List[str]
    entry_points: List[str]
    dependencies: Dict[str, Set[str]]  # file -> dependencies
    package_dependencies: Dict[str, str]  # package -> version
    configuration_files: List[str]
    documentation_files: List[str]
    test_files: List[str]
    git_info: Dict[str, Any]
    analysis_timestamp: datetime


class ProjectScanner:
    """Scans and analyzes project structure for autonomous coding operations."""
    
    def __init__(self, root_path: str = "."):
        self.root_path = Path(root_path).resolve()
        self.logger = self._setup_logger()
        
        # Supported file extensions by language
        self.language_extensions = {
            FileType.PYTHON: {".py"},
            FileType.JAVASCRIPT: {".js", ".jsx"},
            FileType.TYPESCRIPT: {".ts", ".tsx"},
            FileType.JAVA: {".java"},
            FileType.CPP: {".cpp", ".cc", ".cxx", ".h", ".hpp"},
            FileType.GO: {".go"},
            FileType.RUST: {".rs"},
            FileType.HTML: {".html", ".htm"},
            FileType.CSS: {".css", ".scss", ".sass"},
            FileType.YAML: {".yml", ".yaml"},
            FileType.JSON: {".json"},
            FileType.XML: {".xml"},
            FileType.CONFIG: {".toml", ".ini", ".cfg", ".conf", ".properties"},
            FileType.DOCUMENTATION: {".md", ".rst", ".txt"}
        }
        
        # Common project indicators
        self.project_indicators = {
            ProjectType.WEB_APP: {"package.json", "index.html", "static/", "templates/"},
            ProjectType.API_SERVICE: {"main.py", "app.py", "requirements.txt", "api/"},
            ProjectType.LIBRARY: {"setup.py", "pyproject.toml", "src/", "__init__.py"},
            ProjectType.SCRIPT: {"main.py", "script.py", "run.py"},
            ProjectType.MONOLITH: {"app.py", "main.py", "views.py", "models.py"},
            ProjectType.MICROSERVICES: {"docker-compose.yml", "service/", "microservice/"},
            ProjectType.DATA_SCIENCE: {"notebooks/", "data/", "models/", "requirements.txt"},
            ProjectType.AI_ML: {"models/", "training/", "inference/", "config/"},
            ProjectType.DEVOPS: {"Dockerfile", "docker-compose.yml", "k8s/", "terraform/"}
        }
        
        # Default ignore patterns
        self.ignore_patterns = {
            "__pycache__", "*.pyc", "*.pyo", ".git", ".svn", ".hg", ".venv", "venv",
            "node_modules", ".DS_Store", "*.log", "*.tmp", "cache/", "dist/", "build/",
            "target/", "out/", "coverage/", ".pytest_cache/", ".mypy_cache/"
        }
        
        self.logger.info(f"ProjectScanner initialized for path: {self.root_path}")
    
    def _setup_logger(self) -> logging.Logger:
        """Setup logging configuration."""
        logger = logging.getLogger("project_scanner")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    async def scan_project(self, 
                          include_git_info: bool = True,
                          analyze_dependencies: bool = True,
                          max_files: int = 10000) -> ProjectStructure:
        """Scan the entire project and return comprehensive analysis."""
        self.logger.info(f"Starting project scan for: {self.root_path}")
        
        start_time = datetime.now(timezone.utc)
        
        try:
            # Scan files and directories
            all_files = await self._scan_files(max_files)
            
            # Analyze each file
            file_infos = []
            for file_path in all_files:
                try:
                    file_info = await self._analyze_file(file_path)
                    file_infos.append(file_info)
                except Exception as e:
                    self.logger.warning(f"Failed to analyze file {file_path}: {e}")
            
            # Determine project type
            project_type = self._determine_project_type(all_files)
            
            # Extract dependencies
            dependencies = {}
            if analyze_dependencies:
                dependencies = await self._extract_dependencies(file_infos)
            
            # Extract package dependencies
            package_deps = await self._extract_package_dependencies()
            
            # Get git info if requested
            git_info = {}
            if include_git_info:
                git_info = await self._get_git_info()
            
            # Create project structure
            project_structure = ProjectStructure(
                root_path=str(self.root_path),
                project_name=self.root_path.name,
                project_type=project_type,
                total_files=len(file_infos),
                total_lines=sum(f.lines_count for f in file_infos),
                languages=self._count_languages(file_infos),
                file_types=self._count_file_types(file_infos),
                directories=self._get_directories(all_files),
                files=file_infos,
                main_files=self._identify_main_files(file_infos),
                entry_points=self._identify_entry_points(file_infos),
                dependencies=dependencies,
                package_dependencies=package_deps,
                configuration_files=self._find_config_files(file_infos),
                documentation_files=self._find_documentation_files(file_infos),
                test_files=self._find_test_files(file_infos),
                git_info=git_info,
                analysis_timestamp=start_time
            )
            
            # Store in memory
            await self._store_project_analysis(project_structure)
            
            self.logger.info(f"Project scan completed: {len(file_infos)} files analyzed")
            return project_structure
            
        except Exception as e:
            self.logger.error(f"Project scan failed: {e}")
            raise
    
    async def _scan_files(self, max_files: int) -> List[Path]:
        """Scan all files in the project directory."""
        files = []
        
        for root, dirs, filenames in os.walk(self.root_path):
            # Skip hidden directories and ignored patterns
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in self.ignore_patterns]
            
            for filename in filenames:
                if filename.startswith('.'):
                    continue
                
                file_path = Path(root) / filename
                
                # Skip files that match ignore patterns
                if any(filename.endswith(ext) for ext in [".pyc", ".pyo", ".log", ".tmp"]):
                    continue
                
                files.append(file_path)
                
                if len(files) >= max_files:
                    self.logger.warning(f"Reached max files limit: {max_files}")
                    return files
        
        return files
    
    async def _analyze_file(self, file_path: Path) -> FileInfo:
        """Analyze a single file and extract metadata."""
        try:
            stat = file_path.stat()
            
            # Get file type
            file_type, language = self._get_file_type_and_language(file_path)
            
            # Read file content
            content = ""
            lines_count = 0
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    lines_count = len(content.splitlines())
            except Exception as e:
                self.logger.warning(f"Failed to read file {file_path}: {e}")
            
            # Extract dependencies and imports
            imports, functions, classes, complexity = await self._parse_file_content(content, file_type)
            
            return FileInfo(
                path=str(file_path),
                name=file_path.name,
                extension=file_path.suffix,
                file_type=file_type,
                size=stat.st_size,
                lines_count=lines_count,
                language=language,
                dependencies=[],
                imports=imports,
                functions=functions,
                classes=classes,
                complexity_score=complexity,
                last_modified=datetime.fromtimestamp(stat.st_mtime, timezone.utc),
                created_at=datetime.fromtimestamp(stat.st_ctime, timezone.utc)
            )
            
        except Exception as e:
            self.logger.error(f"Error analyzing file {file_path}: {e}")
            # Return basic info even if analysis fails
            stat = file_path.stat()
            return FileInfo(
                path=str(file_path),
                name=file_path.name,
                extension=file_path.suffix,
                file_type=FileType.UNKNOWN,
                size=stat.st_size,
                lines_count=0,
                language="unknown",
                dependencies=[],
                imports=[],
                functions=[],
                classes=[],
                complexity_score=0.0,
                last_modified=datetime.fromtimestamp(stat.st_mtime, timezone.utc),
                created_at=datetime.fromtimestamp(stat.st_ctime, timezone.utc)
            )
    
    def _get_file_type_and_language(self, file_path: Path) -> Tuple[FileType, str]:
        """Determine file type and language from extension."""
        extension = file_path.suffix.lower()
        
        # Map extensions to file types and languages
        type_mapping = {
            FileType.PYTHON: ("python", "Python"),
            FileType.JAVASCRIPT: ("javascript", "JavaScript"),
            FileType.TYPESCRIPT: ("typescript", "TypeScript"),
            FileType.JAVA: ("java", "Java"),
            FileType.CPP: ("cpp", "C++"),
            FileType.GO: ("go", "Go"),
            FileType.RUST: ("rust", "Rust"),
            FileType.HTML: ("html", "HTML"),
            FileType.CSS: ("css", "CSS"),
            FileType.YAML: ("yaml", "YAML"),
            FileType.JSON: ("json", "JSON"),
            FileType.XML: ("xml", "XML"),
            FileType.CONFIG: ("config", "Configuration"),
            FileType.DOCUMENTATION: ("documentation", "Documentation")
        }
        
        for file_type, (language_name, display_name) in type_mapping.items():
            if extension in self.language_extensions[file_type]:
                return file_type, display_name
        
        return FileType.UNKNOWN, "Unknown"
    
    async def _parse_file_content(self, content: str, file_type: FileType) -> Tuple[List[str], List[str], List[str], float]:
        """Parse file content to extract imports, functions, classes, and complexity."""
        imports = []
        functions = []
        classes = []
        complexity = 0.0
        
        try:
            if file_type == FileType.PYTHON:
                # Use AST for Python files
                try:
                    tree = ast.parse(content)
                    
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Import):
                            for alias in node.names:
                                imports.append(alias.name)
                        elif isinstance(node, ast.ImportFrom):
                            if node.module:
                                imports.append(node.module)
                        elif isinstance(node, ast.FunctionDef):
                            functions.append(node.name)
                            # Calculate complexity
                            complexity += self._calculate_function_complexity(node)
                        elif isinstance(node, ast.ClassDef):
                            classes.append(node.name)
                            
                except SyntaxError:
                    # Fallback to regex if AST fails
                    imports = re.findall(r'^(?:from\s+(\w+)|import\s+([\w, ]+))', content, re.MULTILINE)
                    functions = re.findall(r'^def\s+(\w+)', content, re.MULTILINE)
                    classes = re.findall(r'^class\s+(\w+)', content, re.MULTILINE)
            
            elif file_type in [FileType.JAVASCRIPT, FileType.TYPESCRIPT]:
                # Regex-based parsing for JS/TS
                imports = re.findall(r'import\s+(?:.*?\s+from\s+)?[\'"]([^\'"]+)[\'"]', content)
                functions = re.findall(r'(?:function|const|let|var)\s+(\w+)\s*=', content)
                classes = re.findall(r'class\s+(\w+)', content)
            
            # General complexity calculation
            if content:
                complexity += (content.count('if') + content.count('for') + 
                             content.count('while') + content.count('try') + 
                             content.count('catch')) / len(content.splitlines()) * 10
            
        except Exception as e:
            self.logger.warning(f"Failed to parse content: {e}")
        
        return imports, functions, classes, min(complexity, 10.0)
    
    def _calculate_function_complexity(self, func_node: ast.FunctionDef) -> float:
        """Calculate cyclomatic complexity for a function."""
        complexity = 1.0  # Base complexity
        
        for node in ast.walk(func_node):
            if isinstance(node, (ast.If, ast.For, ast.While, ast.ExceptHandler)):
                complexity += 1.0
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1
        
        return complexity
    
    def _determine_project_type(self, files: List[Path]) -> ProjectType:
        """Determine project type based on file structure."""
        file_set = {f.name for f in files}
        dir_set = {str(f.parent).replace(str(self.root_path), "") for f in files}
        
        # Check for project type indicators
        for project_type, indicators in self.project_indicators.items():
            if all(indicator in file_set or indicator in dir_set for indicator in indicators):
                return project_type
        
        # Fallback based on file extensions
        python_files = sum(1 for f in files if f.suffix == '.py')
        js_files = sum(1 for f in files if f.suffix in ['.js', '.jsx', '.ts', '.tsx'])
        
        if python_files > js_files:
            if any('api' in str(f).lower() or 'server' in str(f).lower() for f in files):
                return ProjectType.API_SERVICE
            else:
                return ProjectType.MONOLITH
        else:
            return ProjectType.WEB_APP
    
    def _count_languages(self, file_infos: List[FileInfo]) -> Dict[str, int]:
        """Count files by language."""
        languages = {}
        for file_info in file_infos:
            if file_info.language != "Unknown":
                languages[file_info.language] = languages.get(file_info.language, 0) + 1
        return languages
    
    def _count_file_types(self, file_infos: List[FileInfo]) -> Dict[FileType, int]:
        """Count files by type."""
        file_types = {}
        for file_info in file_infos:
            file_types[file_info.file_type] = file_types.get(file_info.file_type, 0) + 1
        return file_types
    
    def _get_directories(self, files: List[Path]) -> List[str]:
        """Get list of directories."""
        directories = set()
        for file_path in files:
            dir_path = file_path.parent
            relative_path = str(dir_path).replace(str(self.root_path), "").lstrip("/")
            if relative_path:
                directories.add(relative_path)
        return sorted(list(directories))
    
    def _identify_main_files(self, file_infos: List[FileInfo]) -> List[str]:
        """Identify potential main entry files."""
        main_files = []
        
        for file_info in file_infos:
            filename = file_info.name.lower()
            if (filename in ['main.py', 'app.py', 'index.js', 'index.html', 
                           'server.js', 'app.ts', 'main.ts'] or
                filename.startswith('main_') or filename.startswith('app_')):
                main_files.append(file_info.path)
        
        return main_files
    
    def _identify_entry_points(self, file_infos: List[FileInfo]) -> List[str]:
        """Identify entry points based on imports and dependencies."""
        entry_points = []
        
        # Files that are not imported by others are likely entry points
        all_imports = set()
        for file_info in file_infos:
            all_imports.update(file_info.imports)
        
        for file_info in file_infos:
            # Check if this file is imported by others
            is_imported = any(
                file_info.name in imports 
                for other_file in file_infos 
                for imports in other_file.imports
            )
            
            if not is_imported and file_info.file_type in [FileType.PYTHON, FileType.JAVASCRIPT, FileType.TYPESCRIPT]:
                entry_points.append(file_info.path)
        
        return entry_points
    
    async def _extract_dependencies(self, file_infos: List[FileInfo]) -> Dict[str, Set[str]]:
        """Extract file dependencies based on imports."""
        dependencies = {}
        
        for file_info in file_infos:
            deps = set()
            
            # Look for local imports
            for imp in file_info.imports:
                # Try to find matching files
                for other_file in file_infos:
                    if (other_file.name in imp or 
                        other_file.path.endswith(imp) or
                        any(imp.endswith(f"/{other_file.name}") for f in file_infos)):
                        deps.add(other_file.path)
            
            dependencies[file_info.path] = deps
        
        return dependencies
    
    async def _extract_package_dependencies(self) -> Dict[str, str]:
        """Extract package dependencies from configuration files."""
        package_deps = {}
        
        # Check for requirements.txt
        req_file = self.root_path / "requirements.txt"
        if req_file.exists():
            try:
                with open(req_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            if '>=' in line:
                                pkg, version = line.split('>=')
                                package_deps[pkg.strip()] = version.strip()
                            else:
                                package_deps[line.strip()] = "latest"
            except Exception as e:
                self.logger.warning(f"Failed to parse requirements.txt: {e}")
        
        # Check for package.json
        pkg_file = self.root_path / "package.json"
        if pkg_file.exists():
            try:
                with open(pkg_file, 'r') as f:
                    data = json.load(f)
                    if "dependencies" in data:
                        for pkg, version in data["dependencies"].items():
                            package_deps[pkg] = version
            except Exception as e:
                self.logger.warning(f"Failed to parse package.json: {e}")
        
        # Check for pyproject.toml
        pyproject_file = self.root_path / "pyproject.toml"
        if pyproject_file.exists():
            try:
                import toml
                with open(pyproject_file, 'r') as f:
                    data = toml.load(f)
                    if "tool" in data and "poetry" in data["tool"] and "dependencies" in data["tool"]["poetry"]:
                        for pkg, version in data["tool"]["poetry"]["dependencies"].items():
                            if isinstance(version, dict):
                                version = version.get("version", "latest")
                            package_deps[pkg] = version
            except Exception as e:
                self.logger.warning(f"Failed to parse pyproject.toml: {e}")
        
        return package_deps
    
    def _find_config_files(self, file_infos: List[FileInfo]) -> List[str]:
        """Find configuration files."""
        config_files = []
        
        for file_info in file_infos:
            if (file_info.file_type == FileType.CONFIG or
                file_info.name.lower() in ['config.py', 'settings.py', 'config.json', '.env']):
                config_files.append(file_info.path)
        
        return config_files
    
    def _find_documentation_files(self, file_infos: List[FileInfo]) -> List[str]:
        """Find documentation files."""
        doc_files = []
        
        for file_info in file_infos:
            if (file_info.file_type == FileType.DOCUMENTATION or
                file_info.name.lower() in ['readme', 'license', 'contributing', 'changelog']):
                doc_files.append(file_info.path)
        
        return doc_files
    
    def _find_test_files(self, file_infos: List[FileInfo]) -> List[str]:
        """Find test files."""
        test_files = []
        
        for file_info in file_infos:
            if 'test' in file_info.name.lower() or 'spec' in file_info.name.lower():
                test_files.append(file_info.path)
        
        return test_files
    
    async def _get_git_info(self) -> Dict[str, Any]:
        """Get git repository information."""
        git_info = {}
        
        try:
            # Check if git repository
            git_dir = self.root_path / ".git"
            if not git_dir.exists():
                return git_info
            
            # Get git status
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.root_path,
                capture_output=True,
                text=True
            )
            
            git_info["is_repository"] = True
            git_info["dirty"] = bool(result.stdout.strip())
            git_info["status"] = result.stdout.strip()
            
            # Get git log
            result = subprocess.run(
                ["git", "log", "--oneline", "-5"],
                cwd=self.root_path,
                capture_output=True,
                text=True
            )
            
            git_info["recent_commits"] = result.stdout.strip().split('\n') if result.stdout.strip() else []
            
            # Get git remote
            result = subprocess.run(
                ["git", "remote", "-v"],
                cwd=self.root_path,
                capture_output=True,
                text=True
            )
            
            git_info["remotes"] = result.stdout.strip().split('\n') if result.stdout.strip() else []
            
        except Exception as e:
            self.logger.warning(f"Failed to get git info: {e}")
            git_info["error"] = str(e)
        
        return git_info
    
    async def _store_project_analysis(self, project_structure: ProjectStructure):
        """Store project analysis in memory."""
        try:
            # Store main analysis
            await memory_manager.store_memory(
                key="project_analysis",
                value=asdict(project_structure),
                memory_type="project_analysis",
                tags=["autonomous_coding", "project_structure"]
            )
            
            # Store file summary for quick access
            file_summary = {
                "total_files": project_structure.total_files,
                "total_lines": project_structure.total_lines,
                "languages": project_structure.languages,
                "project_type": project_structure.project_type.value,
                "main_files": project_structure.main_files,
                "entry_points": project_structure.entry_points,
                "timestamp": project_structure.analysis_timestamp.isoformat()
            }
            
            await memory_manager.store_memory(
                key="project_summary",
                value=file_summary,
                memory_type="project_summary",
                tags=["autonomous_coding", "quick_reference"]
            )
            
            self.logger.info("Project analysis stored in memory")
            
        except Exception as e:
            self.logger.error(f"Failed to store project analysis: {e}")
    
    def get_project_health(self, project_structure: ProjectStructure) -> Dict[str, Any]:
        """Get project health metrics."""
        total_files = project_structure.total_files
        test_files = len(project_structure.test_files)
        doc_files = len(project_structure.documentation_files)
        config_files = len(project_structure.configuration_files)
        
        # Calculate health scores
        test_coverage = (test_files / total_files * 100) if total_files > 0 else 0
        documentation_coverage = (doc_files / total_files * 100) if total_files > 0 else 0
        
        # Calculate average complexity
        avg_complexity = sum(f.complexity_score for f in project_structure.files) / len(project_structure.files) if project_structure.files else 0
        
        # Determine health status
        if test_coverage > 70 and documentation_coverage > 30 and avg_complexity < 5:
            health_status = "excellent"
        elif test_coverage > 40 and documentation_coverage > 20 and avg_complexity < 8:
            health_status = "good"
        elif test_coverage > 20 and documentation_coverage > 10:
            health_status = "fair"
        else:
            health_status = "needs_attention"
        
        return {
            "health_status": health_status,
            "test_coverage": test_coverage,
            "documentation_coverage": documentation_coverage,
            "average_complexity": avg_complexity,
            "total_files": total_files,
            "test_files": test_files,
            "doc_files": doc_files,
            "config_files": config_files,
            "project_type": project_structure.project_type.value,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


# Global instance
project_scanner = ProjectScanner()