"""Quick structural check of both bridge files."""
import ast
import hashlib

files = {
    "repo": r"C:\Users\Administrator\repos\AI\bridge_mt5_pro.py",
    "desktop": r"C:\Users\Administrator\Desktop\bridge_mt5_pro.py",
}

for label, path in files.items():
    with open(path, "r", encoding="utf-8") as f:
        src = f.read()
    tree = ast.parse(src)
    funcs = sorted({n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)})
    h = hashlib.md5(src.encode()).hexdigest()
    print(f"[{label}] md5={h} funcs={len(funcs)} _reconnect_mt5={'_reconnect_mt5' in funcs} scan_once={'scan_once' in funcs}")

# Compare
with open(files["repo"], "r", encoding="utf-8") as f:
    repo_src = f.read()
with open(files["desktop"], "r", encoding="utf-8") as f:
    desk_src = f.read()

if repo_src == desk_src:
    print("[MATCH] Desktop == Repo (byte-identical)")
else:
    print("[MISMATCH] Desktop != Repo")
    import difflib
    diff = list(difflib.unified_diff(repo_src.splitlines(), desk_src.splitlines(), lineterm="", n=1))
    for line in diff[:20]:
        print(line)
