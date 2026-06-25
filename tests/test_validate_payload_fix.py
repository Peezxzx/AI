"""Validate the validate_payload fix for entry_price geometry checks."""
import sys
sys.path.insert(0, 'ea')
from bridge_mt5_pro import validate_payload

tests = [
    # (name, payload, expected_ok, expected_reason_substr)
    ("valid buy", {'signal': 'buy', 'confidence': 0.8, 'stop_loss': 4518.0, 'take_profit': 4549.0, 'timestamp': '2026-06-02T09:54:51', 'entry_price': 4530.0, 'position_size': 0.05}, True, "ok"),
    ("valid sell", {'signal': 'sell', 'confidence': 0.8, 'stop_loss': 4549.0, 'take_profit': 4518.0, 'timestamp': '2026-06-02T09:54:51', 'entry_price': 4530.0, 'position_size': 0.05}, True, "ok"),
    ("buy entry below SL", {'signal': 'buy', 'confidence': 0.8, 'stop_loss': 4540.0, 'take_profit': 4550.0, 'timestamp': '2026-06-02T09:54:51', 'entry_price': 4530.0, 'position_size': 0.05}, False, "invalid_buy_entry_position"),
    ("buy entry above TP", {'signal': 'buy', 'confidence': 0.8, 'stop_loss': 4510.0, 'take_profit': 4520.0, 'timestamp': '2026-06-02T09:54:51', 'entry_price': 4530.0, 'position_size': 0.05}, False, "invalid_buy_entry_position"),
    ("sell entry above SL", {'signal': 'sell', 'confidence': 0.8, 'stop_loss': 4540.0, 'take_profit': 4510.0, 'timestamp': '2026-06-02T09:54:51', 'entry_price': 4550.0, 'position_size': 0.05}, False, "invalid_sell_entry_position"),
    ("sell entry below TP", {'signal': 'sell', 'confidence': 0.8, 'stop_loss': 4550.0, 'take_profit': 4530.0, 'timestamp': '2026-06-02T09:54:51', 'entry_price': 4510.0, 'position_size': 0.05}, False, "invalid_sell_entry_position"),
    ("hold", {'signal': 'hold', 'confidence': 0.0, 'stop_loss': 0, 'take_profit': 0, 'timestamp': '2026-06-02T09:54:51', 'entry_price': 0}, True, "ok"),
    ("missing field", {'signal': 'buy', 'confidence': 0.8}, False, "missing_stop_loss"),
    ("live signal", {'schema_version': '2.0', 'signal': 'buy', 'confidence': 1.0, 'entry_price': 4530.63, 'stop_loss': 4518.72, 'take_profit': 4549.16, 'timestamp': '2026-06-02T09:54:51.436600+00:00', 'position_size': 0.05}, True, "ok"),
    ("buy sl>=tp", {'signal': 'buy', 'confidence': 0.8, 'stop_loss': 4550.0, 'take_profit': 4540.0, 'timestamp': '2026-06-02T09:54:51', 'entry_price': 4530.0, 'position_size': 0.05}, False, "invalid_buy_geometry"),
    ("sell sl<=tp", {'signal': 'sell', 'confidence': 0.8, 'stop_loss': 4510.0, 'take_profit': 4520.0, 'timestamp': '2026-06-02T09:54:51', 'entry_price': 4530.0, 'position_size': 0.05}, False, "invalid_sell_geometry"),
    ("buy entry=0 skip check", {'signal': 'buy', 'confidence': 0.8, 'stop_loss': 4540.0, 'take_profit': 4550.0, 'timestamp': '2026-06-02T09:54:51', 'entry_price': 0, 'position_size': 0.05}, True, "ok"),
    ("buy entry=0 sl>=tp caught", {'signal': 'buy', 'confidence': 0.8, 'stop_loss': 4550.0, 'take_profit': 4540.0, 'timestamp': '2026-06-02T09:54:51', 'entry_price': 0, 'position_size': 0.05}, False, "invalid_buy_geometry"),
    ("buy zero position_size", {'signal': 'buy', 'confidence': 0.8, 'stop_loss': 4518.0, 'take_profit': 4549.0, 'timestamp': '2026-06-02T09:54:51', 'entry_price': 4530.0, 'position_size': 0.0}, False, "invalid_position_size"),
    ("sell negative position_size", {'signal': 'sell', 'confidence': 0.8, 'stop_loss': 4549.0, 'take_profit': 4518.0, 'timestamp': '2026-06-02T09:54:51', 'entry_price': 4530.0, 'position_size': -0.01}, False, "invalid_position_size"),
    ("buy missing position_size", {'signal': 'buy', 'confidence': 0.8, 'stop_loss': 4518.0, 'take_profit': 4549.0, 'timestamp': '2026-06-02T09:54:51', 'entry_price': 4530.0}, False, "invalid_position_size"),
]

passed = 0
failed = 0
for name, payload, expected_ok, expected_reason in tests:
    ok, reason = validate_payload(payload)
    if ok == expected_ok and (expected_reason == "ok" or expected_reason in reason):
        print(f"  PASS: {name} -> ok={ok}, reason={reason}")
        passed += 1
    else:
        print(f"  FAIL: {name} -> ok={ok}, reason={reason} (expected ok={expected_ok}, reason contains={expected_reason})")
        failed += 1

print(f"\nResults: {passed} passed, {failed} failed")
if failed:
    sys.exit(1)
print("ALL TESTS PASSED")
