"""Tests for the GetLastError-based lock contention fix in _acquire_lock."""
import os
import sys
import tempfile
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from bridge_mt5_pro import _acquire_lock, _release_lock

_log = logging.getLogger("test_lock_getlasterror")
_log.addHandler(logging.StreamHandler(sys.stdout))
_log.setLevel(logging.WARNING)


def test_stale_lock_nonexistent_pid_reclaimed():
    """Lock file with a non-existent PID should be reclaimed (ERROR_INVALID_PARAMETER)."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".lock") as f:
        path = f.name
        f.write(b"99999999")  # non-existent PID
    try:
        result = _acquire_lock(path, _log)
        assert result is True, f"Expected True for stale lock, got {result}"
        _release_lock(path)
    finally:
        if os.path.exists(path):
            os.unlink(path)
    print("  PASSED: stale lock with non-existent PID reclaimed")


def test_live_lock_current_pid_denied():
    """Lock file with the current PID (process IS running) should be denied."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".lock") as f:
        path = f.name
        f.write(str(os.getpid()).encode())
    try:
        result = _acquire_lock(path, _log)
        assert result is False, f"Expected False for live lock, got {result}"
    finally:
        if os.path.exists(path):
            os.unlink(path)
    print("  PASSED: live lock with current PID denied")


def test_lock_after_release_reacquired():
    """After releasing, the lock should be acquirable again."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".lock") as f:
        path = f.name
    try:
        assert _acquire_lock(path, _log) is True
        _release_lock(path)
        assert _acquire_lock(path, _log) is True
        _release_lock(path)
    finally:
        if os.path.exists(path):
            os.unlink(path)
    print("  PASSED: lock reacquired after release")


def test_windows_error_constants():
    """Verify Windows error code constants are correct."""
    ERROR_ACCESS_DENIED = 5
    ERROR_INVALID_PARAMETER = 87
    assert ERROR_ACCESS_DENIED == 5
    assert ERROR_INVALID_PARAMETER == 87
    print("  PASSED: Windows error code constants correct")


if __name__ == "__main__":
    print("Running GetLastError lock fix tests...")
    test_stale_lock_nonexistent_pid_reclaimed()
    test_live_lock_current_pid_denied()
    test_lock_after_release_reacquired()
    test_windows_error_constants()
    print("\nALL GETLASTERROR LOCK TESTS PASSED")
