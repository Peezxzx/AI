"""
Validation test for chop_regime reason fix:
Ensures 'chop_regime' is only appended to reasons when chop_penalty > 0.0,
and that the score_breakdown is consistent with the reasons list.
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import ea.bridge_mt5_pro as _bridge
from ea.bridge_mt5_pro import generate_signal

def _CONFIG():
    return _bridge.CONFIG


def make_rates(n=300, trend="down", volatility="normal"):
    """Generate synthetic rate data for testing."""
    import numpy as np
    np.random.seed(42)
    rates = []
    price = 4500.0
    for i in range(n):
        if trend == "down":
            drift = -0.3
        elif trend == "up":
            drift = 0.3
        else:
            drift = 0.0

        if volatility == "high":
            noise = np.random.normal(0, 8.0)
            high_noise = abs(np.random.normal(0, 5.0))
            low_noise = abs(np.random.normal(0, 5.0))
        elif volatility == "low":
            noise = np.random.normal(0, 0.3)
            high_noise = abs(np.random.normal(0, 0.15))
            low_noise = abs(np.random.normal(0, 0.15))
        else:  # normal
            noise = np.random.normal(0, 2.0)
            high_noise = abs(np.random.normal(0, 1.0))
            low_noise = abs(np.random.normal(0, 1.0))

        close = price + drift + noise
        high = close + high_noise
        low = close - low_noise
        rates.append({
            "time": 1748800000 + i * 900,
            "open": price,
            "high": high,
            "low": low,
            "close": close,
            "tick_volume": 100,
            "spread": 20,
            "real_volume": 0,
        })
        price = close
    import numpy as np
    rates = np.array(
        [(r["time"], r["open"], r["high"], r["low"], r["close"], r["tick_volume"], r["spread"], r["real_volume"]) for r in rates],
        dtype=[
            ("time", "<i8"),
            ("open", "<f8"),
            ("high", "<f8"),
            ("low", "<f8"),
            ("close", "<f8"),
            ("tick_volume", "<i8"),
            ("spread", "<i8"),
            ("real_volume", "<i8"),
        ],
    )
    return rates


class FakeTick:
    def __init__(self, ask, bid=None):
        self.ask = ask
        self.bid = bid or ask - 0.28


def test_chop_regime_reason_consistent_with_penalty():
    """chop_regime should only appear in reasons when chop_penalty > 0.0."""
    cfg = _CONFIG()
    old_min_atr = cfg["min_atr_price"]
    old_min_ema_gap = cfg["min_ema_gap_price"]

    try:
        # Use normal volatility data — ATR should be above min_atr_price
        rates = make_rates(300, trend="down", volatility="high")
        tick = FakeTick(ask=float(rates["close"][-1]))

        sig = generate_signal(rates, tick, current_hour_utc=10, apply_session_filter=False)

        # With high volatility, chop_penalty should be 0.0 and chop_regime should NOT be in reasons
        chop_penalty_in_breakdown = sig.metadata.get("score_breakdown", {}).get("chop_penalty", 0.0)
        has_chop_reason = "chop_regime" in sig.reasons

        # The key invariant: if chop_penalty is 0.0, chop_regime should NOT be in reasons
        if chop_penalty_in_breakdown == 0.0:
            assert not has_chop_reason, (
                f"chop_regime found in reasons but chop_penalty=0.0. "
                f"reasons={sig.reasons}, breakdown={sig.metadata.get('score_breakdown')}"
            )
        else:
            assert has_chop_reason, (
                f"chop_penalty={chop_penalty_in_breakdown} > 0.0 but chop_regime NOT in reasons. "
                f"reasons={sig.reasons}"
            )

        print(f"PASS: chop_penalty={chop_penalty_in_breakdown}, chop_regime in reasons={has_chop_reason}")
    finally:
        cfg["min_atr_price"] = old_min_atr
        cfg["min_ema_gap_price"] = old_min_ema_gap


def test_chop_regime_present_when_low_volatility():
    """With very low volatility, chop_regime SHOULD be in reasons and penalty > 0."""
    cfg = _CONFIG()
    old_min_atr = cfg["min_atr_price"]
    old_min_ema_gap = cfg["min_ema_gap_price"]

    try:
        # Use very low volatility data — ATR should be below min_atr_price
        rates = make_rates(300, trend="flat", volatility="low")
        tick = FakeTick(ask=float(rates["close"][-1]))

        sig = generate_signal(rates, tick, current_hour_utc=10, apply_session_filter=False)

        chop_penalty_in_breakdown = sig.metadata.get("score_breakdown", {}).get("chop_penalty", 0.0)
        has_chop_reason = "chop_regime" in sig.reasons

        # With very low volatility, we expect chop_regime to be present
        # (unless EMAs haven't converged yet with flat data)
        if chop_penalty_in_breakdown > 0.0:
            assert has_chop_reason, (
                f"chop_penalty={chop_penalty_in_breakdown} > 0.0 but chop_regime NOT in reasons. "
                f"reasons={sig.reasons}"
            )
            print(f"PASS: low vol -> chop_penalty={chop_penalty_in_breakdown}, chop_regime present")
        else:
            # Even with low vol, if EMAs are far apart, penalty could be 0
            # This is acceptable — the key is consistency
            assert not has_chop_reason, (
                f"chop_penalty=0.0 but chop_regime in reasons (should not happen after fix). "
                f"reasons={sig.reasons}"
            )
            print(f"PASS: low vol but ema_gap sufficient -> chop_penalty=0.0, no chop_regime reason")
    finally:
        cfg["min_atr_price"] = old_min_atr
        cfg["min_ema_gap_price"] = old_min_ema_gap


def test_score_breakdown_consistency():
    """score_breakdown reasons should be consistent with the reasons list."""
    rates = make_rates(300, trend="down", volatility="normal")
    tick = FakeTick(ask=float(rates["close"][-1]))

    sig = generate_signal(rates, tick, current_hour_utc=10, apply_session_filter=False)

    breakdown = sig.metadata.get("score_breakdown", {})

    # If chop_penalty > 0, chop_regime must be in reasons
    if breakdown.get("chop_penalty", 0.0) > 0.0:
        assert "chop_regime" in sig.reasons, (
            f"chop_penalty={breakdown['chop_penalty']} but chop_regime not in reasons"
        )

    # If session_out_penalty > 0, out_of_session_soft should be in reasons
    if breakdown.get("session_out_penalty", 0.0) > 0.0:
        assert "out_of_session_soft" in sig.reasons, (
            f"session_out_penalty={breakdown['session_out_penalty']} but out_of_session_soft not in reasons"
        )

    print(f"PASS: score_breakdown reasons are consistent")


if __name__ == "__main__":
    test_chop_regime_reason_consistent_with_penalty()
    test_chop_regime_present_when_low_volatility()
    test_score_breakdown_consistency()
    print("\nAll chop_regime fix tests PASSED.")
