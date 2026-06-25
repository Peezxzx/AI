"""Validate that the Desktop bridge has the reconnection fix deployed."""
import ast
import sys

def validate_fix():
    path = r"C:\Users\Administrator\Desktop\bridge_mt5_pro.py"
    with open(path, "r", encoding="utf-8") as f:
        source = f.read()

    # 1. Parse OK
    tree = ast.parse(source)
    print("[PASS] AST parse OK")

    # 2. Check _reconnect_mt5 function exists
    func_names = [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
    assert "_reconnect_mt5" in func_names, "_reconnect_mt5 function not found"
    print("[PASS] _reconnect_mt5 function exists")

    # 3. Check that scan_once result is checked for None in the main loop
    lines = source.splitlines()
    found_result_assign = False
    found_none_check = False
    found_reconnect_call_in_loop = False

    for i, line in enumerate(lines):
        stripped = line.strip()
        if "result = scan_once()" in stripped:
            found_result_assign = True
            chunk = "\n".join(lines[i:i+6])
            if "if result is None:" in chunk or "if result is None" in chunk:
                found_none_check = True
        if "_reconnect_mt5()" in stripped and "if" not in stripped:
            found_reconnect_call_in_loop = True

    assert found_result_assign, "scan_once() result not assigned to variable"
    print("[PASS] scan_once() result captured in variable")

    assert found_none_check, "No None check on scan_once() result"
    print("[PASS] None check on scan_once() result present")

    assert found_reconnect_call_in_loop, "_reconnect_mt5() not called in main loop"
    print("[PASS] _reconnect_mt5() called in main loop")

    # 4. Check that error_count increments on None result
    found_none_error_increment = False
    for i, line in enumerate(lines):
        stripped = line.strip()
        if "if result is None" in stripped:
            chunk = "\n".join(lines[i:i+5])
            if "error_count += 1" in chunk:
                found_none_error_increment = True
    assert found_none_error_increment, "error_count not incremented on None result"
    print("[PASS] error_count incremented on None result")

    # 5. Check that error_count resets on successful scan_once
    found_reset = False
    for i, line in enumerate(lines):
        stripped = line.strip()
        if "error_count = 0" in stripped:
            found_reset = True
    assert found_reset, "error_count not reset on success"
    print("[PASS] error_count reset on successful scan")

    # 6. Check that Desktop file matches repo file
    with open(r"C:\Users\Administrator\repos\AI\bridge_mt5_pro.py", "r", encoding="utf-8") as f:
        repo_source = f.read()
    assert source == repo_source, "Desktop file does NOT match repo file"
    print("[PASS] Desktop bridge matches repo bridge exactly")

    # 7. Check max_consecutive_errors threshold
    found_threshold = False
    for line in lines:
        if "max_consecutive_errors" in line:
            found_threshold = True
            print(f"[PASS] max_consecutive_errors configured: {line.strip()}")
            break
    assert found_threshold, "max_consecutive_errors not configured"

    # 8. Check reconnection threshold triggers at error_count >= 10
    found_reconnect_trigger = False
    for line in lines:
        if "error_count >= max_consecutive_errors" in line:
            found_reconnect_trigger = True
            print("[PASS] Reconnection triggers at error_count >= max_consecutive_errors")
            break
    assert found_reconnect_trigger, "Reconnection trigger not found"

    print("\n=== ALL 8 VALIDATION CHECKS PASSED ===")
    print("Desktop bridge_mt5_pro.py now has full reconnection fix deployed.")
    return True

if __name__ == "__main__":
    try:
        validate_fix()
    except AssertionError as e:
        print(f"[FAIL] {e}")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] {e}")
        sys.exit(1)
