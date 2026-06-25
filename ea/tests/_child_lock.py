"""Helper: child process that acquires a lock and holds it."""
import sys
import os
import time

sys.path.insert(0, r"C:\Users\Administrator\repos\AI\ea")
from bridge_mt5_pro import _acquire_lock, _release_lock

lock_path = os.path.abspath(sys.argv[1])
print(f"child: lock_path={lock_path!r}", flush=True)

acquired = _acquire_lock(lock_path, None)
exists_after = os.path.exists(lock_path)
content = ""
if exists_after:
    content = open(lock_path).read()
print(f"child: pid={os.getpid()} acquired={acquired} exists={exists_after} content={content!r}", flush=True)
print(f"child: cwd={os.getcwd()!r}", flush=True)
if acquired:
    time.sleep(30)
    _release_lock(lock_path)
