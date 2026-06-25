"""Test helper: verify lock blocks another process."""
import subprocess
import sys
import time
import os

lock_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_lock_test")
os.makedirs(lock_dir, exist_ok=True)
path = os.path.abspath(os.path.join(lock_dir, "test.lock"))
print(f"Lock path: {path}")

if os.path.exists(path):
    os.unlink(path)

child = subprocess.Popen(
    [sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "_child_lock.py"), path],
    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
)
time.sleep(3)

out = child.stdout.read().decode()
print(f"child alive: {child.poll() is None}")
print(f"child stdout: {out!r}")

# List ALL files in the directory
print(f"\nDir listing of {lock_dir}:")
if os.path.isdir(lock_dir):
    for f in os.listdir(lock_dir):
        full = os.path.join(lock_dir, f)
        print(f"  {f} ({os.path.getsize(full)} bytes)")
else:
    print("  directory does not exist")

# Also check cwd
print(f"\nParent cwd: {os.getcwd()}")

child.terminate()
child.wait(timeout=5)
if os.path.exists(path):
    os.unlink(path)
if os.path.isdir(lock_dir):
    os.rmdir(lock_dir)
print("DONE")
