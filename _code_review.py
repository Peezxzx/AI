"""ATSAWIN Review — Code-level risk checks."""
import ast
import os
import re
import sys

repo = 'C:/Users/Administrator/repos/AI'
issues = []
warnings = []

def check_file(filepath):
    """Check a Python file for dangerous patterns."""
    try:
        src = open(filepath, encoding='utf-8').read()
    except Exception:
        return

    lines = src.splitlines()
    fname = os.path.relpath(filepath, repo)

    # 1. Check for hardcoded Windows paths that may be wrong
    for i, line in enumerate(lines, 1):
        # Hardcoded paths that don't use CONFIG or os.path
        if re.search(r'C:\\\\Users\\\\', line) and 'CONFIG' not in line and 'r"' not in line and "r'" not in line:
            if 'CONFIG' in src and 'config' not in line.lower():
                continue  # skip config definitions
            warnings.append(f"{fname}:{i}: Hardcoded Windows path (verify correctness)")

    # 2. Check for missing try/except around MT5 calls
    mt5_funcs = ['mt5.initialize', 'mt5.symbol_info_tick', 'mt5.copy_rates_from_pos',
                 'mt5.account_info', 'mt5.symbol_info', 'mt5.positions_get']
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith('#') or stripped.startswith('//'):
            continue
        for func in mt5_funcs:
            if func in line and 'try' not in stripped and 'except' not in stripped:
                # Check if we're inside a try block (simple heuristic: look back 10 lines)
                in_try = False
                for back in range(max(0, i-10), i):
                    if 'try' in lines[back-1].strip() or lines[back-1].strip().endswith(':'):
                        if 'try' in lines[back-1].strip():
                            in_try = True
                            break
                if not in_try and 'def ' not in line:
                    warnings.append(f"{fname}:{i}: MT5 call '{func}' possibly unguarded")

    # 3. Check for ensure_ascii=True (contract requires ASCII-safe output)
    for i, line in enumerate(lines, 1):
        if 'ensure_ascii' in line:
            if 'ensure_ascii=True' in line:
                warnings.append(f"{fname}:{i}: OK — ensure_ascii=True (contract compliant)")
            elif 'ensure_ascii=False' in line:
                issues.append(f"{fname}:{i}: CRITICAL — ensure_ascii=False breaks MQL5 FILE_ANSI reading!")

    # 4. Check for signal_id / setup_key in payload
    for i, line in enumerate(lines, 1):
        if 'signal_id' in line and 'payload' in line:
            warnings.append(f"{fname}:{i}: Payload includes signal_id reference — verify it's always set")

    # 5. Check for validate_payload being called before write
    for i, line in enumerate(lines, 1):
        if 'atomic_write' in line and 'signal_path' in line:
            # Check if validate_payload was called before
            has_validation = any('validate_payload' in l for l in lines[:i])
            if has_validation:
                warnings.append(f"{fname}:{i}: OK — atomic_write with prior validate_payload")
            else:
                issues.append(f"{fname}:{i}: atomic_write without validate_payload!")

    # 6. Check for confidence clamping
    for i, line in enumerate(lines, 1):
        if 'confidence' in line and 'min(' in line and '1.0' in line:
            warnings.append(f"{fname}:{i}: Confidence clamping detected — verify [0,1] range")

    # 7. Check for hardcoded credentials
    for i, line in enumerate(lines, 1):
        if re.search(r'password\s*=\s*["\']', line, re.IGNORECASE) or \
           re.search(r'api_key\s*=\s*["\']', line, re.IGNORECASE):
            if 'os.environ' not in line and 'getenv' not in line:
                warnings.append(f"{fname}:{i}: Possible hardcoded credential — use env vars")

    # 8. Check for ORDER_FILLING fallback in MQL5 EA files
    if filepath.endswith('.mq5'):
        for i, line in enumerate(lines, 1):
            if 'ORDER_FILLING_IOC' in line and i > 1:
                # Check if there's a fallback chain (ORDER_FILLING_FOK or ORDER_FILLING_RETURN)
                # Must check for the full ORDER_FILLING_ prefix to avoid false positives
                # from plain "return" statements (e.g. "return INIT_SUCCEEDED;")
                has_fallback = any('ORDER_FILLING_FOK' in l or 'ORDER_FILLING_RETURN' in l for l in lines)
                if has_fallback:
                    warnings.append(f"{fname}:{i}: OK — ORDER_FILLING_IOC with FOK/RETURN fallback")
                else:
                    warnings.append(f"{fname}:{i}: ORDER_FILLING_IOC without fallback may fail on some brokers")

    # 9. Check for file open without encoding
    for i, line in enumerate(lines, 1):
        if re.search(r'open\s*\(', line) and 'encoding' not in line:
            if 'FileOpen' not in line:  # MQL5 FileOpen doesn't have encoding param
                warnings.append(f"{fname}:{i}: open() without encoding parameter")

    # 10. Check risk_percent > 5%
    for i, line in enumerate(lines, 1):
        m = re.search(r'risk_percent[\s:=]+([\d.]+)', line)
        if m:
            val = float(m.group(1))
            if val > 5.0:
                issues.append(f"{fname}:{i}: CRITICAL — risk_percent={val}% exceeds 5% threshold!")
            elif val > 3.0:
                warnings.append(f"{fname}:{i}: Elevated risk_percent={val}% — verify intentional")


# Run checks on all relevant files
target_dirs = [
    os.path.join(repo, 'ea'),
    os.path.join(repo, 'backend', 'trading'),
]

target_files = [
    os.path.join(repo, 'bridge_mt5_pro.py'),
]

for d in target_dirs:
    if os.path.isdir(d):
        for f in os.listdir(d):
            if f.endswith(('.py', '.mq5')) and not f.startswith('_'):
                full = os.path.join(d, f)
                if os.path.isfile(full):
                    check_file(full)

for f in target_files:
    if os.path.isfile(f):
        check_file(f)

# Also check if bridge on Desktop matches repo
desktop_bridge = 'C:/Users/Administrator/Desktop/bridge_mt5_pro.py'
repo_bridge = os.path.join(repo, 'ea', 'bridge_mt5_pro.py')
if os.path.isfile(desktop_bridge) and os.path.isfile(repo_bridge):
    import hashlib
    def md5(p):
        return hashlib.md5(open(p, 'rb').read()).hexdigest()
    if md5(desktop_bridge) == md5(repo_bridge):
        warnings.append("DESKTOP SYNC: Desktop bridge_mt5_pro.py matches repo version")
    else:
        issues.append("DESKTOP SYNC MISMATCH: Desktop bridge differs from repo! Risk of running outdated code.")

# Also check atsawin_bridge.py for availability
legacy_bridge = os.path.join(repo, 'ea', 'atsawin_bridge.py')
if os.path.isfile(legacy_bridge):
    warnings.append("LEGACY BRIDGE: ea/atsawin_bridge.py still present — ensure it's not accidentally run instead of bridge_mt5_pro.py")

# Result
print("=" * 60)
print("CODE REVIEW RESULTS")
print("=" * 60)
print(f"\nCRITICAL ISSUES ({len(issues)}):")
for iss in issues:
    print(f"  FAIL: {iss}")
if not issues:
    print("  None")

print(f"\nWARNINGS / INFO ({len(warnings)}):")
for w in warnings:
    print(f"  WARN: {w}")

if issues:
    print("\nOVERALL: FAIL")
    sys.exit(1)
else:
    print("\nOVERALL: PASS (no critical issues)")
    sys.exit(0)
