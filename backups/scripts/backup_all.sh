#!/usr/bin/env bash
# ============================================================
# ATSAWIN FULL SYSTEM BACKUP SCRIPT
# Created: 2026-06-25
# Backs up: repos, hermes config, MT5 data, desktop scripts
# ============================================================
set -euo pipefail

TIMESTAMP=$(date '+%Y%m%d_%H%M%S')
BACKUP_ROOT="/c/Users/Administrator/backups"
LOG_FILE="$BACKUP_ROOT/backup_${TIMESTAMP}.log"
MAX_BACKUPS=7  # Keep last 7 backups

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

# Create timestamped backup dir
BACKUP_DIR="$BACKUP_ROOT/backup_${TIMESTAMP}"

log "===== ATSAWIN BACKUP STARTED ====="

# ---------- 1. Git repos (push to GitHub + local snapshot) ----------
log "Step 1: Backing up git repos..."

REPOS=(
    "/c/Users/Administrator/repos/AI"
    "/c/Users/Administrator/repos/ai-trading-rpg"
    "/c/Users/Administrator/repos/atsawin-trading-cafe"
    "/c/Users/Administrator/repos/AI_fresh"
)

for repo in "${REPOS[@]}"; do
    if [ -d "$repo/.git" ]; then
        repo_name=$(basename "$repo")
        log "  Processing $repo_name..."
        
        # Stage + commit any changes
        cd "$repo"
        if ! git diff --quiet || ! git diff --cached --quiet || [ -n "$(git ls-files --others --exclude-standard)" ]; then
            git add -A 2>/dev/null || true
            git commit -m "auto-backup: $TIMESTAMP" 2>/dev/null || true
        fi
        
        # Push to GitHub (best backup)
        git push origin HEAD 2>&1 | tee -a "$LOG_FILE" || log "  WARN: Push failed for $repo_name"
        
        # Local bundle as extra safety
        BUNDLE_DIR="$BACKUP_DIR/repos"
        mkdir -p "$BUNDLE_DIR"
        git bundle create "$BUNDLE_DIR/${repo_name}.bundle" --all 2>/dev/null || log "  WARN: Bundle failed for $repo_name"
    else
        log "  SKIP: $repo (no .git)"
    fi
done

# ---------- 2. Hermes config ----------
log "Step 2: Backing up Hermes config..."
HERMES_DIR="$BACKUP_DIR/hermes"
mkdir -p "$HERMES_DIR"
cp -r "/c/Users/Administrator/AppData/Local/hermes/config.yaml" "$HERMES_DIR/" 2>/dev/null || true
cp -r "/c/Users/Administrator/AppData/Local/hermes/skills" "$HERMES_DIR/" 2>/dev/null || true
cp -r "/c/Users/Administrator/AppData/Local/hermes/cron" "$HERMES_DIR/" 2>/dev/null || true
cp -r "/c/Users/Administrator/AppData/Local/hermes/memories" "$HERMES_DIR/" 2>/dev/null || true

# ---------- 3. Desktop scripts ----------
log "Step 3: Backing up Desktop scripts..."
DESKTOP_DIR="$BACKUP_DIR/desktop"
mkdir -p "$DESKTOP_DIR"
find "/c/Users/Administrator/Desktop" -maxdepth 1 \( -name "*.py" -o -name "*.cmd" -o -name "*.ps1" -o -name "*.bat" -o -name "*.json" -o -name "*.txt" -o -name "*.sh" \) \
    -exec cp {} "$DESKTOP_DIR/" \; 2>/dev/null || true

# ---------- 4. MT5 critical files ----------
log "Step 4: Backing up MT5 configs..."
MT5_DIR="$BACKUP_DIR/mt5"
mkdir -p "$MT5_DIR"
# MT5 user data
MT5_TERMINAL="/c/Users/Administrator/AppData/Roaming/MetaQuotes/Terminal"
if [ -d "$MT5_TERMINAL" ]; then
    # Find active terminal instance
    for d in "$MT5_TERMINAL"/*/; do
        if [ -f "$d/origin.txt" ]; then
            terminal_name=$(basename "$d")
            mkdir -p "$MT5_DIR/$terminal_name"
            cp "$d/origin.txt" "$MT5_DIR/$terminal_name/" 2>/dev/null || true
            # Backup MQL5 Experts
            [ -d "$d/MQL5/Experts" ] && cp -r "$d/MQL5/Experts" "$MT5_DIR/$terminal_name/" 2>/dev/null || true
            # Backup config
            [ -f "$d/config/common.ini" ] && cp "$d/config/common.ini" "$MT5_DIR/$terminal_name/" 2>/dev/null || true
            break
        fi
    done
fi
# MT5 Common files (signal bridge)
MT5_COMMON="/c/Users/Administrator/AppData/Roaming/MetaQuotes/Terminal/Common"
[ -d "$MT5_COMMON" ] && cp -r "$MT5_COMMON/Files/atsawin" "$MT5_DIR/common_files/" 2>/dev/null || true
[ -d "$MT5_COMMON" ] && cp -r "$MT5_COMMON/Files/tempo" "$MT5_DIR/common_files/" 2>/dev/null || true

# ---------- 5. Clean old backups ----------
log "Step 5: Cleaning old backups..."
BACKUP_COUNT=$(ls -1d "$BACKUP_ROOT"/backup_* 2>/dev/null | wc -l | tr -d ' ')
if [ "$BACKUP_COUNT" -gt "$MAX_BACKUPS" ]; then
    DELETE_COUNT=$((BACKUP_COUNT - MAX_BACKUPS))
    ls -1dt "$BACKUP_ROOT"/backup_* 2>/dev/null | tail -n "$DELETE_COUNT" | xargs rm -rf 2>/dev/null || true
    log "  Removed $DELETE_COUNT old backup(s)"
fi

# ---------- Summary ----------
BACKUP_SIZE=$(du -sh "$BACKUP_DIR" 2>/dev/null | cut -f1)
log "===== BACKUP COMPLETE ====="
log "Location: $BACKUP_DIR"
log "Size: $BACKUP_SIZE"
log "Log: $LOG_FILE"
log "==========================="

echo "BACKUP_DIR=$BACKUP_DIR"
echo "BACKUP_SIZE=$BACKUP_SIZE"