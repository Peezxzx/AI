"""One-shot validation for the position_size check in validate_payload."""
import sys
sys.path.insert(0, "ea")
from bridge_mt5_pro import validate_payload

tests = [
    ("valid buy with pos_size=0.05",
     {'signal': 'buy', 'confidence': 0.8, 'stop_loss': 4518.0, 'take_profit': 4549.0,
      'timestamp': '2026-06-02T09:54:51', 'entry_price': 4530.0, 'position_size': 0.05},
     True, "ok"),
    ("buy zero position_size",
     {'signal': 'buy', 'confidence': 0.8, 'stop_loss': 4518.0, 'take_profit': 4549.0,
      'timestamp': '2026-06-02T09:54:51', 'entry_price': 4530.0, 'position_size': 0.0},
     False, "invalid_position_size"),
    ("sell negative position_size",
     {'signal': 'sell', 'confidence': 0.8, 'stop_loss': 4549.0, 'take_profit': 4518.0,
      'timestamp': '2026-06-02T09:54:51', 'entry_price': 4530.0, 'position_size': -0.01},
     False, "invalid_position_size"),
    ("buy missing position_size",
     {'signal': 'buy', 'confidence': 0.8, 'stop_loss': 4518.0, 'take_profit': 4549.0,
      'timestamp': '2026-06-02T09:54:51', 'entry_price': 4530.0},
     False, "invalid_position_size"),
    ("hold signal (no pos_size check)",
     {'signal': 'hold', 'confidence': 0.0, 'stop_loss': 0, 'take_profit': 0,
      'timestamp': '2026-06-02T09:54:51'},
     True, "ok"),
]

passed = 0
failed = 0
for name, payload, expected_ok, expected_reason in tests:
    ok, reason = validate_payload(payload)
    if ok == expected_ok and (expected_reason == "ok" or expected_reason in reason):
        print(f"  PASS: {name} -> ok={ok}, reason={reason}")
        passed += 1
    else:
        print(f"  FAIL: {name} -> ok={ok}, reason={reason} (expected ok={expected_ok}, reason={expected_reason})")
        failed += 1

print(f"\nResults: {passed} passed, {failed} failed")
if failed:
    sys.exit(1)
print("ALL VALIDATION PASSED")
