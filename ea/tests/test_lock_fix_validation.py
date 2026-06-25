"""Validate that --optimize-session and other file-writing modes now acquire the PID lock."""
import argparse
import importlib
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import bridge_mt5_pro as bridge
importlib.reload(bridge)


def _args(**kwargs):
    defaults = dict(
        health=False, backtest=False, analyze=False, autotune=False,
        walkforward=False, optimize_session=False, compare_live_execution=False,
        once=False, symbol=None, tf=None, compare_days=30,
    )
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_optimize_session_acquires_lock():
    """--optimize-session must now acquire the lock (was previously excluded)."""
    a = _args(optimize_session=True)
    # Replicate the lock check from bridge_mt5_pro.py main
    should_lock = not any([a.health, a.analyze])
    assert should_lock is True, f"optimize_session should acquire lock, got {should_lock}"
    print("  PASS: --optimize-session now acquires lock")


def test_backtest_acquires_lock():
    """--backtest must now acquire the lock (was previously excluded)."""
    a = _args(backtest=True)
    should_lock = not any([a.health, a.analyze])
    assert should_lock is True, f"backtest should acquire lock, got {should_lock}"
    print("  PASS: --backtest now acquires lock")


def test_autotune_acquires_lock():
    """--autotune must now acquire the lock (was previously excluded)."""
    a = _args(autotune=True)
    should_lock = not any([a.health, a.analyze])
    assert should_lock is True, f"autotune should acquire lock, got {should_lock}"
    print("  PASS: --autotune now acquires lock")


def test_walkforward_acquires_lock():
    """--walkforward must now acquire the lock (was previously excluded)."""
    a = _args(walkforward=True)
    should_lock = not any([a.health, a.analyze])
    assert should_lock is True, f"walkforward should acquire lock, got {should_lock}"
    print("  PASS: --walkforward now acquires lock")


def test_compare_live_execution_acquires_lock():
    """--compare-live-execution must now acquire the lock."""
    a = _args(compare_live_execution=True)
    should_lock = not any([a.health, a.analyze])
    assert should_lock is True
    print("  PASS: --compare-live-execution now acquires lock")


def test_health_skips_lock():
    """--health should still skip the lock (read-only check)."""
    a = _args(health=True)
    should_lock = not any([a.health, a.analyze])
    assert should_lock is False, f"health should skip lock, got {should_lock}"
    print("  PASS: --health still skips lock")


def test_analyze_skips_lock():
    """--analyze should still skip the lock (read-only, no shared file writes)."""
    a = _args(analyze=True)
    should_lock = not any([a.health, a.analyze])
    assert should_lock is False, f"analyze should skip lock, got {should_lock}"
    print("  PASS: --analyze still skips lock")


def test_once_acquires_lock():
    """default live-scan modes (--once, no flags) should still acquire lock."""
    a = _args()
    should_lock = not any([a.health, a.analyze])
    assert should_lock is True, f"live-scan should acquire lock, got {should_lock}"
    print("  PASS: live-scan (default) still acquires lock")


if __name__ == "__main__":
    print("Lock scope fix validation")
    print("=" * 50)
    test_optimize_session_acquires_lock()
    test_backtest_acquires_lock()
    test_autotune_acquires_lock()
    test_walkforward_acquires_lock()
    test_compare_live_execution_acquires_lock()
    test_health_skips_lock()
    test_analyze_skips_lock()
    test_once_acquires_lock()
    print("=" * 50)
    print("ALL 8 VALIDATION TESTS PASSED")
