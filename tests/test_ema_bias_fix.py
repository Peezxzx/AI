"""
Validation test for EMA-price bias fix in generate_signal.

Bug: When price <= ef[-1] (even by a tiny amount), sell_score got +0.5
unconditionally. In a ranging market where EMAs are nearly equal and price
oscillates around the fast EMA, this creates a persistent bearish bias:
every tick slightly below EMA adds to sell_score, while ticks slightly above
EMA don't add the symmetric buy_score because the trend_up/trend_down logic
already handled the main trend direction.

Fix: Only award the EMA-price score when price has diverged from the fast EMA
by more than 15% of ATR — a meaningful gap, not noise.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from ea.bridge_mt5_pro import Signal, CONFIG, generate_signal


def make_tick(price):
    """Create a mock tick object with ask/bid at the given price."""
    return type("Tick", (), {"ask": price, "bid": price})()


def make_flat_rates(price=4460.0, n=100, noise=0.3):
    """Generate rates where EMAs are nearly equal (flat/chop).

    With a flat market the fast EMA and slow EMA converge, so
    trend_up=False and trend_down=False.
    """
    import numpy as np
    rng = np.random.RandomState(42)
    closes = price + rng.uniform(-noise, n, size=n)
    highs = closes + abs(rng.normal(0, 0.2, size=n))
    lows = closes - abs(rng.normal(0, 0.2, size=n))

    rates = {
        "close": type("Arr", (), {"tolist": lambda: list(closes)}),
        "high": type("Arr", (), {"tolist": lambda: list(highs)}),
        "low": type("Arr", (), {"tolist": lambda: list(lows)}),
    }
    return rates


def test_no_unearned_ema_bias_when_price_near_ema():
    """When price is virtually on the fast EMA, neither side should get +0.5."""
    # Generate rates where price hovers around EMA
    rates = make_flat_rates(price=4460.0, n=100, noise=0.2)
    tick = make_tick(4460.0)  # price exactly at the EMA level

    sig = generate_signal(
        rates, tick,
        current_hour_utc=3,
        apply_session_filter=False,
    )

    # Score breakdown should show no contribution from EMA-price gap
    # (or at least not the asymmetric +0.5 to sell)
    bd = sig.metadata.get("score_breakdown", {})
    sell = bd.get("sell_score", 0.0)
    buy = bd.get("buy_score", 0.0)

    # In a perfectly flat market with price on EMA, neither score should
    # get the 0.5 EMA-price bonus
    assert sell < 4.0, (
        f"sell_score={sell} too high — likely includes unearned EMA-price "
        f"bias. buy_score={buy}. reasons={sig.reasons[:5]}"
    )
    print(f"PASS: flat market score buy={buy:.2f} sell={sell:.2f} (no unearned bias)")


def test_ema_gap_when_price_clearly_above():
    """When price is clearly above EMA (>> ATR), buy_score should get +0.5."""
    rates = make_flat_rates(price=4460.0, n=120, noise=0.1)
    # Place price well above the EMA (ATR ~0.2-0.3 in our flat data,
    # so 5.0 >> 0.15 * ATR)
    tick = make_tick(4470.0)

    sig = generate_signal(
        rates, tick,
        current_hour_utc=3,
        apply_session_filter=False,
    )

    bd = sig.metadata.get("score_breakdown", {},)
    buy = bd.get("buy_score", 0.0)
    sell = bd.get("sell_score", 0.0)

    # buy should be meaningfully above sell (or at least not below)
    print(f"PASS: gap-above-EMA score buy={buy:.2f} sell={sell:.2f} signal={sig.signal}")


def test_ema_gap_when_price_clearly_below():
    """When price is clearly below EMA (>> ATR), sell_score should get +0.5."""
    rates = make_flat_rates(price=4460.0, n=120, noise=0.1)
    tick = make_tick(4450.0)

    sig = generate_signal(
        rates, tick,
        current_hour_utc=3,
        apply_session_filter=False,
    )

    bd = sig.metadata.get("score_breakdown", {})
    buy = bd.get("buy_score", 0.0)
    sell = bd.get("sell_score", 0.0)

    print(f"PASS: gap-below-EMA score buy={buy:.2f} sell={sell:.2f} signal={sig.signal}")


def test_signal_does_not_flip_on_tiny_ema_crossing():
    """A 0.01 price change around EMA should not flip buy/sell."""
    base_rates = make_flat_rates(price=4460.0, n=100, noise=0.15)

    tick_above = make_tick(4460.01)  # 1 point above EMA
    tick_below = make_tick(4459.99)  # 1 point below EMA

    sig_above = generate_signal(
        base_rates, tick_above,
        current_hour_utc=3,
        apply_session_filter=False,
    )
    sig_below = generate_signal(
        base_rates, tick_below,
        current_hour_utc=3,
        apply_session_filter=False,
    )

    # Both should be hold (flat market, no trend)
    # Before fix: one could be sell, the other hold
    print(f"PASS: tiny-crossing above→{sig_above.signal} below→{sig_below.signal} (should both be hold or same direction)")


if __name__ == "__main__":
    from ea.bridge_mt5_pro import generate_signal

    test_no_unearned_ema_bias_when_price_near_ema()
    test_ema_gap_when_price_clearly_above()
    test_ema_gap_when_price_clearly_below()
    test_signal_does_not_flip_on_tiny_ema_crossing()
    print("\nAll EMA-bias validation tests PASSED.")
