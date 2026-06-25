import json
from pathlib import Path

from backend.office_store import OfficeStore, classify_command_risk, build_daily_brief


def test_office_store_ingests_signal_and_runtime_snapshots(tmp_path):
    store = OfficeStore(tmp_path / "office.db")
    signal = {
        "signal_id": "sig-1",
        "signal": "sell",
        "confidence": 0.91,
        "mt5_symbol": "XAUUSDm",
        "timeframe": "M15",
        "entry_price": 4479.63,
        "stop_loss": 4493.2,
        "take_profit": 4460.62,
    }
    runtime = {
        "signal_id": "sig-1",
        "decision": "SKIP",
        "reason": "entry_gap_too_soon",
        "symbol": "XAUUSDm",
        "magic_positions": 3,
    }

    store.ingest_snapshot(signal=signal, ea_status=None, runtime=runtime)
    summary = store.summary()

    assert summary["signals_count"] == 1
    assert summary["runtime_count"] == 1
    assert summary["latest_signal"]["signal"] == "sell"
    assert summary["latest_runtime"]["reason"] == "entry_gap_too_soon"
    assert summary["skip_reasons"][0]["reason"] == "entry_gap_too_soon"


def test_risky_command_creates_waiting_approval(tmp_path):
    store = OfficeStore(tmp_path / "office.db")
    record = store.record_command("buy XAUUSD now", source="test", target="mina")

    assert record["status"] == "waiting_owner_approval"
    assert record["risk"] == "approval_required"

    approvals = store.list_approvals(status="waiting_owner_approval")
    assert len(approvals) == 1
    assert approvals[0]["command_id"] == record["id"]
    assert approvals[0]["title"] == "Approve command: buy XAUUSD now"


def test_classify_command_risk_keeps_read_only_safe():
    risk = classify_command_risk("สรุปสถานะ MT5 วันนี้")
    assert risk["risk"] == "low"
    assert risk["status"] == "logged"


def test_build_daily_brief_contains_actionable_trading_context(tmp_path):
    store = OfficeStore(tmp_path / "office.db")
    store.ingest_snapshot(
        signal={"signal_id": "sig-1", "signal": "sell", "confidence": 1.0, "mt5_symbol": "XAUUSDm", "timeframe": "M15"},
        ea_status=None,
        runtime={"signal_id": "sig-1", "decision": "SKIP", "reason": "basket_loss_guard"},
    )
    store.record_command("buy XAUUSD now", source="test", target="mina")

    brief = build_daily_brief(store.summary(), store.list_approvals())

    assert "XAUUSDm" in brief["headline"]
    assert "SKIP" in brief["trading_summary"]
    assert "basket_loss_guard" in brief["risk_notes"]
    assert brief["waiting_approval"] == 1
