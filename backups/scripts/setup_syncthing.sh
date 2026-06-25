#!/usr/bin/env bash
# ============================================================
# ATSAWIN SYNCTHING SETUP
# Creates all sync folders and starts Syncthing
# ============================================================
set -euo pipefail

SYNC_BASE="/c/Users/Administrator/syncthing"

echo "=== ATSAWIN Syncthing Setup ==="

# Create sync folders
mkdir -p "$SYNC_BASE/desktop-scripts"
mkdir -p "$SYNC_BASE/trading-signals"
mkdir -p "$SYNC_BASE/hermes-configs"
mkdir -p "$SYNC_BASE/mt5-common"

echo "Folders created:"
echo "  $SYNC_BASE/desktop-scripts   → Desktop .py/.cmd files"
echo "  $SYNC_BASE/trading-signals   → MT5 signal JSON"
echo "  $SYNC_BASE/hermes-configs     → Hermes config/skills/cron"
echo "  $SYNC_BASE/mt5-common        → MT5 Common/Files"

# Create initial sync links (symlinks or copy on first run)
SOURCE_DESKTOP="/c/Users/Administrator/Desktop"
SOURCE_SIGNALS="/c/Users/Administrator/AppData/Roaming/MetaQuotes/Terminal/Common/Files/atsawin"
SOURCE_HERMES="/c/Users/Administrator/AppData/Local/hermes"

# Copy current state to sync folders (first sync)
echo ""
echo "=== Initial sync (copy current files) ==="

# Desktop scripts
find "$SOURCE_DESKTOP" -maxdepth 1 \( -name "*.py" -o -name "*.cmd" -o -name "*.ps1" -o -name "*.json" -o -name "*.txt" \) \
    -exec cp {} "$SYNC_BASE/desktop-scripts/" \; 2>/dev/null || true
echo "  Desktop → synced"

# Trading signals
if [ -d "$SOURCE_SIGNALS" ]; then
    cp -r "$SOURCE_SIGNALS"/* "$SYNC_BASE/trading-signals/" 2>/dev/null || true
    echo "  Trading signals → synced"
fi

# Hermes configs
cp "$SOURCE_HERMES/config.yaml" "$SYNC_BASE/hermes-configs/" 2>/dev/null || true
[ -d "$SOURCE_HERMES/skills" ] && cp -r "$SOURCE_HERMES/skills" "$SYNC_BASE/hermes-configs/" 2>/dev/null || true
[ -d "$SOURCE_HERMES/cron" ] && cp -r "$SOURCE_HERMES/cron" "$SYNC_BASE/hermes-configs/" 2>/dev/null || true
[ -d "$SOURCE_HERMES/memories" ] && cp -r "$SOURCE_HERMES/memories" "$SYNC_BASE/hermes-configs/" 2>/dev/null || true
echo "  Hermes configs → synced"

# MT5 common
MT5_COMMON="/c/Users/Administrator/AppData/Roaming/MetaQuotes/Terminal/Common/Files"
if [ -d "$MT5_COMMON" ]; then
    cp -r "$MT5_COMMON/atsawin" "$SYNC_BASE/mt5-common/" 2>/dev/null || true
    cp -r "$MT5_COMMON/tempo" "$SYNC_BASE/mt5-common/" 2>/dev/null || true
    echo "  MT5 common → synced"
fi

echo ""
echo "=== NEXT STEPS ==="
echo "1. Open http://127.0.0.1:8384 in browser"
echo "2. Actions → Show ID → copy Device ID"
echo "3. On new machine: Add Remote Device → paste ID"
echo "4. Share these folders:"
echo "   - $SYNC_BASE/desktop-scripts"
echo "   - $SYNC_BASE/trading-signals"
echo "   - $SYNC_BASE/hermes-configs"
echo "   - $SYNC_BASE/mt5-common"
echo ""
echo "=== DONE ==="