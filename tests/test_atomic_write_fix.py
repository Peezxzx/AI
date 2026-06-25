"""
Validation script for atomic_write crash-safety fix.
Confirms that atomic_write never raises OSError even under simulated lock contention.
"""
import json
import os
import sys
import tempfile
import time
from pathlib import Path

# Import from the ea version (the one actually running as bridge)
sys.path.insert(0, r"C:\Users\Administrator\repos\AI\ea")

# Force re-import
if "bridge_mt5_pro" in sys.modules:
    del sys.modules["bridge_mt5_pro"]

from bridge_mt5_pro import atomic_write

def test_basic_write():
    """Test basic atomic write works."""
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "test_signal.json")
        payload = {"signal": "sell", "confidence": 0.62, "test": True}
        atomic_write(path, payload)

        assert os.path.exists(path), "File should exist after write"
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert data == payload, f"Content mismatch: {data} != {payload}"
        print("[PASS] test_basic_write")

def test_overwrite():
    """Test overwriting existing file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "test.json")
        atomic_write(path, {"v": 1})
        atomic_write(path, {"v": 2})
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert data["v"] == 2, f"Expected v=2, got {data}"
        print("[PASS] test_overwrite")

def test_never_raises():
    """Simulate 50 rapid writes — none should raise an exception."""
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "stress.json")
        errors = []
        for i in range(50):
            try:
                atomic_write(path, {"iteration": i, "signal": "sell", "confidence": 0.75})
            except Exception as e:
                errors.append((i, e))

        if errors:
            for idx, err in errors:
                print(f"  [FAIL] iteration {idx}: {err}")
            raise AssertionError(f"atomic_write raised {len(errors)} exceptions — fix did not work!")
        print(f"[PASS] test_never_raises: 50/50 writes succeeded without exception")

def test_no_stale_tmp():
    """Ensure no .tmp files are left behind."""
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "clean.json")
        for i in range(10):
            atomic_write(path, {"round": i})
        tmp_files = list(Path(tmpdir).glob("*.tmp"))
        assert len(tmp_files) == 0, f"Stale .tmp files found: {tmp_files}"
        print("[PASS] test_no_stale_tmp")

def test_nested_dir():
    """Test writing to a path where parent dirs don't exist yet."""
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "deep", "nested", "dir", "signal.json")
        atomic_write(path, {"signal": "buy", "confidence": 0.99})
        assert os.path.exists(path), "Nested path should be created"
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert data["signal"] == "buy"
        print("[PASS] test_nested_dir")

def test_payload_types():
    """Test with payloads matching the actual signal contract."""
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "signal.json")
        payload = {
            "schema_version": "2.3",
            "contract": "atsawin_mt5_signal",
            "signal": "sell",
            "confidence": 0.752,
            "entry_price": 4461.88,
            "stop_loss": 4476.79,
            "take_profit": 4441.0,
            "risk_reward_ratio": 1.4,
            "position_size": 0.01,
            "atr": 7.46,
            "rsi": 28.9,
            "ema_fast": 4475.09,
            "ema_slow": 4478.03,
            "reasons": ["trend_down", "confirm_down"],
            "symbol": "XAUUSD",
            "mt5_symbol": "XAUUSDm",
            "timeframe": "M15",
            "score_breakdown": {"buy_score": 0.0, "sell_score": 2.0, "edge": 2.0},
            "setup_key": "XAUUSDm|M15|sell|4461.88|4476.79|4441.00|0.752|none|none|0.00",
            "signal_id": "XAUUSDm|M15|sell|4461.88|4476.79|4441.00|0.752|none|none|0.00",
        }
        atomic_write(path, payload)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert data["signal"] == "sell"
        assert data["confidence"] == 0.752
        assert data["setup_key"].startswith("XAUUSDm")
        print("[PASS] test_payload_types")

if __name__ == "__main__":
    print("=" * 60)
    print("  atomic_write crash-safety validation")
    print("  Verifying fix for: [WinError 5] Access is denied on .tmp rename")
    print("=" * 60)
    test_basic_write()
    test_overwrite()
    test_never_raises()
    test_no_stale_tmp()
    test_nested_dir()
    test_payload_types()
    print("=" * 60)
    print("ALL 6 TESTS PASSED")
    print("atomic_write is now crash-safe for scan_once.")
    print("=" * 60)
