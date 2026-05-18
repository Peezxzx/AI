# AUTONOMOUS CODING PIPELINE CONTRACTS

## Interface Definitions for Pipeline Operations

---

## 1. Pipeline Execution Contract

### Run Pipeline
```
POST /pipeline/run
Request:
{
    "plan": [
        {
            "action": "create" | "modify" | "patch" | "append" | "delete",
            "path": string,
            "content": string (for create/modify/append),
            "old_string": string (for patch),
            "new_string": string (for patch),
            "overwrite": boolean (default: false),
            "replace_all": boolean (default: false)
        }
    ],
    "scan_only": boolean (default: false),
    "update_memory": boolean (default: false),
    "dry_run": boolean (default: false)
}
Response:
{
    "pipeline_id": string,
    "status": "started",
    "submitted_at": ISO8601 timestamp
}
```

### Get Pipeline Status
```
GET /pipeline/status/{pipeline_id}
Response:
{
    "pipeline_id": string,
    "status": "running" | "completed" | "failed",
    "phase": "idle" | "scanning" | "planning" | "coding" | "validating" | "updating_memory" | "completed" | "failed",
    "progress": float (0.0 - 1.0),
    "files_created": int,
    "files_modified": int,
    "errors": string[],
    "started_at": ISO8601 timestamp,
    "completed_at": ISO8601 timestamp | null,
    "duration_seconds": float
}
```

### Get Pipeline Report
```
GET /pipeline/report/{pipeline_id}
Response:
{
    "pipeline_id": string,
    "success": boolean,
    "phase_reached": string,
    "tasks_total": int,
    "tasks_completed": int,
    "tasks_failed": int,
    "files_created": int,
    "files_modified": int,
    "scan_summary": {
        "total_files": int,
        "languages": object,
        "total_lines": int
    },
    "errors": string[],
    "duration_seconds": float
}
```

---

## 2. Project Scan Contract

### Scan Project
```
GET /pipeline/scan?path={root_path}
Response:
{
    "total_files": int,
    "languages": {
        "python": {"files": int, "lines": int},
        "javascript": {"files": int, "lines": int}
    },
    "total_lines": int,
    "dependencies": string[],
    "structure": {
        "directories": int,
        "max_depth": int,
        "largest_files": [{"path": string, "lines": int}]
    },
    "scanned_at": ISO8601 timestamp
}
```

---

## 3. Code Quality Contract

### Analyze Code Quality
```
POST /pipeline/quality/analyze
Request:
{
    "path": string (file or directory),
    "checks": ["syntax" | "style" | "complexity" | "security" | "all"]
}
Response:
{
    "path": string,
    "overall_score": float (0.0 - 1.0),
    "issues": [
        {
            "type": string,
            "severity": "info" | "warning" | "error" | "critical",
            "file": string,
            "line": int,
            "message": string,
            "suggestion": string
        }
    ],
    "metrics": {
        "lines_of_code": int,
        "comment_ratio": float,
        "cyclomatic_complexity": float,
        "duplication_percentage": float
    }
}
```

---

## 4. Git Integration Contract

### Git Status
```
GET /pipeline/git/status
Response:
{
    "branch": string,
    "clean": boolean,
    "modified_files": string[],
    "untracked_files": string[],
    "last_commit": {
        "hash": string,
        "message": string,
        "author": string,
        "timestamp": ISO8601 timestamp
    }
}
```

### Git Commit
```
POST /pipeline/git/commit
Request:
{
    "message": string,
    "files": string[] (empty = all staged),
    "push": boolean (default: false)
}
Response:
{
    "commit_hash": string,
    "message": string,
    "files_committed": int,
    "pushed": boolean
}
```

### Create Branch
```
POST /pipeline/git/branch
Request:
{
    "branch_name": string,
    "from_branch": string (default: "main"),
    "checkout": boolean (default: true)
}
Response:
{
    "branch_name": string,
    "created": boolean,
    "checked_out": boolean
}
```

---

## 5. CI/CD Contract

### Trigger Pipeline
```
POST /pipeline/cicd/trigger
Request:
{
    "environment": "development" | "staging" | "production",
    "tests": boolean (default: true),
    "lint": boolean (default: true),
    "build": boolean (default: true),
    "deploy": boolean (default: false)
}
Response:
{
    "run_id": string,
    "status": "triggered",
    "environment": string,
    "triggered_at": ISO8601 timestamp
}
```

### Get CI/CD Status
```
GET /pipeline/cicd/status/{run_id}
Response:
{
    "run_id": string,
    "status": "running" | "passed" | "failed",
    "stages": [
        {
            "name": string,
            "status": "pending" | "running" | "passed" | "failed",
            "duration_seconds": float
        }
    ],
    "started_at": ISO8601 timestamp,
    "completed_at": ISO8601 timestamp | null
}
```

---

## 6. Testing Contract

### Run Tests
```
POST /pipeline/tests/run
Request:
{
    "test_type": "unit" | "integration" | "e2e" | "all",
    "path": string (optional, default: project root),
    "coverage": boolean (default: true),
    "parallel": boolean (default: true)
}
Response:
{
    "test_run_id": string,
    "status": "started",
    "total_tests": int,
    "passed": int,
    "failed": int,
    "skipped": int,
    "coverage_percentage": float,
    "duration_seconds": float,
    "failures": [
        {
            "test_name": string,
            "file": string,
            "line": int,
            "error": string
        }
    ]
}
```

---

## Error Codes

| Code | Meaning |
|------|---------|
| 5001 | Pipeline not found |
| 5002 | Invalid plan format |
| 5003 | File operation failed |
| 5004 | Git operation failed |
| 5005 | Test execution failed |
| 5006 | CI/CD trigger failed |
| 5007 | Quality check failed |
| 5008 | Scan failed |
| 5009 | Dry run validation failed |
| 5010 | Pipeline timeout |
