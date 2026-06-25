"""
Regression test for mt5.symbol_info() returning None in scan_once.
Verifies the code structure has the None guard.
"""
import re
import os
import sys


def test_scan_once_has_symbol_info_none_guard():
    """scan_once() must guard against mt5.symbol_info() returning None."""
    bridge_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'bridge_mt5_pro.py')
    with open(bridge_path, 'r') as f:
        source = f.read()

    # Find the scan_once function body
    # Check that before accessing .point, there's a None check
    assert 'mt5.symbol_info(symbol)' in source, "symbol_info call should exist"

    # The pattern: sym_info = mt5.symbol_info(symbol) followed by if sym_info is None
    pattern = r'sym_info\s*=\s*mt5\.symbol_info\(symbol\).*?if\s+sym_info\s+is\s+None'
    match = re.search(pattern, source, re.DOTALL)
    assert match, "Missing None guard on mt5.symbol_info() result before accessing .point"
    print("  PASS: symbol_info None guard present in scan_once")


def test_point_access_uses_sym_info_variable():
    """After the fix, point should be accessed via sym_info.point, not mt5.symbol_info(symbol).point"""
    bridge_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'bridge_mt5_pro.py')
    with open(bridge_path, 'r') as f:
        source = f.read()

    # Should NOT have the old inline pattern: mt5.symbol_info(symbol).point
    bad_pattern = r'mt5\.symbol_info\(symbol\)\.point'
    assert not re.search(bad_pattern, source), "Old pattern 'mt5.symbol_info(symbol).point' still exists — should use sym_info variable"

    # Should have the new pattern
    assert re.search(r'sym_info\.point', source), "Should access .point via sym_info variable"
    print("  PASS: point accessed via sym_info variable")


def test_syntax_ok():
    """Verify bridge_mt5_pro.py compiles without errors."""
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
    print("Regression Test: symbol_info() None Guard")
    print("=" * 60)
    print()

    tests = [
        ("Test 1: symbol_info None guard present", test_scan_once_has_symbol_info_none_guard),
        ("Test 2: point access uses sym_info var", test_point_access_uses_sym_info_variable),
        ("Test 3: syntax check", test_syntax_ok),
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
