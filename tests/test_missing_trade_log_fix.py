"""
Validation for the missing trade-log fix:
When the trade log CSV does not exist, optimize_session_hours_from_trade_log()
should return a proper result dict (not None) with selection_mode='skipped_no_trade_log',
write the result JSON, and NOT log an ERROR.
"""
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import ea.bridge_mt5_pro as _bridge
from ea.bridge_mt5_pro import optimize_session_hours_from_trade_log


def test_missing_trade_log_returns_result():
    """Missing trade log should return a result dict, not None."""
    cfg = _bridge.CONFIG
    old_path = cfg["trade_log_csv"]
    # Point to a non-existent file
    fake_path = r"C:\Users\Administrator\Desktop\_nonexistent_trade_log_12345.csv"
    cfg["trade_log_csv"] = fake_path
    tmp_json = os.path.join(tempfile.gettempdir(), "_test_sess_missing.json")
    cfg["session_opt_json"] = tmp_json

    try:
        result = optimize_session_hours_from_trade_log()
        assert result is not None, "Expected result dict, got None"
        assert result["selection_mode"] == "skipped_no_trade_log", (
            f"Expected 'skipped_no_trade_log', got '{result['selection_mode']}'"
        )
        assert result["new_hours"] == result["old_hours"], (
            "new_hours should equal old_hours when skipped"
        )
        assert "trade_log_not_found" in result["rejection_reason"], (
            f"rejection_reason should mention file not found: {result['rejection_reason']}"
        )
        # Result JSON should have been written
        assert os.path.exists(tmp_json), f"Result JSON not written to {tmp_json}"
        with open(tmp_json, "r") as f:
            written = json.load(f)
        assert written["selection_mode"] == "skipped_no_trade_log"
        print(f"PASS: missing trade log returns result with mode={result['selection_mode']}")
    finally:
        cfg["trade_log_csv"] = old_path
        if os.path.exists(tmp_json):
            os.unlink(tmp_json)


def test_missing_trade_log_preserves_session_hours():
    """Missing trade log should never mutate session_hours_utc."""
    cfg = _bridge.CONFIG
    old_path = cfg["trade_log_csv"]
    old_hours = list(cfg["session_hours_utc"])
    fake_path = r"C:\Users\Administrator\Desktop\_nonexistent_trade_log_67890.csv"
    cfg["trade_log_csv"] = fake_path
    tmp_json = os.path.join(tempfile.gettempdir(), "_test_sess_preserve.json")
    cfg["session_opt_json"] = tmp_json

    try:
        result = optimize_session_hours_from_trade_log()
        assert cfg["session_hours_utc"] == old_hours, (
            f"session_hours_utc was mutated: {old_hours} -> {cfg['session_hours_utc']}"
        )
        print(f"PASS: session_hours_utc preserved as {cfg['session_hours_utc']}")
    finally:
        cfg["trade_log_csv"] = old_path
        cfg["session_hours_utc"] = old_hours
        if os.path.exists(tmp_json):
            os.unlink(tmp_json)


if __name__ == "__main__":
    test_missing_trade_log_returns_result()
    test_missing_trade_log_preserves_session_hours()
    print("\nAll missing-trade-log fix tests PASSED.")
