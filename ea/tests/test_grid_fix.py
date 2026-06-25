"""
Validation test: autotune + walkforward grids include proven-best params from autotune run.
Proven best (from bridge_mt5_autotune_result.json): ema_fast=30, atr_sl_mult=2.0
Both autotune_parameters() and find_best_params_on_rates() must include these in their grids.
"""
import sys
import os
import re

def _extract_grid(bridge_source, func_name):
    """Extract the grid dict that appears right after a function definition."""
    pattern = rf'def {func_name}\([^)]*\):.*?\n    grid = \{{([^}}]+)\}}'
    m = re.search(pattern, bridge_source, re.DOTALL)
    assert m, f"Could not find grid in {func_name}"
    grid_body = m.group(1)
    grid = {}
    for line in grid_body.strip().split('\n'):
        line = line.strip().rstrip(',')
        if ':' in line:
            key, val = line.split(':', 1)
            key = key.strip().strip('"').strip("'")
            val = val.strip()
            # Evaluate list literal
            grid[key] = eval(val)
    return grid

def test_autotune_grid_includes_proven_best():
    bridge_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'bridge_mt5_pro.py')
    with open(bridge_path, 'r') as f:
        source = f.read()

    grid = _extract_grid(source, 'autotune_parameters')
    print(f"  autotune grid: {grid}")

    assert 30 in grid["ema_fast"], f"ema_fast grid missing 30 (proven best). Got: {grid['ema_fast']}"
    assert 2.0 in grid["atr_sl_mult"], f"atr_sl_mult grid missing 2.0 (proven best). Got: {grid['atr_sl_mult']}"
    assert 40 in grid["ema_slow"], f"ema_slow grid missing 40 (proven best). Got: {grid['ema_slow']}"
    assert 2.8 in grid["atr_tp_mult"], f"atr_tp_mult grid missing 2.8 (proven best). Got: {grid['atr_tp_mult']}"
    print("  PASS: autotune grid includes all proven-best params")

def test_walkforward_grid_includes_proven_best():
    bridge_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'bridge_mt5_pro.py')
    with open(bridge_path, 'r') as f:
        source = f.read()

    grid = _extract_grid(source, 'find_best_params_on_rates')
    print(f"  walkforward grid: {grid}")

    assert 30 in grid["ema_fast"], f"ema_fast grid missing 30 (proven best). Got: {grid['ema_fast']}"
    assert 2.0 in grid["atr_sl_mult"], f"atr_sl_mult grid missing 2.0 (proven best). Got: {grid['atr_sl_mult']}"
    print("  PASS: walkforward grid includes all proven-best params")

def test_grid_values_are_superset():
    """New grids must be a superset of old grids (backward compat)."""
    bridge_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'bridge_mt5_pro.py')
    with open(bridge_path, 'r') as f:
        source = f.read()

    at_grid = _extract_grid(source, 'autotune_parameters')
    wf_grid = _extract_grid(source, 'find_best_params_on_rates')

    old_ef = {12, 20}
    old_slm = {1.6, 1.8}
    assert old_ef.issubset(set(at_grid["ema_fast"])), "autotune ema_fast not superset of old"
    assert old_slm.issubset(set(at_grid["atr_sl_mult"])), "autotune atr_sl_mult not superset of old"
    assert old_ef.issubset(set(wf_grid["ema_fast"])), "walkforward ema_fast not superset of old"
    assert old_slm.issubset(set(wf_grid["atr_tp_mult"]) | set(wf_grid["atr_sl_mult"])), "walkforward atr_sl_mult not superset of old"
    print("  PASS: New grids are supersets of old grids (backward compatible)")

def test_syntax_ok():
    import py_compile
    bridge_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'bridge_mt5_pro.py')
    try:
        py_compile.compile(bridge_path, doraise=True)
        print("  PASS: SYNTAX OK")
    except py_compile.PyCompileError as e:
        print(f"  FAIL: Syntax error: {e}")
        raise


if __name__ == '__main__':
    print("=" * 60)
    print("Validation: Autotune/Walkforward Grid Fix")
    print("=" * 60)
    print()

    tests = [
        ("Test 1: autotune grid includes ema_fast=30, atr_sl_mult=2.0", test_autotune_grid_includes_proven_best),
        ("Test 2: walkforward grid includes ema_fast=30, atr_sl_mult=2.0", test_walkforward_grid_includes_proven_best),
        ("Test 3: grid backward compatibility", test_grid_values_are_superset),
        ("Test 4: syntax check", test_syntax_ok),
    ]

    passed = 0
    for name, fn in tests:
        print(name)
        try:
            fn()
            passed += 1
        except Exception as e:
            print(f"  FAIL: {e}")
        print()

    print("=" * 60)
    print(f"RESULTS: {passed}/{len(tests)} tests passed")
    if passed == len(tests):
        print("ALL TESTS PASSED")
    else:
        print("SOME TESTS FAILED")
        sys.exit(1)
    print("=" * 60)
