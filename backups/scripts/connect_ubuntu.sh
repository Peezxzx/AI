#!/usr/bin/env bash
# ============================================================
# CONNECT WINDOWS TO UBUNTU
# Usage: bash connect_ubuntu.sh <ubuntu-ip-or-hostname>
# This adds Ubuntu as a Syncthing peer and shares all folders
# ============================================================
set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

UBUNTU_IP="${1:-}"
if [ -z "$UBUNTU_IP" ]; then
    echo "Usage: $0 <ubuntu-ip>"
    echo "  Get Ubuntu device ID first:"
    echo "    ssh ubuntu@<ip> 'cat ~/.local/state/syncthing/config.xml | grep -oP \"device id=\\\"\\K[^\"]+\" | head -1'"
    exit 1
fi

log() { echo -e "${GREEN}[OK]${NC} $*"; }
err() { echo -e "${RED}[ERR]${NC} $*"; }

# ---- Get Ubuntu Syncthing Device ID ----
log "Fetching Ubuntu Syncthing Device ID..."

UBUNTU_ID=$(ssh "ubuntu@${UBUNTU_IP}" \
    "grep -oP 'device id=\"\K[^\"]+' ~/.local/state/syncthing/config.xml | head -1" 2>/dev/null)

if [ -z "$UBUNTU_ID" ]; then
    err "Cannot reach Ubuntu at $UBUNTU_IP"
    echo ""
    echo "  Make sure:"
    echo "  1. Ubuntu is online"
    echo "  2. SSH key is set up: ssh-copy-id ubuntu@$UBUNTU_IP"
    echo "  3. Syncthing is running on Ubuntu"
    echo ""
    echo "  Or get the ID manually:"
    echo "  ssh ubuntu@$UBUNTU_IP"
    echo "  grep -oP 'device id=\"\K[^\"]+' ~/.local/state/syncthing/config.xml | head -1"
    exit 1
fi

log "Ubuntu Device ID: $UBUNTU_ID"

# ---- Get Windows Syncthing API key ----
WINDOWS_CONFIG="/c/Users/Administrator/AppData/Local/Syncthing/config.xml"
API_KEY=*** -oP '<apikey>\K[^<]+' "$WINDOWS_CONFIG" 2>/dev/null)

if [ -z "$API_KEY" ]; then
    err "Syncthing not running on Windows. Start it first."
    exit 1
fi

# ---- Add Ubuntu as remote device ----
log "Adding Ubuntu to Syncthing..."

DEVICE_JSON=$(cat <<EOF
{
    "deviceID": "$UBUNTU_ID",
    "name": "ubuntu-vps",
    "addresses": ["dynamic"],
    "compression": "metadata",
    "introducer": false,
    "autoAcceptFolders": false
}
EOF
)

curl -s -X POST "http://127.0.0.1:8384/rest/config/devices" \
    -H "X-API-Key: $API_KEY" \
    -H "Content-Type: application/json" \
    -d "$DEVICE_JSON" 2>/dev/null

log "  Ubuntu added as device"

# ---- Share folders with Ubuntu ----
log "Sharing folders..."

FOLDERS=(
    "atsawin-desktop"
    "atsawin-signals"
    "atsawin-hermes"
    "atsawin-mt5"
)

for folder_id in "${FOLDERS[@]}"; do
    # Get current folder config
    FOLDER_CONFIG=$(curl -s "http://127.0.0.1:8384/rest/config/folders/$folder_id" \
        -H "X-API-Key: $API_KEY" 2>/dev/null)
    
    if echo "$FOLDER_CONFIG" | grep -q "$folder_id"; then
        # Add Ubuntu device to folder's device list
        UPDATED=$(echo "$FOLDER_CONFIG" | python3 -c "
import sys, json
f = json.load(sys.stdin)
devices = [d.get('deviceID','') for d in f.get('devices',[])]
devices.append('$UBUNTU_ID')
f['devices'] = [{'deviceID': d} for d in list(set(devices))]
print(json.dumps(f))
" 2>/dev/null)
        
        if [ -n "$UPDATED" ]; then
            curl -s -X PATCH "http://127.0.0.1:8384/rest/config/folders/$folder_id" \
                -H "X-API-Key: $API_KEY" \
                -H "Content-Type: application/json" \
                -d "$UPDATED" 2>/dev/null
            log "  $folder_id: shared"
        fi
    fi
done

# ---- Restart Syncthing to apply ----
log "Restarting Syncthing..."
curl -s -X POST "http://127.0.0.1:8384/rest/system/restart" \
    -H "X-API-Key: $API_KEY" 2>/dev/null

sleep 3

echo ""
echo "============================================"
log "WINDOWS ↔ UBUNTU CONNECTED!"
echo "============================================"
echo ""
echo "  Windows Device: Q3TV2RP-7LOP2TS-..."
echo "  Ubuntu Device:  $UBUNTU_ID"
echo ""
echo "  Sync status: http://127.0.0.1:8384"
echo ""
echo "  Files will sync automatically."
echo "  Ubuntu API: http://$UBUNTU_IP:8000"
echo ""