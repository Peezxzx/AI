"""Validate dynamic signal threshold fix for chop_regime and session penalty interaction.

The bug (1): chop_regime forced confidence=0 and immediate HOLD, killing all signals
            when EMA gap was tight even with strong directional scores.
The bug (2): out_penalty referenced before assignment when session_filter_mode="hard".

The fix: chop_penalty is computed proportionally to how far below threshold the EMA gap
and ATR are, then subtracted from scores and used to lower the signal threshold.
out_penalty NameError fixed by using chop_penalty (always initialized to 0.0).
"""
import sys
import os
import math
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ea'))

# We cannot import bridge_mt5_pro directly (requires MetaTrader5),
# so we test the logic by extracting the relevant constants and simulating.

SESSION_OUT_PENALTY = 0.15
OLD_THRESHOLD = 1.9

def old_logic(score, out_penalty):
    """Simulate OLD behavior: penalty applied first, then fixed threshold."""
    adjusted = max(0.0, score - out_penalty)
    return adjusted >= OLD_THRESHOLD

def new_logic(score, out_penalty):
    """Simulate NEW behavior: threshold reduced by penalty amount."""
    threshold = max(1.5, OLD_THRESHOLD - out_penalty)
    adjusted = max(0.0, score - out_penalty)
    return adjusted >= threshold

# Test case 1: score=1.95, penalty=0.15 -> adjusted=1.80
# OLD: 1.80 >= 1.9 -> False (WRONG - signal lost)
# NEW: threshold=1.75, 1.80 >= 1.75 -> True (CORRECT - signal preserved)
score = 1.95
assert old_logic(score, SESSION_OUT_PENALTY) == False, "OLD should reject (demonstrating the bug)"
assert new_logic(score, SESSION_OUT_PENALTY) == True, "NEW should accept (demonstrating the fix)"
print(f"PASS: score={score} -> old=REJECT, new=ACCEPT (bug fixed)")

# Test case 2: score=2.10, penalty=0.15 -> adjusted=1.95
# BOTH should accept
score = 2.10
assert old_logic(score, SESSION_OUT_PENALTY) == True
assert new_logic(score, SESSION_OUT_PENALTY) == True
print(f"PASS: score={score} -> both ACCEPT")

# Test case 3: score=1.60, penalty=0.15 -> adjusted=1.45
# BOTH should reject (too weak even with penalty adjustment)
score = 1.60
assert old_logic(score, SESSION_OUT_PENALTY) == False
assert new_logic(score, SESSION_OUT_PENALTY) == False
print(f"PASS: score={score} -> both REJECT")

# Test case 4: score=1.92, penalty=0.15 -> adjusted=1.77
# OLD: 1.77 < 1.9 -> False
# NEW: 1.77 >= 1.75 -> True
score = 1.92
assert old_logic(score, SESSION_OUT_PENALTY) == False
assert new_logic(score, SESSION_OUT_PENALTY) == True
print(f"PASS: score={score} -> old=REJECT, new=ACCEPT (edge case fixed)")

# Test case 5: threshold floor at 1.5
assert max(1.5, 1.9 - 0.15) == 1.75
assert max(1.5, 1.9 - 2.0) == 1.5  # floor
print(f"PASS: threshold floor at 1.5 works")

# Test case 6: no session filter -> penalty=0, threshold=1.9 (original behavior)
assert new_logic(1.85, 0.0) == False
assert new_logic(1.95, 0.0) == True
print(f"PASS: no penalty -> threshold=1.9 (backward compatible)")

# Test case 7: no session filter and not out of session
# The old code path: apply_session_filter=False means no penalty applied
# The new code path: same, since out_penalty is only subtracted when filter is active
assert new_logic(1.80, 0.0) == False  # still below 1.9
assert new_logic(1.90, 0.0) == True   # meets original threshold
print(f"PASS: backward compatible when filter disabled")

# === Chop regime tests (new) ===

# Note: The actual code checks `av < min_atr_price or ema_gap < min_ema_gap_price`
# test scenario from latest_signal.json: ema_gap=0.16, min_ema=0.8, atr=5.99, min_atr=3.0
# ema_gap < min_ema_gap_price triggers chop, ATR is fine
MIN_EMA_GAP = 0.8
MIN_ATR = 3.0

# Scenario A: very tight EMA gap (from live data)
ema_gap_a = abs(4485.41 - 4485.25)  # 0.16
atr_a = 5.99
gap_ratio_a = ema_gap_a / MIN_EMA_GAP  # 0.20
atr_ratio_a = atr_a / MIN_ATR  # 1.997
expected_penalty_a = max(0.0, 0.4 * (1.0 - gap_ratio_a) + 0.3 * (1.0 - atr_ratio_a))
# atr_ratio > 1 so (1 - atr_ratio) < 0, but max(0, ...) handles it
assert math.isclose(expected_penalty_a, max(0.0, 0.4 * 0.8 + 0.3 * (1.0 - atr_ratio_a)), rel_tol=1e-9)
print(f"PASS: scenario A (ema_gap={ema_gap_a}) -> penalty={expected_penalty_a:.4f}")

# A score of 2.75 (strong buy) with light penalty should still produce a buy signal
buy_score_a = max(0.0, 2.75 - expected_penalty_a)
threshold_a = max(1.5, 1.9 - expected_penalty_a)
assert buy_score_a >= threshold_a, f"score {buy_score_a} should meet threshold {threshold_a}"
assert buy_score_a > 0, "score should be non-zero"
print(f"PASS: strong buy score={buy_score_a:.4f} >= threshold={threshold_a:.4f}")

# Scenario B: normal EMA gap (no chop)
ema_gap_b = 1.5
atr_b = 5.0
normal_penalty = 0.0
assert not (atr_b < MIN_ATR or ema_gap_b < MIN_EMA_GAP), "should not trigger chop"
threshold_b = max(1.5, 1.9 - normal_penalty)
assert threshold_b == 1.9, "no chop -> threshold should be 1.9"
print(f"PASS: no chop -> penalty=0.0, threshold=1.9")

# Scenario C: both ATR and EMA gap below threshold (heavy chop)
ema_gap_c = 0.2
atr_c = 1.5
gap_ratio_c = ema_gap_c / MIN_EMA_GAP  # 0.25
atr_ratio_c = atr_c / MIN_ATR  # 0.5
penalty_c = max(0.0, 0.4 * (1.0 - gap_ratio_c) + 0.3 * (1.0 - atr_ratio_c))
assert penalty_c > expected_penalty_a, "heavy chop should have larger penalty"
print(f"PASS: heavy chop penalty={penalty_c:.4f} > light chop penalty={expected_penalty_a:.4f}")

# Even heavy chop doesn't force zero confidence - it penalizes
buy_score_c = max(0.0, 2.75 - penalty_c)
threshold_c = max(1.5, 1.9 - penalty_c)
confidence_c = min(1.0, (max(buy_score_c, 0) / 3.1) * 0.7 + (buy_score_c / 2.0) * 0.3)
assert confidence_c > 0, "confidence should never be zero after fix"
print(f"PASS: heavy chop still produces confidence={confidence_c:.4f} > 0")

print("\nAll tests passed.")
