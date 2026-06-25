"""Unit tests for bridge_mt5_pro file-lock mechanism."""
import os
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from bridge_mt5_pro import _acquire_lock, _release_lock

import logging

_log = logging.getLogger("test_lock")
_log.addHandler(logging.StreamHandler(sys.stdout))
_log.setLevel(logging.WARNING)


def test_lock_acquire_and_release():
    """First acquire succeeds, release clears lock."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".lock") as f:
        path = f.name
    try:
        assert _acquire_lock(path, _log) is True
        assert os.path.exists(path)
        _release_lock(path)
        assert not os.path.exists(path)
    finally:
        if os.path.exists(path):
            os.unlink(path)


def test_lock_reacquire_after_release():
    """After release, another acquire succeeds."""
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


def test_stale_lock_reclaimed():
    """Lock file with non-running PID is reclaimed."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".lock") as f:
        path = f.name
        f.write(b"99999999")  # non-existent PID
    try:
        assert _acquire_lock(path, _log) is True
        _release_lock(path)
    finally:
        if os.path.exists(path):
            os.unlink(path)


def test_lock_file_contains_pid():
    """Lock file contains the current process PID."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".lock") as f:
        path = f.name
    try:
        assert _acquire_lock(path, _log) is True
        pid_str = open(path).read().strip()
        assert pid_str == str(os.getpid())
        _release_lock(path)
    finally:
        if os.path.exists(path):
            os.unlink(path)


def test_lock_with_none_log():
    """_acquire_lock works with None logger (child process fallback)."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".lock") as f:
        path = f.name
    try:
        assert _acquire_lock(path, None) is True
        assert os.path.exists(path)
        _release_lock(path)
    finally:
        if os.path.exists(path):
            os.unlink(path)


if __name__ == "__main__":
    test_lock_acquire_and_release()
    test_lock_reacquire_after_release()
    test_stale_lock_reclaimed()
    test_lock_file_contains_pid()
    test_lock_with_none_log()
    print("ALL LOCK TESTS PASSED")
