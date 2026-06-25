"""
Virtual Office API — live local status for the Benz/Atsawin command center UI.

This router intentionally exposes only read-only system/MT5 status plus a local
command log. It does not execute trades, publish content, send email, or mutate
external services. Dangerous actions remain behind the owner approval workflow.
"""
from __future__ import annotations

import json
import os
import platform
import socket
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import psutil
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.office_store import DEFAULT_DB_PATH, OfficeStore, build_daily_brief, route_command_reply

router = APIRouter(prefix="/api/office", tags=["office"])
office_store = OfficeStore(DEFAULT_DB_PATH)

ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIR = ROOT / "frontend"
BRAIN_QUEUE = ROOT / "brain" / "task_queue.md"
LOG_DIR = ROOT / "logs"
COMMAND_LOG = LOG_DIR / "office_commands.jsonl"
COMMON_ATSAWIN = Path.home() / "AppData" / "Roaming" / "MetaQuotes" / "Terminal" / "Common" / "Files" / "atsawin"
SIGNAL_FILE = COMMON_ATSAWIN / "latest_signal.json"
EA_STATUS_FILE = COMMON_ATSAWIN / "ea_status.json"
EA_RUNTIME_FILE = COMMON_ATSAWIN / "ea_runtime_status.json"
GOOGLE_TOKEN = Path.home() / ".hermes" / "google_token.json"
GOOGLE_CLIENT = Path.home() / ".hermes" / "google_client_secret.json"


class OfficeCommand(BaseModel):
    text: str = Field(..., min_length=1, max_length=1000)
    source: str = Field(default="virtual-office", max_length=80)
    target: str = Field(default="mina", max_length=80)


class ApprovalDecision(BaseModel):
    note: str = Field(default="", max_length=500)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def file_age_seconds(path: Path) -> Optional[float]:
    if not path.exists():
        return None
    return max(0.0, time.time() - path.stat().st_mtime)


def read_json(path: Path) -> Optional[Dict[str, Any]]:
    try:
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception as exc:
        return {"_error": str(exc), "_path": str(path)}


def tail_text(path: Path, max_lines: int = 8) -> List[str]:
    try:
        if not path.exists():
            return []
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        return lines[-max_lines:]
    except Exception as exc:
        return [f"read error: {exc}"]


def proc_matches(name_part: str) -> List[Dict[str, Any]]:
    """Fast process lookup.

    Avoid reading cmdline for every process on Windows; that can stall the UI API
    for 10+ seconds under MSYS/permission boundaries. Name-only is enough for
    the dashboard health lights.
    """
    rows: List[Dict[str, Any]] = []
    needle = name_part.lower()
    for proc in psutil.process_iter(["pid", "name", "create_time", "status"]):
        try:
            info = proc.info
            name = info.get("name") or ""
            if needle in name.lower():
                rows.append({
                    "pid": info.get("pid"),
                    "name": name,
                    "status": info.get("status"),
                    "cmdline": name,
                    "started_at": datetime.fromtimestamp(info.get("create_time", 0), timezone.utc).isoformat() if info.get("create_time") else None,
                })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return rows


def system_status() -> Dict[str, Any]:
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("C:\\")
    return {
        "hostname": socket.gethostname(),
        "platform": platform.platform(),
        "cpu_percent": psutil.cpu_percent(interval=0.05),
        "memory_percent": mem.percent,
        "memory_used_gb": round(mem.used / (1024 ** 3), 2),
        "memory_total_gb": round(mem.total / (1024 ** 3), 2),
        "disk_percent": disk.percent,
        "disk_used_gb": round(disk.used / (1024 ** 3), 2),
        "disk_total_gb": round(disk.total / (1024 ** 3), 2),
    }


def integration_status(signal: Optional[Dict[str, Any]], runtime: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    signal_age = file_age_seconds(SIGNAL_FILE)
    runtime_age = file_age_seconds(EA_RUNTIME_FILE)
    bridge_live = bool(signal) and (signal_age or 999999) < 3600
    mt5_live = bool(runtime or signal) and min(signal_age or 999999, runtime_age or 999999) < 3600
    return [
        {"id": "backend", "name": "FastAPI Backend", "status": "online", "detail": "API reachable"},
        {"id": "mt5", "name": "MetaTrader 5", "status": "online" if mt5_live else "offline", "detail": "fresh MT5/EA file" if mt5_live else "no fresh file"},
        {"id": "bridge", "name": "MT5 Bridge", "status": "online" if bridge_live else "offline", "detail": "fresh signal file" if bridge_live else "stale/missing signal"},
        {"id": "signal", "name": "Signal File", "status": "online" if signal else "offline", "detail": f"age {round(file_age_seconds(SIGNAL_FILE) or 0)}s" if signal else "missing"},
        {"id": "ea", "name": "EA Runtime", "status": "online" if runtime else "offline", "detail": (runtime or {}).get("decision", "missing")},
        {"id": "notion", "name": "Notion", "status": "setup_needed" if not os.getenv("NOTION_API_KEY") else "configured", "detail": "NOTION_API_KEY" if os.getenv("NOTION_API_KEY") else "missing token"},
        {"id": "google", "name": "Google Workspace", "status": "configured" if GOOGLE_TOKEN.exists() and GOOGLE_CLIENT.exists() else "setup_needed", "detail": "OAuth token" if GOOGLE_TOKEN.exists() else "missing OAuth"},
    ]


def agent_rows(signal: Optional[Dict[str, Any]], runtime: Optional[Dict[str, Any]], integrations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    integ = {i["id"]: i for i in integrations}
    return [
        {"name": "Mina", "role": "AI Secretary", "status": "online", "queue": 3, "risk": "low", "detail": "Routing commands and daily brief"},
        {"name": "Leo", "role": "Meta Ads Analyst", "status": "setup_needed", "queue": 1, "risk": "medium", "detail": "Needs Meta API integration"},
        {"name": "Sam", "role": "Google Tracking", "status": integ.get("google", {}).get("status", "unknown"), "queue": 2, "risk": "medium", "detail": integ.get("google", {}).get("detail", "")},
        {"name": "Ava", "role": "Admin / Documents", "status": integ.get("notion", {}).get("status", "unknown"), "queue": 2, "risk": "low", "detail": integ.get("notion", {}).get("detail", "")},
        {"name": "MT5", "role": "Trading Journal Monitor", "status": "online" if signal or runtime else "offline", "queue": 1 if signal else 0, "risk": "high", "detail": f"{(signal or {}).get('signal', 'no signal')} / {(runtime or {}).get('decision', 'no runtime')}"},
        {"name": "Owner", "role": "Benz Approval", "status": "online", "queue": 0, "risk": "owner", "detail": "Final approval required for write/publish/trade actions"},
    ]


def workflow_rows(signal: Optional[Dict[str, Any]], runtime: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    tasks: List[Dict[str, Any]] = []
    if signal:
        tasks.append({
            "title": f"MT5 signal: {signal.get('signal', 'unknown').upper()}",
            "lane": "In Progress",
            "detail": f"{signal.get('mt5_symbol', signal.get('symbol', ''))} {signal.get('timeframe', '')} conf={signal.get('confidence', 0)}",
            "risk": "high",
        })
    if runtime:
        tasks.append({
            "title": f"EA decision: {runtime.get('decision', 'unknown')}",
            "lane": "Waiting Approval" if runtime.get("decision") == "SKIP" else "Done / Audit",
            "detail": runtime.get("reason", "runtime status"),
            "risk": "high",
        })
    for line in tail_text(BRAIN_QUEUE, 6):
        if line.strip().startswith("-"):
            tasks.append({"title": line.strip("- ")[:80], "lane": "Backlog", "detail": "brain/task_queue.md", "risk": "medium"})
    if not tasks:
        tasks.append({"title": "No live workflow items", "lane": "Done / Audit", "detail": "System idle", "risk": "low"})
    return tasks[:12]


def latest_commands(limit: int = 8) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    if not COMMAND_LOG.exists():
        return rows
    for line in tail_text(COMMAND_LOG, limit):
        try:
            rows.append(json.loads(line))
        except Exception:
            rows.append({"text": line, "created_at": None})
    return rows


@router.get("/status")
async def office_status() -> Dict[str, Any]:
    signal = read_json(SIGNAL_FILE)
    ea_status = read_json(EA_STATUS_FILE)
    runtime = read_json(EA_RUNTIME_FILE)
    integrations = integration_status(signal, runtime)
    office_store.ingest_snapshot(signal=signal, ea_status=ea_status, runtime=runtime)
    journal_summary = office_store.summary()
    approvals = office_store.list_approvals(status="waiting_owner_approval")
    daily_brief = build_daily_brief(journal_summary, approvals)
    sys = system_status()
    approval_count = len(approvals)
    return {
        "ok": True,
        "generated_at": now_iso(),
        "system": sys,
        "kpis": {
            "waiting_approval": approval_count,
            "need_attention": sum(1 for i in integrations if i["status"] in {"offline", "setup_needed"}),
            "read_only_sources": 3,
            "audit_events": journal_summary.get("commands_count", 0),
            "secrets_exposed": 0,
            "production_release": "Locked",
        },
        "integrations": integrations,
        "trading": {
            "latest_signal": signal,
            "ea_status": ea_status,
            "ea_runtime_status": runtime,
            "signal_age_seconds": file_age_seconds(SIGNAL_FILE),
            "runtime_age_seconds": file_age_seconds(EA_RUNTIME_FILE),
        },
        "agents": agent_rows(signal, runtime, integrations),
        "workflow": workflow_rows(signal, runtime) + [
            {"title": a["title"], "lane": "Waiting Approval", "detail": a["detail"], "risk": a["risk"], "approval_id": a["id"]}
            for a in approvals[:6]
        ],
        "commands": office_store.list_commands(),
        "approvals": approvals,
        "journal": journal_summary,
        "daily_brief": daily_brief,
        "paths": {
            "signal_file": str(SIGNAL_FILE),
            "ea_status_file": str(EA_STATUS_FILE),
            "ea_runtime_file": str(EA_RUNTIME_FILE),
            "command_log": str(COMMAND_LOG),
        },
    }


@router.post("/command")
async def office_command(command: OfficeCommand) -> Dict[str, Any]:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    record = office_store.record_command(
        command.text.strip(),
        source=command.source,
        target=command.target,
    )
    if record.get("risk") == "low":
        record["reply"] = route_command_reply(command.text, office_store)
    else:
        record["reply"] = f"{record['reply']}\n{route_command_reply('งานไหนต้อง approve', office_store)}"
    # Keep the previous JSONL log for compatibility with old tooling.
    with COMMAND_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    return {"ok": True, "command": record}


@router.get("/brief")
async def office_brief() -> Dict[str, Any]:
    return {"ok": True, "brief": build_daily_brief(office_store.summary(), office_store.list_approvals(status="waiting_owner_approval"))}


@router.get("/approvals")
async def office_approvals(status: Optional[str] = None) -> Dict[str, Any]:
    return {"ok": True, "approvals": office_store.list_approvals(status=status)}


@router.post("/approvals/{approval_id}/approve")
async def approve_action(approval_id: str, decision: ApprovalDecision) -> Dict[str, Any]:
    item = office_store.decide_approval(approval_id, "approved", decision.note)
    if not item:
        raise HTTPException(status_code=404, detail="Approval not found")
    return {"ok": True, "approval": item}


@router.post("/approvals/{approval_id}/reject")
async def reject_action(approval_id: str, decision: ApprovalDecision) -> Dict[str, Any]:
    item = office_store.decide_approval(approval_id, "rejected", decision.note)
    if not item:
        raise HTTPException(status_code=404, detail="Approval not found")
    return {"ok": True, "approval": item}
