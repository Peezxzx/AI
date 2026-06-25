"""Quick validation script for atomic_write return value fix."""
import json
import os
import sys
import tempfile

# Add repo to path so we can import
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bridge_mt5_pro import atomic_write

passed = 0
failed = 0

# Test 1: Normal write returns True
with tempfile.NamedTemporaryFile(suffix='.json', delete=False, dir=tempfile.gettempdir()) as f:
    path = f.name
result = atomic_write(path, {'test': 'data', 'value': 42})
if result is True:
    print("PASS: Test 1 - Normal write returns True")
    passed += 1
else:
    print(f"FAIL: Test 1 - Normal write returned {result}, expected True")
    failed += 1
os.unlink(path)

# Test 2: Write and verify content
with tempfile.NamedTemporaryFile(suffix='.json', delete=False, dir=tempfile.gettempdir()) as f:
    path = f.name
atomic_write(path, {'signal': 'sell', 'confidence': 1.0})
with open(path, 'r') as f:
    data = json.load(f)
if data == {'signal': 'sell', 'confidence': 1.0}:
    print("PASS: Test 2 - Content round-trip correct")
    passed += 1
else:
    print(f"FAIL: Test 2 - Content mismatch: {data}")
    failed += 1
os.unlink(path)

# Test 3: Overwrite returns True
with tempfile.NamedTemporaryFile(suffix='.json', delete=False, dir=tempfile.gettempdir()) as f:
    path = f.name
atomic_write(path, {'v': 1})
result = atomic_write(path, {'v': 2})
if result is True:
    print("PASS: Test 3 - Overwrite returns True")
    passed += 1
else:
    print(f"FAIL: Test 3 - Overwrite returned {result}, expected True")
    failed += 1
os.unlink(path)

# Test 4: Nested directory creation
nested = os.path.join(tempfile.gettempdir(), 'atsawin_test', 'sub', 'signal.json')
result = atomic_write(nested, {'nested': True})
if result is True:
    print("PASS: Test 4 - Nested directory write returns True")
    passed += 1
else:
    print(f"FAIL: Test 4 - Nested write returned {result}, expected True")
    failed += 1
os.unlink(nested)
os.rmdir(os.path.dirname(nested))
os.rmdir(os.path.dirname(os.path.dirname(nested)))

print(f"\nResults: {passed} passed, {failed} failed")
sys.exit(0 if failed == 0 else 1)
