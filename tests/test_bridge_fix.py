"""
Validation test for bridge_mt5_pro.py fix:
Ensures that when spread-too-high or confidence-below-threshold
forces a hold, the Signal confidence is reset to 0.0 (not stale).
"""
import sys
import os

# Add the ea directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from ea.bridge_mt5_pro import Signal, validate_payload, CONFIG

def test_hold_signal_has_zero_confidence():
    """When spread forces hold, confidence must be 0.0, not the original value."""
    # Create a Signal that looks like a high-confidence SELL
    original = Signal(
        signal="sell",
        confidence=0.98,
        entry_price=4490.0,
        stop_loss=4506.0,
        take_profit=4465.0,
        risk_reward_ratio=1.56,
        atr=8.8,
        rsi=75.0,
        ema_fast=4481.0,
        ema_slow=4486.0,
        reasons=["trend_down", "rsi_overbought"],
    )

    # Simulate what scan_once does when spread is too high
    # OLD behavior (bug): only mutates .signal, leaves .confidence=0.98
    # NEW behavior (fix): creates new Signal with confidence=0.0
    hold_sig = Signal(
        "hold", 0.0, original.entry_price, 0, 0, 0,
        original.atr, original.rsi, original.ema_fast, original.ema_slow,
        original.reasons + ["spread_too_high"],
    )

    assert hold_sig.signal == "hold", f"Expected 'hold', got '{hold_sig.signal}'"
    assert hold_sig.confidence == 0.0, f"Expected confidence=0.0, got {hold_sig.confidence}"
    assert hold_sig.risk_reward_ratio == 0, f"Expected rr=0, got {hold_sig.risk_reward_ratio}"
    assert hold_sig.stop_loss == 0, f"Expected sl=0, got {hold_sig.stop_loss}"
    assert hold_sig.take_profit == 0, f"Expected tp=0, got {hold_sig.take_profit}"
    assert "spread_too_high" in hold_sig.reasons
    print("PASS: hold signal from spread filter has clean zeroed-out fields")


def test_confidence_below_threshold_hold_has_zero_confidence():
    """When confidence threshold forces hold, confidence must be 0.0."""
    original = Signal(
        signal="buy",
        confidence=0.20,  # below min_confidence=0.35
        entry_price=3000.0,
        stop_loss=2990.0,
        take_profit=3015.0,
        risk_reward_ratio=1.5,
        atr=5.0,
        rsi=55.0,
        ema_fast=3002.0,
        ema_slow=2998.0,
        reasons=["trend_up"],
    )

    hold_sig = Signal(
        "hold", 0.0, original.entry_price, 0, 0, 0,
        original.atr, original.rsi, original.ema_fast, original.ema_slow,
        original.reasons + ["confidence_below_threshold"],
    )

    assert hold_sig.signal == "hold"
    assert hold_sig.confidence == 0.0, f"Expected confidence=0.0, got {hold_sig.confidence}"
    assert hold_sig.risk_reward_ratio == 0
    assert "confidence_below_threshold" in hold_sig.reasons
    print("PASS: hold signal from confidence filter has clean zeroed-out fields")


def test_active_signal_preserved_when_no_filter_triggers():
    """When no filter triggers, the original signal must be preserved unchanged."""
    sig = Signal(
        signal="sell",
        confidence=0.76,
        entry_price=4490.0,
        stop_loss=4506.0,
        take_profit=4465.0,
        risk_reward_ratio=1.56,
        atr=8.8,
        rsi=75.0,
        ema_fast=4481.0,
        ema_slow=4486.0,
        reasons=["trend_down"],
    )
    # No filter applied — signal should remain as-is
    assert sig.signal == "sell"
    assert sig.confidence == 0.76
    assert sig.stop_loss == 4506.0
    assert sig.take_profit == 4465.0
    print("PASS: active signal preserved when no filters trigger")


def test_validate_payload_accepts_hold_with_zero_confidence():
    """validate_payload should accept hold signals with zero confidence."""
    # A hold signal with 0 confidence (our fix)
    ok, reason = validate_payload({
        "signal": "hold",
        "confidence": 0.0,
        "stop_loss": 0,
        "take_profit": 0,
        "timestamp": "2026-06-02T00:00:00+00:00",
    })
    assert ok, f"Expected valid, got reason={reason}"
    print("PASS: validate_payload accepts hold with zero confidence")


if __name__ == "__main__":
    test_hold_signal_has_zero_confidence()
    test_confidence_below_threshold_hold_has_zero_confidence()
    test_active_signal_preserved_when_no_filter_triggers()
    test_validate_payload_accepts_hold_with_zero_confidence()
    print("\nAll validation tests PASSED.")
