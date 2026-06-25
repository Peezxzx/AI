"""Local Office journal storage for Atsawin Virtual Office.

SQLite-backed, dependency-free persistence for the local command center:
- signal snapshots from MT5 bridge files
- EA runtime decisions
- command logs
- approval queue for risky actions
- generated daily brief context

This module is deliberately local-first and safe: it records/queues actions, but
never executes trades, publishes content, or mutates external systems.
"""
from __future__ import annotations

import json
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB_PATH = ROOT / "data" / "office_journal.db"

RISK_WORDS = [
    "trade", "buy", "sell", "order", "publish", "delete", "send email",
    "ซื้อ", "ขาย", "ลบ", "โพสต์", "ส่งเมล", "เปิดออเดอร์", "ปิดออเดอร์",
]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _json(data: Any) -> str:
    return json.dumps(data or {}, ensure_ascii=False, sort_keys=True)


def _loads(text: Optional[str]) -> Any:
    if not text:
        return None
    try:
        return json.loads(text)
    except Exception:
        return text


def classify_command_risk(text: str) -> Dict[str, str]:
    """Classify a user command before routing it.

    Read-only questions are logged. Anything that looks like a trade, publish,
    deletion, or external-send request is held for owner approval.
    """
    lower = (text or "").lower()
    if any(word in lower for word in RISK_WORDS):
        return {
            "risk": "approval_required",
            "status": "waiting_owner_approval",
            "reply": "คำสั่งนี้เป็น action เสี่ยง/เขียนข้อมูลจริง จึงถูกพักไว้ใน approval gate ก่อนดำเนินการ",
        }
    return {
        "risk": "low",
        "status": "logged",
        "reply": "รับคำสั่งแล้วครับ บันทึกเข้า local journal และ route ให้ Mina ตรวจต่อ",
    }


class OfficeStore:
    def __init__(self, db_path: Path | str = DEFAULT_DB_PATH):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_db()

    def connect(self) -> sqlite3.Connection:
        con = sqlite3.connect(str(self.db_path))
        con.row_factory = sqlite3.Row
        return con

    def init_db(self) -> None:
        with self.connect() as con:
            con.executescript(
                """
                CREATE TABLE IF NOT EXISTS signal_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    signal_id TEXT,
                    symbol TEXT,
                    timeframe TEXT,
                    signal TEXT,
                    confidence REAL,
                    entry_price REAL,
                    stop_loss REAL,
                    take_profit REAL,
                    payload TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    UNIQUE(signal_id, created_at)
                );
                CREATE INDEX IF NOT EXISTS idx_signal_created ON signal_snapshots(created_at DESC);

                CREATE TABLE IF NOT EXISTS ea_runtime_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    signal_id TEXT,
                    decision TEXT,
                    reason TEXT,
                    symbol TEXT,
                    payload TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    UNIQUE(signal_id, decision, reason, created_at)
                );
                CREATE INDEX IF NOT EXISTS idx_runtime_created ON ea_runtime_snapshots(created_at DESC);

                CREATE TABLE IF NOT EXISTS commands (
                    id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    source TEXT NOT NULL,
                    target TEXT NOT NULL,
                    text TEXT NOT NULL,
                    status TEXT NOT NULL,
                    risk TEXT NOT NULL,
                    reply TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS approvals (
                    id TEXT PRIMARY KEY,
                    command_id TEXT,
                    title TEXT NOT NULL,
                    detail TEXT NOT NULL,
                    risk TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    decided_at TEXT,
                    decision_note TEXT,
                    FOREIGN KEY(command_id) REFERENCES commands(id)
                );
                CREATE INDEX IF NOT EXISTS idx_approvals_status ON approvals(status, created_at DESC);
                """
            )

    def ingest_snapshot(
        self,
        signal: Optional[Dict[str, Any]],
        ea_status: Optional[Dict[str, Any]],
        runtime: Optional[Dict[str, Any]],
    ) -> None:
        created_at = now_iso()
        with self.connect() as con:
            if signal and not signal.get("_error"):
                con.execute(
                    """
                    INSERT INTO signal_snapshots
                    (signal_id, symbol, timeframe, signal, confidence, entry_price, stop_loss, take_profit, payload, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        signal.get("signal_id") or signal.get("setup_key") or f"signal-{int(time.time()*1000)}",
                        signal.get("mt5_symbol") or signal.get("symbol"),
                        signal.get("timeframe"),
                        signal.get("signal"),
                        float(signal.get("confidence") or 0),
                        signal.get("entry_price"),
                        signal.get("stop_loss"),
                        signal.get("take_profit"),
                        _json(signal),
                        created_at,
                    ),
                )
            if runtime and not runtime.get("_error"):
                con.execute(
                    """
                    INSERT INTO ea_runtime_snapshots
                    (signal_id, decision, reason, symbol, payload, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        runtime.get("signal_id") or runtime.get("setup_key") or f"runtime-{int(time.time()*1000)}",
                        runtime.get("decision"),
                        runtime.get("reason"),
                        runtime.get("symbol") or runtime.get("mt5_symbol"),
                        _json(runtime),
                        created_at,
                    ),
                )

    def record_command(self, text: str, source: str, target: str) -> Dict[str, Any]:
        classification = classify_command_risk(text)
        record = {
            "id": f"cmd_{int(time.time() * 1000)}",
            "created_at": now_iso(),
            "source": source,
            "target": target,
            "text": text.strip(),
            **classification,
        }
        with self.connect() as con:
            con.execute(
                "INSERT INTO commands (id, created_at, source, target, text, status, risk, reply) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (record["id"], record["created_at"], source, target, record["text"], record["status"], record["risk"], record["reply"]),
            )
            if record["status"] == "waiting_owner_approval":
                approval = {
                    "id": f"appr_{int(time.time() * 1000)}",
                    "command_id": record["id"],
                    "title": f"Approve command: {record['text'][:80]}",
                    "detail": record["text"],
                    "risk": record["risk"],
                    "status": "waiting_owner_approval",
                    "created_at": record["created_at"],
                }
                con.execute(
                    "INSERT INTO approvals (id, command_id, title, detail, risk, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (approval["id"], approval["command_id"], approval["title"], approval["detail"], approval["risk"], approval["status"], approval["created_at"]),
                )
        return record

    def list_commands(self, limit: int = 20) -> List[Dict[str, Any]]:
        with self.connect() as con:
            rows = con.execute("SELECT * FROM commands ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        return [dict(r) for r in rows][::-1]

    def list_approvals(self, status: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        with self.connect() as con:
            if status:
                rows = con.execute("SELECT * FROM approvals WHERE status=? ORDER BY created_at DESC LIMIT ?", (status, limit)).fetchall()
            else:
                rows = con.execute("SELECT * FROM approvals ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        return [dict(r) for r in rows]

    def decide_approval(self, approval_id: str, decision: str, note: str = "") -> Optional[Dict[str, Any]]:
        if decision not in {"approved", "rejected"}:
            raise ValueError("decision must be approved or rejected")
        decided_at = now_iso()
        with self.connect() as con:
            row = con.execute("SELECT * FROM approvals WHERE id=?", (approval_id,)).fetchone()
            if not row:
                return None
            con.execute(
                "UPDATE approvals SET status=?, decided_at=?, decision_note=? WHERE id=?",
                (decision, decided_at, note, approval_id),
            )
            if row["command_id"]:
                con.execute("UPDATE commands SET status=? WHERE id=?", (decision, row["command_id"]))
        updated = dict(row)
        updated.update({"status": decision, "decided_at": decided_at, "decision_note": note})
        return updated

    def summary(self) -> Dict[str, Any]:
        with self.connect() as con:
            sig_count = con.execute("SELECT COUNT(*) FROM signal_snapshots").fetchone()[0]
            run_count = con.execute("SELECT COUNT(*) FROM ea_runtime_snapshots").fetchone()[0]
            cmd_count = con.execute("SELECT COUNT(*) FROM commands").fetchone()[0]
            waiting = con.execute("SELECT COUNT(*) FROM approvals WHERE status='waiting_owner_approval'").fetchone()[0]
            latest_signal = con.execute("SELECT * FROM signal_snapshots ORDER BY created_at DESC LIMIT 1").fetchone()
            latest_runtime = con.execute("SELECT * FROM ea_runtime_snapshots ORDER BY created_at DESC LIMIT 1").fetchone()
            skip_rows = con.execute(
                """
                SELECT COALESCE(reason, 'unknown') AS reason, COUNT(*) AS count
                FROM ea_runtime_snapshots
                WHERE decision='SKIP'
                GROUP BY reason
                ORDER BY count DESC
                LIMIT 5
                """
            ).fetchall()
            signal_mix = con.execute(
                """
                SELECT COALESCE(signal, 'unknown') AS signal, COUNT(*) AS count
                FROM signal_snapshots GROUP BY signal ORDER BY count DESC
                """
            ).fetchall()
        return {
            "signals_count": sig_count,
            "runtime_count": run_count,
            "commands_count": cmd_count,
            "waiting_approval": waiting,
            "latest_signal": _row_with_payload(latest_signal),
            "latest_runtime": _row_with_payload(latest_runtime),
            "skip_reasons": [dict(r) for r in skip_rows],
            "signal_mix": [dict(r) for r in signal_mix],
        }


def _row_with_payload(row: Optional[sqlite3.Row]) -> Optional[Dict[str, Any]]:
    if not row:
        return None
    data = dict(row)
    payload = _loads(data.pop("payload", None)) or {}
    payload.update({k: v for k, v in data.items() if v is not None})
    return payload


def build_daily_brief(summary: Dict[str, Any], approvals: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    latest_signal = summary.get("latest_signal") or {}
    latest_runtime = summary.get("latest_runtime") or {}
    symbol = latest_signal.get("mt5_symbol") or latest_signal.get("symbol") or latest_runtime.get("symbol") or "XAUUSDm"
    signal = str(latest_signal.get("signal") or "none").upper()
    confidence = latest_signal.get("confidence", 0)
    decision = latest_runtime.get("decision") or "none"
    reason = latest_runtime.get("reason") or "no runtime reason"
    waiting = len(list(approvals))
    skip_reasons = summary.get("skip_reasons") or []
    top_skip = skip_reasons[0]["reason"] if skip_reasons else reason
    return {
        "generated_at": now_iso(),
        "headline": f"{symbol}: latest signal {signal} confidence {confidence}",
        "trading_summary": f"EA decision ล่าสุด: {decision} / {reason}. Signals logged: {summary.get('signals_count', 0)}; runtime events: {summary.get('runtime_count', 0)}.",
        "risk_notes": f"Top skip reason: {top_skip}. Waiting approvals: {waiting}. Owner gate remains locked for trade/publish/delete actions.",
        "recommendation": _recommendation(decision, reason, waiting),
        "waiting_approval": waiting,
        "signal_mix": summary.get("signal_mix", []),
        "skip_reasons": skip_reasons,
    }


def route_command_reply(text: str, store: OfficeStore) -> str:
    """Return a useful local answer for common Virtual Office commands.

    This is the first small task engine: it does not execute external actions;
    it routes read-only intents to journal/brief/approval data so the chat feels
    alive and useful immediately.
    """
    lower = (text or "").lower()
    summary = store.summary()
    approvals = store.list_approvals(status="waiting_owner_approval")

    if any(token in lower for token in ["mt5", "ea", "สถานะ", "signal"]):
        sig = summary.get("latest_signal") or {}
        rt = summary.get("latest_runtime") or {}
        signal = str(sig.get("signal") or "none").upper()
        return (
            f"MT5/EA status: {sig.get('mt5_symbol') or sig.get('symbol') or 'XAUUSDm'} "
            f"{sig.get('timeframe') or ''} signal={signal} conf={sig.get('confidence', 0)}. "
            f"EA={rt.get('decision') or 'none'} / {rt.get('reason') or 'no reason'}. "
            f"Journal: signals={summary.get('signals_count', 0)}, runtime={summary.get('runtime_count', 0)}."
        )

    if any(token in lower for token in ["brief", "report", "รายงาน", "สรุปวันนี้", "daily"]):
        brief = build_daily_brief(summary, approvals)
        return (
            f"Daily Brief — {brief['headline']}\n"
            f"{brief['trading_summary']}\n"
            f"Risk: {brief['risk_notes']}\n"
            f"Recommendation: {brief['recommendation']}"
        )

    if any(token in lower for token in ["approve", "approval", "อนุมัติ", "รอ"]):
        if not approvals:
            return "Approval Board: ไม่มีคำสั่งเสี่ยงที่รออนุมัติอยู่ตอนนี้"
        lines = [f"Approval Board: มี {len(approvals)} งานรออนุมัติ"]
        lines.extend(f"- {a['title']} ({a['risk']})" for a in approvals[:5])
        return "\n".join(lines)

    return "Mina รับคำสั่งแล้วค่ะ ตอนนี้รองรับ read-only status, daily brief และ approval list ผ่าน local task engine"


def _recommendation(decision: str, reason: str, waiting: int) -> str:
    reason_l = (reason or "").lower()
    if waiting:
        return "ตรวจ Approval Board ก่อน เพราะมีคำสั่งเสี่ยงรอเจ้าของตัดสินใจ"
    if "basket_loss" in reason_l or "drawdown" in reason_l:
        return "ลดความเสี่ยง/หยุดเทรดชั่วคราวจนกว่า loss guard จะเคลียร์"
    if "hard_magic_cap" in reason_l:
        return "หยุดเปิดไม้เพิ่มก่อน เพราะ EA ชน hard magic cap แล้ว ให้จัดการ position เดิมก่อน"
    if "invalid_sl_tp" in reason_l:
        return "ตรวจ SL/TP geometry ก่อนเข้าไม้ เพราะ EA มองว่าระยะไม่ valid"
    if "entry_gap" in reason_l or "too_soon" in reason_l:
        return "รอ setup ใหม่ อย่าไล่ราคา เพราะ EA skip จาก entry gap/จังหวะเร็วเกินไป"
    if str(decision).upper() == "SKIP":
        return "ยังไม่ควรบังคับเข้าไม้ ให้เก็บข้อมูลเพิ่มและรอ confirmation"
    return "ระบบปกติ ใช้ dashboard เป็น journal และให้ owner approve action เสี่ยงก่อนเสมอ"
