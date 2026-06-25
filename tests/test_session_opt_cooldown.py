"""
Validation test for session optimization cooldown guard:
Ensures optimize_session_hours_from_trade_log respects the cooldown interval
and returns None when called again within the cooldown window.
"""
import json
import os
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import ea.bridge_mt5_pro as _bridge
from ea.bridge_mt5_pro import optimize_session_hours_from_trade_log


def _CONFIG():
    return _bridge.CONFIG


def make_trade_log(rows, path):
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


def test_cooldown_blocks_re_execution():
    """Second call within cooldown window should return None immediately."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        tmp_path = f.name

    try:
        # Create 60 trades across 6 hours (enough to pass all guards)
        rows = []
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
        old_cooldown = cfg["session_opt_cooldown_sec"]
        tmp_json = tmp_path.replace(".csv", "_sess.json")
        tmp_txt = tmp_path.replace(".csv", "_sess.txt")
        cfg["trade_log_csv"] = tmp_path
        cfg["session_opt_json"] = tmp_json
        cfg["session_opt_txt"] = tmp_txt
        cfg["session_opt_cooldown_sec"] = 3600  # 1 hour

        try:
            # First call: should execute normally
            result1 = optimize_session_hours_from_trade_log(
                min_trades_per_hour=2, max_hours=12, min_hours=4, min_total_trades=5
            )
            assert result1 is not None, "First call should return a result"
            assert result1["selection_mode"] == "strict", f"Expected strict, got {result1['selection_mode']}"
            print(f"  First call: mode={result1['selection_mode']}, hours={result1['new_hours']}")

            # Second call (immediate): should be blocked by cooldown
            result2 = optimize_session_hours_from_trade_log(
                min_trades_per_hour=2, max_hours=12, min_hours=4, min_total_trades=5
            )
            assert result2 is None, (
                f"Second call within cooldown should return None, got {result2}"
            )
            print("  Second call returned None (cooldown active) — PASS")

        finally:
            cfg["trade_log_csv"] = old_path
            cfg["session_opt_cooldown_sec"] = old_cooldown
            for p in [tmp_path, tmp_json, tmp_txt]:
                if os.path.exists(p):
                    os.unlink(p)

    except Exception:
        # Cleanup on failure
        for p in [tmp_path, tmp_path.replace(".csv", "_sess.json"), tmp_path.replace(".csv", "_sess.txt")]:
            if os.path.exists(p):
                os.unlink(p)
        raise


def test_cooldown_disabled_with_zero():
    """Setting cooldown to 0 should disable the guard and always run."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        tmp_path = f.name

    try:
        rows = []
        for h in range(6):
            for i in range(10):
                rows.append({
                    "timestamp": f"2026-06-01T{h:02d}:{i:02d}:00+00:00",
                    "outcome": "win",
                    "pnl_r": 0.5,
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
        old_cooldown = cfg["session_opt_cooldown_sec"]
        tmp_json = tmp_path.replace(".csv", "_sess.json")
        tmp_txt = tmp_path.replace(".csv", "_sess.txt")
        cfg["trade_log_csv"] = tmp_path
        cfg["session_opt_json"] = tmp_json
        cfg["session_opt_txt"] = tmp_txt
        cfg["session_opt_cooldown_sec"] = 0  # disabled

        try:
            result1 = optimize_session_hours_from_trade_log(
                min_trades_per_hour=2, max_hours=12, min_hours=4, min_total_trades=5
            )
            assert result1 is not None, "First call should return a result"

            result2 = optimize_session_hours_from_trade_log(
                min_trades_per_hour=2, max_hours=12, min_hours=4, min_total_trades=5
            )
            assert result2 is not None, "With cooldown=0, second call should also execute"
            print("  cooldown=0: both calls executed — PASS")

        finally:
            cfg["trade_log_csv"] = old_path
            cfg["session_opt_cooldown_sec"] = old_cooldown
            for p in [tmp_path, tmp_json, tmp_txt]:
                if os.path.exists(p):
                    os.unlink(p)

    except Exception:
        for p in [tmp_path, tmp_path.replace(".csv", "_sess.json"), tmp_path.replace(".csv", "_sess.txt")]:
            if os.path.exists(p):
                os.unlink(p)
        raise


def test_cooldown_config_default():
    """CONFIG should have session_opt_cooldown_sec=3600 by default."""
    cfg = _CONFIG()
    assert "session_opt_cooldown_sec" in cfg, "CONFIG missing session_opt_cooldown_sec"
    assert cfg["session_opt_cooldown_sec"] == 3600, (
        f"Expected 3600, got {cfg['session_opt_cooldown_sec']}"
    )
    print(f"  CONFIG[session_opt_cooldown_sec]={cfg['session_opt_cooldown_sec']} — PASS")


if __name__ == "__main__":
    print("Test 1: cooldown config default")
    test_cooldown_config_default()

    print("\nTest 2: cooldown blocks re-execution within window")
    test_cooldown_blocks_re_execution()

    print("\nTest 3: cooldown disabled with zero")
    test_cooldown_disabled_with_zero()

    print("\n" + "=" * 50)
    print("ALL COOLDOWN GUARD TESTS PASSED")
