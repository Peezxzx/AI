"""
Validation: ea_status.json payload in scan_now() includes
fib_nearest_ratio, fib_nearest_level, fib_distance, rsi_divergence.
"""
import ast, inspect, sys

def check_status_payload_fields():
    """Parse bridge_mt5_pro.py AST and verify the status dict literal
    in scan_once() contains the 4 missing metadata fields."""
    with open(r'C:\Users\Administrator\repos\AI\bridge_mt5_pro.py', 'r', encoding='utf-8') as f:
        source = f.read()

    tree = ast.parse(source)

    # Find scan_once function
    scan_once_fn = None
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == 'scan_once':
            scan_once_fn = node
            break

    assert scan_once_fn is not None, "scan_once() not found"

    # Find the status dict (second atomic_write call)
    status_dict = None
    for node in ast.walk(scan_once_fn):
        if isinstance(node, ast.Call):
            # Look for atomic_write(status_path, { ... })
            if isinstance(node.func, ast.Name) and node.func.id == 'atomic_write':
                if len(node.args) >= 2:
                    second_arg = node.args[1]
                    if isinstance(second_arg, ast.Dict):
                        # Check if this is the status dict (has 'last_scan' key)
                        keys = [k.value for k in second_arg.keys if isinstance(k, ast.Constant)]
                        if 'last_scan' in keys:
                            status_dict = second_arg
                            break

    assert status_dict is not None, "status dict not found in scan_once()"

    # Extract all keys from the status dict
    status_keys = set()
    for k in status_dict.keys:
        if isinstance(k, ast.Constant):
            status_keys.add(k.value)

    required_new = {'fib_nearest_ratio', 'fib_nearest_level', 'fib_distance', 'rsi_divergence'}
    missing = required_new - status_keys
    assert not missing, f"Missing fields in ea_status payload: {missing}"

    print(f"OK: ea_status payload contains all 4 metadata fields: {sorted(required_new)}")
    print(f"Total status keys: {len(status_keys)}")
    return True


def check_py_compile():
    """Verify both bridge files compile cleanly."""
    import py_compile
    files = [
        r'C:\Users\Administrator\repos\AI\bridge_mt5_pro.py',
        r'C:\Users\Administrator\repos\AI\ea\bridge_mt5_pro.py',
    ]
    for f in files:
        try:
            py_compile.compile(f, doraise=True)
            print(f"OK: py_compile {f}")
        except py_compile.PyCompileError as e:
            assert False, f"py_compile failed for {f}: {e}"
    return True


def check_files_identical():
    """Verify repo and ea copies are still in sync."""
    import hashlib
    files = [
        r'C:\Users\Administrator\repos\AI\bridge_mt5_pro.py',
        r'C:\Users\Administrator\repos\AI\ea\bridge_mt5_pro.py',
    ]
    hashes = []
    for f in files:
        with open(f, 'rb') as fh:
            hashes.append(hashlib.sha256(fh.read()).hexdigest())
    assert hashes[0] == hashes[1], "bridge_mt5_pro.py copies are NOT identical!"
    print("OK: repo and ea/ bridge_mt5_pro.py are identical")
    return True


if __name__ == '__main__':
    ok = True
    for fn in [check_status_payload_fields, check_py_compile, check_files_identical]:
        try:
            fn()
        except Exception as e:
            print(f"FAIL: {fn.__name__}: {e}")
            ok = False
    if ok:
        print("\nALL CHECKS PASSED")
    else:
        print("\nSOME CHECKS FAILED")
        sys.exit(1)
