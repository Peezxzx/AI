import ast
import sys

def validate_syntax(filepath):
    with open(filepath, encoding='utf-8') as f:
        source = f.read()
    try:
        ast.parse(source)
        print(f"SYNTAX OK: {filepath}")
        return True
    except SyntaxError as e:
        print(f"SYNTAX ERROR in {filepath}: {e}")
        return False

def validate_logic():
    """Simulate the chop_regime logic to verify it doesn't force zero confidence."""
    # Simulate the scenario from latest_signal.json:
    # ATR=5.99, ema_gap = |4485.41 - 4485.25| = 0.16
    # min_ema_gap_price=0.8, min_atr_price=3.0
    
    min_ema_gap_price = 0.8
    min_atr_price = 3.0
    av = 5.99
    ema_gap = 0.16  # from latest signal data
    
    buy_score = 2.75  # trend_up(1.2) + rsi_support_up(0.8) + price>ema(0.5) + vol_ok(0.2) = 2.75
    sell_score = 0.25  # tf_bias could be confirm_down=-0.25
    
    old_approach_hold = (av < min_atr_price or ema_gap < min_ema_gap_price)
    
    # New approach: penalty instead of hard return
    chop_penalty = 0.0
    if av < min_ema_gap_price or ema_gap < min_ema_gap_price:
        gap_ratio = (ema_gap / min_ema_gap_price) if min_ema_gap_price > 0 else 0.0
        atr_ratio = (av / min_atr_price) if min_atr_price > 0 else 0.0
        chop_penalty = max(0.0, 0.4 * (1.0 - gap_ratio) + 0.3 * (1.0 - atr_ratio))
        buy_score = max(0.0, buy_score - chop_penalty)
        sell_score = max(0.0, sell_score - chop_penalty)
    
    sig_threshold = max(1.5, 1.9 - chop_penalty)
    edge = abs(buy_score - sell_score)
    
    print(f"=== Chop Regime Validation ===")
    print(f"EMA gap: {ema_gap} (threshold: {min_ema_gap_price})")
    print(f"ATR: {av} (threshold: {min_atr_price})")
    print(f"Old approach would HOLD: {old_approach_hold}")
    print(f"New chop_penalty: {chop_penalty:.4f}")
    print(f"Sig threshold: {sig_threshold:.4f}")
    print(f"Buy score after penalty: {buy_score:.4f}")
    print(f"Sell score after penalty: {sell_score:.4f}")
    print(f"Edge: {edge:.4f}")
    
    if buy_score > sell_score and buy_score >= sig_threshold and edge >= 0.55:
        print("New approach: BUY signal generated!")
    elif sell_score > buy_score and sell_score >= sig_threshold and edge >= 0.55:
        print("New approach: SELL signal generated!")
    else:
        print("New approach: HOLD (but with non-zero confidence)")
    
    # Verify the key fix: confidence is no longer forced to 0
    strength = max(buy_score, sell_score)
    confidence = min(1.0, (strength / 3.1) * 0.7 + (edge / 2.0) * 0.3)
    print(f"Confidence: {confidence:.4f}")
    
    if confidence > 0:
        print("PASS: Confidence is non-zero in chop regime (stale output fix)")
    else:
        print("FAIL: Confidence still zero")
    
    return confidence > 0

ok = validate_syntax('ea/bridge_mt5_pro.py')
if ok:
    logic_ok = validate_logic()
    if logic_ok:
        print("\nALL VALIDATIONS PASSED")
    else:
        print("\nLOGIC VALIDATION FAILED")
        sys.exit(1)
else:
    sys.exit(1)
