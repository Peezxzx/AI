#!/usr/bin/env bash
# ============================================================
# ATSAWIN MACHINE MIGRATION SCRIPT
# Run this on the NEW machine after installing Windows
# This pulls everything from GitHub and sets it up
# ============================================================
set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'
log() { echo -e "${GREEN}[OK]${NC} $*"; }
warn() { echo -e "${YELLOW}[..]${NC} $*"; }
err()  { echo -e "${RED}[!!]${NC} $*"; }

NEW_MACHINE_USER="${1:-Administrator}"
DESKTOP_PATH="/c/Users/$NEW_MACHINE_USER/Desktop"
REPOS_PATH="/c/Users/$NEW_MACHINE_USER/repos"

echo ""
echo "========================================"
echo " ATSAWIN MACHINE MIGRATION"
echo " $(date)"
echo "========================================"
echo ""

# ---- STEP 1: Install required software ----
log "Step 1: Install required software (manual)"
echo ""
echo "  [ ] Python 3.11+  → https://python.org"
echo "  [ ] Git for Windows → https://git-scm.com"
echo "  [ ] MetaTrader 5   → https://www.metatrader5.com"
echo "  [ ] Hermes Agent    → (your current AI assistant)"
echo ""
read -p "  Press Enter when all installed..."

# ---- STEP 2: Configure Git ----
log "Step 2: Git config"
git config --global user.name "Peezxzx"
git config --global user.email "peezxzx@users.noreply.github.com"
git config --global credential.helper manager
log "  Git configured"

# ---- STEP 3: Clone all repos ----
log "Step 3: Clone repos from GitHub"
mkdir -p "$REPOS_PATH"

declare -A REPOS=(
    ["AI"]="https://github.com/Peezxzx/AI.git"
    ["ai-trading-rpg"]="https://github.com/Peezxzx/ai-trading-rpg.git"
    ["atsawin-trading-cafe"]="https://github.com/Peezxzx/atsawin-trading-cafe.git"
)

for name in "${!REPOS[@]}"; do
    url="${REPOS[$name]}"
    target="$REPOS_PATH/$name"
    if [ -d "$target/.git" ]; then
        warn "  $name: already exists, pulling latest..."
        cd "$target" && git pull origin main
    else
        log "  Cloning $name..."
        git clone "$url" "$target"
    fi
done

# ---- STEP 4: Restore Desktop files ----
log "Step 4: Restore Desktop trading files"
mkdir -p "$DESKTOP_PATH"
if [ -d "$REPOS_PATH/AI/desktop-sync" ]; then
    cp "$REPOS_PATH/AI/desktop-sync/"* "$DESKTOP_PATH/" 2>/dev/null || true
    log "  Desktop files copied"
fi

# ---- STEP 5: Set up Python venv ----
log "Step 5: Python virtual environment"
cd "$REPOS_PATH/AI"
if [ -f "backend/requirements.txt" ]; then
    uv venv 2>/dev/null || python -m venv venv
    source venv/Scripts/activate 2>/dev/null || source venv/bin/activate
    uv pip install -r backend/requirements.txt 2>/dev/null || pip install -r backend/requirements.txt
    log "  Python deps installed"
fi

# ---- STEP 6: Set up sync bridge ----
log "Step 6: Setting up sync bridge"
mkdir -p "/c/Users/$NEW_MACHINE_USER/backups/scripts"
cp "$REPOS_PATH/AI/backups/scripts/"* "/c/Users/$NEW_MACHINE_USER/backups/scripts/" 2>/dev/null || true
cp "$REPOS_PATH/AI/backups/SYNC_GUIDE.md" "/c/Users/$NEW_MACHINE_USER/backups/" 2>/dev/null || true

# Update bridge_state.json with new machine
cat > "$REPOS_PATH/AI/bridge_state.json" << STATE
{
  "system": "Atsawin Cross-Machine Bridge",
  "version": "1.0",
  "migrated": "$(date '+%Y-%m-%d %H:%M')",
  "current_machine": "$(hostname)",
  "history": "migrated from DESKTOP-4NRHFGA",
  "sync": {
    "method": "git",
    "hub": "github.com/Peezxzx",
    "manual_cmd": "bash /c/Users/$NEW_MACHINE_USER/backups/scripts/sync_bridge.sh"
  }
}
STATE
log "  Bridge configured"

# ---- STEP 7: MT5 setup reminder ----
echo ""
echo "========================================"
log "MANUAL STEPS REMAINING:"
echo ""
echo "  1. Login MT5 → Exness-MT5Trial7"
echo "     Login: 433684944"
echo "  2. Copy EA files to MT5:"
echo "     $REPOS_PATH/AI/ea/AtsawinEA.mq5"
echo "     → MT5 MQL5/Experts/"
echo "  3. Enable AutoTrading in MT5"
echo "  4. Test bridge:"
echo "     python $DESKTOP_PATH/bridge_mt5_pro.py"
echo ""
echo "========================================"
log "MIGRATION COMPLETE!"
echo "  Repos: $REPOS_PATH"
echo "  Sync:  bash /c/Users/$NEW_MACHINE_USER/backups/scripts/sync_bridge.sh"
echo "  Guide: /c/Users/$NEW_MACHINE_USER/backups/SYNC_GUIDE.md"
echo "========================================"