#!/usr/bin/env bash
# ============================================================
# ATSAWIN CROSS-MACHINE SYNC BRIDGE
# Uses GitHub as the sync backbone between machines
# Run on EITHER machine to sync:
#   push: sends local changes to GitHub
#   pull: gets remote changes from GitHub
#   sync: push + pull (two-way sync)
# ============================================================
set -euo pipefail

MODE="${1:-sync}"  # push | pull | sync
MACHINE_ID="${2:-$(hostname)}"
TIMESTAMP=$(date '+%Y%m%d_%H%M%S')

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() { echo -e "${GREEN}[$TIMESTAMP]${NC} $*"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
err()  { echo -e "${RED}[ERR]${NC} $*"; }

REPOS=(
    "/c/Users/Administrator/repos/AI"
    "/c/Users/Administrator/repos/ai-trading-rpg"
    "/c/Users/Administrator/repos/atsawin-trading-cafe"
)

# ----- SYNC DESKTOP FILES INTO AI REPO -----
sync_desktop_to_repo() {
    log "Syncing Desktop files → AI repo..."
    DESKTOP="/c/Users/Administrator/Desktop"
    REPO_DESKTOP="/c/Users/Administrator/repos/AI/desktop-sync"
    mkdir -p "$REPO_DESKTOP"
    
    # Copy important desktop scripts into repo (so they're backed up via git)
    for ext in py cmd ps1 bat json txt sh; do
        find "$DESKTOP" -maxdepth 1 -name "*.$ext" -newer "$REPO_DESKTOP/.last_sync" \
            -exec cp {} "$REPO_DESKTOP/" \; 2>/dev/null || true
    done
    
    # Copy bridge_mt5_pro.py specifically
    [ -f "$DESKTOP/bridge_mt5_pro.py" ] && cp "$DESKTOP/bridge_mt5_pro.py" "$REPO_DESKTOP/" 2>/dev/null || true
    
    touch "$REPO_DESKTOP/.last_sync"
    log "  Desktop sync done"
}

# ----- PUSH ALL REPOS -----
do_push() {
    log "=== PUSH MODE: $MACHINE_ID → GitHub ==="
    sync_desktop_to_repo
    
    for repo in "${REPOS[@]}"; do
        repo_name=$(basename "$repo")
        if [ ! -d "$repo/.git" ]; then
            warn "  SKIP $repo_name (no git)"
            continue
        fi
        
        cd "$repo"
        
        # Stage + commit if dirty
        if ! git diff --quiet 2>/dev/null || ! git diff --cached --quiet 2>/dev/null || \
           [ -n "$(git ls-files --others --exclude-standard 2>/dev/null)" ]; then
            git add -A
            git commit -m "sync($MACHINE_ID): $TIMESTAMP" 2>/dev/null || true
            log "  $repo_name: committed changes"
        fi
        
        # Push
        if git push origin HEAD 2>&1; then
            log "  $repo_name: pushed OK"
        else
            err "  $repo_name: push FAILED"
        fi
    done
}

# ----- PULL ALL REPOS -----
do_pull() {
    log "=== PULL MODE: GitHub → $MACHINE_ID ==="
    
    for repo in "${REPOS[@]}"; do
        repo_name=$(basename "$repo")
        if [ ! -d "$repo/.git" ]; then
            warn "  SKIP $repo_name (no git)"
            continue
        fi
        
        cd "$repo"
        
        # Stash local changes before pull
        HAS_LOCAL=false
        if ! git diff --quiet 2>/dev/null || [ -n "$(git ls-files --others --exclude-standard 2>/dev/null)" ]; then
            git stash push -m "autostash-$TIMESTAMP" 2>/dev/null || true
            HAS_LOCAL=true
        fi
        
        # Pull
        if git pull origin HEAD 2>&1; then
            log "  $repo_name: pulled OK"
        else
            err "  $repo_name: pull FAILED"
        fi
        
        # Pop stash
        [ "$HAS_LOCAL" = true ] && git stash pop 2>/dev/null || true
    done
}

# ----- TWO-WAY SYNC -----
do_sync() {
    log "=== TWO-WAY SYNC: $MACHINE_ID ⇄ GitHub ==="
    do_push
    do_pull
}

# ----- Shared data bridge file -----
write_bridge_info() {
    BRIDGE_FILE="/c/Users/Administrator/repos/AI/bridge_info.json"
    cat > "$BRIDGE_FILE" << EOF
{
    "last_sync": "$TIMESTAMP",
    "machine": "$MACHINE_ID",
    "mode": "$MODE",
    "repos": [
        {"name": "AI", "path": "/c/Users/Administrator/repos/AI", "remote": "Peezxzx/AI"},
        {"name": "ai-trading-rpg", "path": "/c/Users/Administrator/repos/ai-trading-rpg", "remote": "Peezxzx/ai-trading-rpg"},
        {"name": "atsawin-trading-cafe", "path": "/c/Users/Administrator/repos/atsawin-trading-cafe", "remote": "Peezxzx/atsawin-trading-cafe"}
    ]
}
EOF
}

# ----- MAIN -----
case "$MODE" in
    push)  do_push ;;
    pull)  do_pull ;;
    sync)  do_sync ;;
    *)
        echo "Usage: $0 [push|pull|sync] [machine-id]"
        echo "  push  - send local changes to GitHub"
        echo "  pull  - get remote changes from GitHub"
        echo "  sync  - two-way push+pull (default)"
        exit 1
        ;;
esac

write_bridge_info
log "=== DONE ==="
echo "SYNC_OK"