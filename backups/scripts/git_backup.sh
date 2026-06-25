#!/usr/bin/env bash
# ============================================================
# ATSAWIN GIT-BACKUP (LIGHTWEIGHT)
# Just commits + pushes to GitHub. No local archive bloat.
# Run via cron or manually.
# ============================================================
set -euo pipefail

TIMESTAMP=$(date '+%Y%m%d_%H%M%S')
REPOS=(
    "/c/Users/Administrator/repos/AI"
    "/c/Users/Administrator/repos/ai-trading-rpg"
    "/c/Users/Administrator/repos/atsawin-trading-cafe"
)

# ---- Sync Desktop files into AI repo first ----
DESKTOP_SRC="/c/Users/Administrator/Desktop"
DESKTOP_DST="/c/Users/Administrator/repos/AI/desktop-sync"
mkdir -p "$DESKTOP_DST"

for ext in py cmd ps1 json txt; do
    find "$DESKTOP_SRC" -maxdepth 1 -name "*.$ext" -exec cp {} "$DESKTOP_DST/" \; 2>/dev/null
done

# ---- Commit + push each repo ----
for repo in "${REPOS[@]}"; do
    [ ! -d "$repo/.git" ] && continue
    cd "$repo"
    git add -A 2>/dev/null || true
    if ! git diff --cached --quiet 2>/dev/null; then
        git commit -m "backup: $TIMESTAMP" 2>/dev/null || true
    fi
    git push origin HEAD 2>/dev/null || echo "WARN: push failed for $(basename "$repo")"
done

echo "BACKUP_OK $TIMESTAMP"