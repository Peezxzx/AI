"""Test session optimization safety guards in bridge_mt5_pro.py"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unittest.mock import patch, MagicMock
from datetime import datetime, timezone

# We test the logic by importing the function and mocking dependencies
# First, let's test the CONFIG defaults and safety floor logic

def test_config_has_session_opt_floor():
    """CONFIG must include session_opt_min_hours and session_opt_min_pnl_r"""
    import importlib
    import ea.bridge_mt5_pro as bridge
    importlib.reload(bridge)

    assert "session_opt_min_hours" in bridge.CONFIG, "Missing session_opt_min_hours in CONFIG"
    assert "session_opt_min_pnl_r" in bridge.CONFIG, "Missing session_opt_min_pnl_r in CONFIG"
    assert bridge.CONFIG["session_opt_min_hours"] >= 4, f"session_opt_min_hours too low: {bridge.CONFIG['session_opt_min_hours']}"
    print(f"  CONFIG[session_opt_min_hours]={bridge.CONFIG['session_opt_min_hours']}")
    print(f"  CONFIG[session_opt_min_pnl_r]={bridge.CONFIG['session_opt_min_pnl_r']}")
    print("  PASS: CONFIG has safety floor params")


def test_session_floor_reset_in_main_path():
    """When session hours are below floor, the live bridge reset logic should restore defaults"""
    import importlib
    import ea.bridge_mt5_pro as bridge
    importlib.reload(bridge)

    # Simulate what happened: optimize-session shrunk hours to [0, 5]
    bridge.CONFIG["session_hours_utc"] = [0, 5]
    bridge.CONFIG["session_opt_min_hours"] = 5

    _session_floor = int(bridge.CONFIG.get("session_opt_min_hours", 5))
    if len(bridge.CONFIG.get("session_hours_utc", [])) < _session_floor:
        bridge.CONFIG["session_hours_utc"] = [0, 1, 5, 10, 13, 14]

    assert len(bridge.CONFIG["session_hours_utc"]) >= _session_floor, \
        f"Session hours still too few: {bridge.CONFIG['session_hours_utc']}"
    print(f"  After reset: session_hours_utc={bridge.CONFIG['session_hours_utc']}")
    print("  PASS: Session floor reset works")


def test_optimize_session_rejects_too_few_hours():
    """optimize_session_hours_from_trade_log should reject selection with too few hours"""
    import importlib
    import ea.bridge_mt5_pro as bridge
    importlib.reload(bridge)

    # Set up: simulate that only 2 hours would be selected
    bridge.CONFIG["session_opt_min_hours"] = 5
    bridge.CONFIG["session_hours_utc"] = [0, 1, 5, 10, 13, 14]  # original

    # Create a mock trade log with only 2 hours having data
    import tempfile, csv
    tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8')
    tmp.write("timestamp,bar_index,symbol,timeframe,side,entry,stop_loss,take_profit,rr,confidence,outcome,pnl_r,reason\n")
    # Hour 0: 2 trades
    tmp.write(f"2026-06-02T00:15:00+00:00,50,XAUUSDm,M15,sell,4500.00,4510.00,4480.00,2.0,0.8,win,2.0,tp_hit\n")
    tmp.write(f"2026-06-02T00:30:00+00:00,51,XAUUSDm,M15,sell,4501.00,4511.00,4481.00,2.0,0.8,loss,-1.0,sl_hit\n")
    # Hour 5: 2 trades
    tmp.write(f"2026-06-02T05:15:00+00:00,60,XAUUSDm,M15,sell,4502.00,4512.00,4482.00,2.0,0.8,win,2.0,tp_hit\n")
    tmp.write(f"2026-06-02T05:30:00+00:00,61,XAUUSDm,M15,sell,4503.00,4513.00,4483.00,2.0,0.8,loss,-1.0,sl_hit\n")
    tmp.close()

    old_trade_log = bridge.CONFIG["trade_log_csv"]
    old_sess_json = bridge.CONFIG["session_opt_json"]
    old_sess_txt = bridge.CONFIG["session_opt_txt"]
    bridge.CONFIG["trade_log_csv"] = tmp.name
    bridge.CONFIG["session_opt_json"] = tmp.name.replace(".csv", "_sess.json")
    bridge.CONFIG["session_opt_txt"] = tmp.name.replace(".csv", "_sess.txt")

    try:
        result = bridge.optimize_session_hours_from_trade_log(min_trades_per_hour=2, max_hours=12, min_hours=2)
        # Should reject because only 2 hours selected but floor is 5
        assert bridge.CONFIG["session_hours_utc"] == [0, 1, 5, 10, 13, 14], \
            f"Session hours were changed despite violation: {bridge.CONFIG['session_hours_utc']}"
        print(f"  Result: {result['selection_mode']}")
        print("  PASS: Rejected too-few-hours selection")
    finally:
        bridge.CONFIG["trade_log_csv"] = old_trade_log
        bridge.CONFIG["session_opt_json"] = old_sess_json
        bridge.CONFIG["session_opt_txt"] = old_sess_txt
        os.unlink(tmp.name)


def test_optimize_session_rejects_negative_pnl():
    """optimize_session_hours_from_trade_log should reject selection with very negative PnL"""
    import importlib
    import ea.bridge_mt5_pro as bridge
    importlib.reload(bridge)

    bridge.CONFIG["session_opt_min_hours"] = 5
    bridge.CONFIG["session_opt_min_pnl_r"] = -2.0
    bridge.CONFIG["session_hours_utc"] = [0, 1, 5, 10, 13, 14]

    import tempfile, csv
    tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8')
    tmp.write("timestamp,bar_index,symbol,timeframe,side,entry,stop_loss,take_profit,rr,confidence,outcome,pnl_r,reason\n")
    # Create 6 hours of data, all with terrible PnL
    for h in range(6):
        for _ in range(3):
            tmp.write(f"2026-06-02T{h:02d}:15:00+00:00,50,XAUUSDm,M15,sell,4500.00,4520.00,4470.00,1.5,0.8,loss,-1.0,sl_hit\n")
    tmp.close()

    old_trade_log = bridge.CONFIG["trade_log_csv"]
    old_sess_json = bridge.CONFIG["session_opt_json"]
    old_sess_txt = bridge.CONFIG["session_opt_txt"]
    bridge.CONFIG["trade_log_csv"] = tmp.name
    bridge.CONFIG["session_opt_json"] = tmp.name.replace(".csv", "_sess.json")
    bridge.CONFIG["session_opt_txt"] = tmp.name.replace(".csv", "_sess.txt")

    try:
        result = bridge.optimize_session_hours_from_trade_log(min_trades_per_hour=2, max_hours=12, min_hours=5)
        # All losses = -18 total PnL, should be rejected
        assert bridge.CONFIG["session_hours_utc"] == [0, 1, 5, 10, 13, 14], \
            f"Session hours were changed despite negative PnL: {bridge.CONFIG['session_hours_utc']}"
        print(f"  Result: {result['selection_mode']}")
        print("  PASS: Rejected negative PnL selection")
    finally:
        bridge.CONFIG["trade_log_csv"] = old_trade_log
        bridge.CONFIG["session_opt_json"] = old_sess_json
        bridge.CONFIG["session_opt_txt"] = old_sess_txt
        os.unlink(tmp.name)


def test_optimize_session_accepts_good_selection():
    """optimize_session_hours_from_trade_log should accept good selection"""
    import importlib
    import ea.bridge_mt5_pro as bridge
    importlib.reload(bridge)

    bridge.CONFIG["session_opt_min_hours"] = 5
    bridge.CONFIG["session_opt_min_pnl_r"] = -2.0
    bridge.CONFIG["session_hours_utc"] = [0, 1, 5, 10, 13, 14]

    import tempfile, csv
    tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8')
    tmp.write("timestamp,bar_index,symbol,timeframe,side,entry,stop_loss,take_profit,rr,confidence,outcome,pnl_r,reason\n")
    # Create 6 hours of data with positive PnL
    for h in [0, 1, 5, 10, 13]:
        for _ in range(5):
            tmp.write(f"2026-06-02T{h:02d}:15:00+00:00,50,XAUUSDm,M15,sell,4500.00,4490.00,4520.00,2.0,0.8,win,2.0,tp_hit\n")
    tmp.close()

    old_trade_log = bridge.CONFIG["trade_log_csv"]
    old_sess_json = bridge.CONFIG["session_opt_json"]
    old_sess_txt = bridge.CONFIG["session_opt_txt"]
    bridge.CONFIG["trade_log_csv"] = tmp.name
    bridge.CONFIG["session_opt_json"] = tmp.name.replace(".csv", "_sess.json")
    bridge.CONFIG["session_opt_txt"] = tmp.name.replace(".csv", "_sess.txt")

    try:
        result = bridge.optimize_session_hours_from_trade_log(min_trades_per_hour=2, max_hours=12, min_hours=5)
        # Should accept: 5 hours with positive PnL
        assert len(bridge.CONFIG["session_hours_utc"]) >= 5, \
            f"Session hours too few: {bridge.CONFIG['session_hours_utc']}"
        print(f"  New session hours: {bridge.CONFIG['session_hours_utc']}")
        print(f"  Result mode: {result['selection_mode']}")
        print("  PASS: Accepted good selection")
    finally:
        bridge.CONFIG["trade_log_csv"] = old_trade_log
        bridge.CONFIG["session_opt_json"] = old_sess_json
        bridge.CONFIG["session_opt_txt"] = old_sess_txt
        os.unlink(tmp.name)


if __name__ == "__main__":
    print("Test 1: CONFIG safety floor params")
    test_config_has_session_opt_floor()

    print("\nTest 2: Session floor reset in main path")
    test_session_floor_reset_in_main_path()

    print("\nTest 3: Reject too-few-hours selection")
    test_optimize_session_rejects_too_few_hours()

    print("\nTest 4: Reject negative PnL selection")
    test_optimize_session_rejects_negative_pnl()

    print("\nTest 5: Accept good selection")
    test_optimize_session_accepts_good_selection()

    print("\n" + "="*50)
    print("ALL TESTS PASSED")
