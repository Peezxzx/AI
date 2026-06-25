"""
Validation test for session optimization fix:
Ensures optimize_session_hours_from_trade_log never returns < min_hours
and that the fallback/padding logic works correctly.
"""
import csv
import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import ea.bridge_mt5_pro as _bridge
from ea.bridge_mt5_pro import optimize_session_hours_from_trade_log

def _CONFIG():
    """Return the current CONFIG dict, resilient to importlib.reload()."""
    return _bridge.CONFIG


def make_trade_log(rows, path):
    """Write a CSV trade log with the given rows."""
    header = "timestamp,bar_index,symbol,timeframe,side,entry,stop_loss,take_profit,rr,confidence,outcome,pnl_r,reason\n"
    with open(path, "w", encoding="utf-8") as f:
        f.write(header)
        for r in rows:
            f.write(
                f"{r['timestamp']},{r.get('bar_index',0)},{r.get('symbol','XAUUSDm')},"
                f"{r.get('timeframe','M15')},{r.get('side','sell')},"
                f"{r.get('entry',4483.0):.2f},{r.get('stop_loss',4506.0):.2f},"
                f"{r.get('take_profit',4465.0):.2f},{r.get('rr',1.56):.2f},"
                f"{r.get('confidence',0.71):.3f},{r.get('outcome','loss')},"
                f"{r.get('pnl_r',-1.0):.2f},{r.get('reason','sl_hit')}\n"
            )


def test_session_opt_never_returns_empty():
    """With sufficient data, session opt should return >= min_hours hours."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        tmp_path = f.name

    try:
        # Create trades spread across 6 hours with 10+ trades each (60+ total)
        rows = []
        for h in range(6):
            for i in range(10):
                rows.append({
                    "timestamp": f"2026-06-01T{h:02d}:{i:02d}:00+00:00",
                    "outcome": "win" if h < 4 else "loss",
                    "pnl_r": 1.56 if h < 4 else -1.0,
                    "confidence": 0.71,
                    "side": "sell",
                    "bar_index": h * 10 + i,
                    "symbol": "XAUUSDm",
                    "timeframe": "M15",
                    "entry": 4483.0,
                    "stop_loss": 4506.0,
                    "take_profit": 4465.0,
                    "rr": 1.56,
                    "reason": "tp_hit" if h < 4 else "sl_hit",
                })

        make_trade_log(rows, tmp_path)

        # Patch CONFIG to use our temp file
        cfg = _CONFIG()
        old_path = cfg["trade_log_csv"]
        cfg["trade_log_csv"] = tmp_path
        cfg["session_opt_json"] = tmp_path.replace(".csv", "_sess.json")
        cfg["session_opt_txt"] = tmp_path.replace(".csv", "_sess.txt")

        result = optimize_session_hours_from_trade_log()
        assert result is not None, "Session opt returned None — should always produce result with data"
        assert len(result["new_hours"]) >= 4, (
            f"Expected >= 4 hours with min_hours=4, got {len(result['new_hours'])}: {result['new_hours']}"
        )
        print(f"PASS: session opt returned {result['new_hours']} (mode={result['selection_mode']})")
    finally:
        _CONFIG()["trade_log_csv"] = old_path
        os.unlink(tmp_path)
        for suffix in ["_sess.json", "_sess.txt"]:
            p = tmp_path.replace(".csv", suffix)
            if os.path.exists(p):
                os.unlink(p)


def test_session_opt_mode_strict_when_enough_good_hours():
    """When enough hours pass strict criteria, mode should be 'strict'."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        tmp_path = f.name

    try:
        rows = []
        # Use 10+ trades per hour and 50+ total to pass new statistical guards
        for h in range(6):
            for i in range(10):
                rows.append({
                    "timestamp": f"2026-06-01T{h:02d}:{i:02d}:00+00:00",
                    "outcome": "win",
                    "pnl_r": 1.56,
                    "confidence": 0.71,
                    "side": "sell",
                    "bar_index": h * 10 + i,
                    "symbol": "XAUUSDm",
                    "timeframe": "M15",
                    "entry": 4483.0,
                    "stop_loss": 4506.0,
                    "take_profit": 4465.0,
                    "rr": 1.56,
                    "reason": "tp_hit",
                })

        make_trade_log(rows, tmp_path)

        cfg = _CONFIG()
        old_path = cfg["trade_log_csv"]
        cfg["trade_log_csv"] = tmp_path
        cfg["session_opt_json"] = tmp_path.replace(".csv", "_sess.json")
        cfg["session_opt_txt"] = tmp_path.replace(".csv", "_sess.txt")

        result = optimize_session_hours_from_trade_log()
        assert result is not None
        assert result["selection_mode"] == "strict", (
            f"Expected mode='strict', got '{result['selection_mode']}'"
        )
        assert 0 in result["new_hours"], "Hour 0 should be in selected hours"
        print(f"PASS: session opt mode={result['selection_mode']}, hours={result['new_hours']}")
    finally:
        _CONFIG()["trade_log_csv"] = old_path
        os.unlink(tmp_path)
        for suffix in ["_sess.json", "_sess.txt"]:
            p = tmp_path.replace(".csv", suffix)
            if os.path.exists(p):
                os.unlink(p)


def test_session_opt_result_includes_min_hours():
    """Result dict should include min_hours field."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        tmp_path = f.name

    try:
        rows = []
        # Use 50+ total trades to pass new statistical guards
        for i in range(50):
            rows.append({
                "timestamp": f"2026-06-01T{i % 24:02d}:{i:02d}:00+00:00",
                "outcome": "win",
                "pnl_r": 1.56,
                "confidence": 0.71,
                "side": "sell",
                "bar_index": i,
                "symbol": "XAUUSDm",
                "timeframe": "M15",
                "entry": 4483.0,
                "stop_loss": 4506.0,
                "take_profit": 4465.0,
                "rr": 1.56,
                "reason": "tp_hit",
            })

        make_trade_log(rows, tmp_path)

        cfg = _CONFIG()
        old_path = cfg["trade_log_csv"]
        cfg["trade_log_csv"] = tmp_path
        cfg["session_opt_json"] = tmp_path.replace(".csv", "_sess.json")
        cfg["session_opt_txt"] = tmp_path.replace(".csv", "_sess.txt")

        result = optimize_session_hours_from_trade_log()
        assert result is not None
        assert "min_hours" in result, "Result should include 'min_hours' field"
        assert result["min_hours"] == 4, f"Expected min_hours=4, got {result['min_hours']}"
        print(f"PASS: result includes min_hours={result['min_hours']}")
    finally:
        _CONFIG()["trade_log_csv"] = old_path
        os.unlink(tmp_path)
        for suffix in ["_sess.json", "_sess.txt"]:
            p = tmp_path.replace(".csv", suffix)
            if os.path.exists(p):
                os.unlink(p)


if __name__ == "__main__":
    test_session_opt_never_returns_empty()
    test_session_opt_mode_strict_when_enough_good_hours()
    test_session_opt_result_includes_min_hours()
    print("\nAll session optimization tests PASSED.")
