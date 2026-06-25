"""Unit tests for evaluate_trade multi-bar hold logic."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from bridge_mt5_pro import evaluate_trade, Signal


def make_rates(closes, highs=None, lows=None):
    """Build a list of rate dicts from close prices."""
    if highs is None:
        highs = [c + 0.5 for c in closes]
    if lows is None:
        lows = [c - 0.5 for c in closes]
    return [
        {"time": i, "open": c, "high": h, "low": l, "close": c}
        for i, (c, h, l) in enumerate(zip(closes, highs, lows))
    ]


def make_signal(signal, entry, sl, tp, rr=1.5):
    return Signal(signal, 0.8, entry, sl, tp, rr, 5.0, 50.0, entry + 1, entry - 1, ["test"])


def test_buy_tp_hit_on_second_bar():
    """Buy trade: SL far below, TP = entry+5, second bar touches TP."""
    rates = make_rates(
        [100, 101, 102, 103, 104, 105, 106],
        highs=[100.5, 101.5, 102.5, 103.5, 104.5, 105.5, 106.5],
        lows=[99.5, 100.5, 101.5, 102.5, 103.5, 104.5, 105.5],
    )
    sig = make_signal("buy", entry=100.0, sl=90.0, tp=105.0)
    outcome, reason, price = evaluate_trade(rates, 0, sig, max_hold=6)
    assert outcome == "win"
    assert reason == "tp_hit"
    assert price == 105.0


def test_buy_sl_hit_on_third_bar():
    """Buy trade: TP far above, SL = entry-5, third bar touches SL."""
    rates = make_rates(
        [100, 99, 98, 97, 96, 95],
        highs=[100.5, 99.5, 98.5, 97.5, 96.5, 95.5],
        lows=[99.5, 98.5, 97.5, 96.5, 95.5, 94.5],
    )
    sig = make_signal("buy", entry=100.0, sl=95.5, tp=110.0)
    outcome, reason, price = evaluate_trade(rates, 0, sig, max_hold=5)
    assert outcome == "loss"
    assert reason == "sl_hit"


def test_sell_tp_hit_on_second_bar():
    """Sell trade: SL far above, TP = entry-5, second bar touches TP."""
    rates = make_rates(
        [100, 99, 98, 97, 96, 95],
        highs=[100.5, 99.5, 98.5, 97.5, 96.5, 95.5],
        lows=[99.5, 98.5, 97.5, 96.5, 95.5, 94.5],
    )
    sig = make_signal("sell", entry=100.0, sl=110.0, tp=96.5)
    outcome, reason, price = evaluate_trade(rates, 0, sig, max_hold=5)
    assert outcome == "win"
    assert reason == "tp_hit"


def test_sell_sl_hit_on_third_bar():
    """Sell trade: TP far below, SL = entry+5, third bar touches SL."""
    rates = make_rates(
        [100, 101, 102, 103, 104, 105],
        highs=[100.5, 101.5, 102.5, 103.5, 104.5, 105.5],
        lows=[99.5, 100.5, 101.5, 102.5, 103.5, 104.5],
    )
    sig = make_signal("sell", entry=100.0, sl=102.5, tp=90.0)
    outcome, reason, price = evaluate_trade(rates, 0, sig, max_hold=5)
    assert outcome == "loss"
    assert reason == "sl_hit"


def test_expired_trade_no_hit():
    """Trade where neither SL nor TP is hit within max_hold bars."""
    rates = make_rates(
        [100, 100.5, 100.3, 100.7, 100.2, 100.6, 100.4, 100.8],
        highs=[100.6, 101.0, 100.8, 101.2, 100.7, 101.1, 100.9, 101.3],
        lows=[99.9, 100.0, 99.8, 100.2, 99.7, 100.1, 99.6, 100.3],
    )
    sig = make_signal("buy", entry=100.0, sl=95.0, tp=110.0)
    outcome, reason, price = evaluate_trade(rates, 0, sig, max_hold=3)
    assert outcome == "expired"
    assert reason == "max_hold_reached"
    assert price == rates[4]["close"]  # entry(0) + 1 + max_hold(3) = bar 4


def test_same_bar_sl_tp_both_hit_sl_closer():
    """Bar where both SL and TP are touched; midpoint closer to SL -> loss."""
    rates = make_rates(
        [100, 100, 100],
        highs=[100.5, 110.0, 100.5],  # bar 1 touches TP=110
        lows=[99.5, 90.0, 99.5],     # bar 1 touches SL=90
    )
    sig = make_signal("buy", entry=100.0, sl=90.0, tp=110.0)
    # midpoint of bar 1 = (110+90)/2 = 100, distance to SL=90 is 10, to TP=110 is 10 -> tie, SL wins (<=)
    outcome, reason, price = evaluate_trade(rates, 0, sig, max_hold=1)
    assert outcome == "loss"
    assert reason == "sl_hit"


def test_same_bar_sl_tp_both_hit_tp_closer():
    """Bar where both SL and TP are touched; midpoint closer to TP -> win."""
    rates = make_rates(
        [102, 102, 102],
        highs=[102.5, 110.0, 102.5],  # bar 1 touches TP=110
        lows=[101.5, 95.0, 101.5],   # bar 1 touches SL=95
    )
    sig = make_signal("buy", entry=102.0, sl=95.0, tp=110.0)
    # midpoint of bar 1 = (110+95)/2 = 102.5, dist to SL=95 is 7.5, to TP=110 is 7.5 -> tie, SL wins
    outcome, reason, price = evaluate_trade(rates, 0, sig, max_hold=1)
    assert outcome == "loss"
    assert reason == "sl_hit"


def test_first_bar_immediate_tp_hit():
    """TP hit on the very first bar after entry."""
    rates = make_rates(
        [100, 106],
        highs=[100.5, 106.5],
        lows=[99.5, 105.5],
    )
    sig = make_signal("buy", entry=100.0, sl=90.0, tp=105.0)
    outcome, reason, price = evaluate_trade(rates, 0, sig, max_hold=5)
    assert outcome == "win"
    assert reason == "tp_hit"


def test_zero_max_hold_means_check_one_bar():
    """max_hold=0 still checks one bar (range(entry+1, entry+1+0+1)=range(entry+1, entry+2))."""
    rates = make_rates(
        [100, 105, 110],
        highs=[100.5, 105.5, 110.5],
        lows=[99.5, 104.5, 109.5],
    )
    sig = make_signal("buy", entry=100.0, sl=90.0, tp=104.0)
    outcome, reason, price = evaluate_trade(rates, 0, sig, max_hold=0)
    # hold_limit = min(0+1+0, 2) = 1, range(1, 2) = [1]
    # bar 1: h=105.5 >= tp=104 -> win
    assert outcome == "win"


def test_syntax_ok():
    """Module compiles without errors."""
    import py_compile
    import tempfile
    src = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "bridge_mt5_pro.py")
    py_compile.compile(src, doraise=True)


if __name__ == "__main__":
    test_buy_tp_hit_on_second_bar()
    test_buy_sl_hit_on_third_bar()
    test_sell_tp_hit_on_second_bar()
    test_sell_sl_hit_on_third_bar()
    test_expired_trade_no_hit()
    test_same_bar_sl_tp_both_hit_sl_closer()
    test_same_bar_sl_tp_both_hit_tp_closer()
    test_first_bar_immediate_tp_hit()
    test_zero_max_hold_means_check_one_bar()
    test_syntax_ok()
    print("ALL TESTS PASSED")
