#!/usr/bin/env bash
# ============================================================
# ATSAWIN UBUNTU SETUP — Production Server
# Run this on Ubuntu VPS (22.04/24.04)
# Connects with Windows machine via Syncthing + GitHub
# ============================================================
set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'
log() { echo -e "${GREEN}[OK]${NC} $*"; }
warn() { echo -e "${YELLOW}[..]${NC} $*"; }

ATSAWIN_HOME="/opt/atsawin"
SYNC_BASE="/home/ubuntu/syncthing"

echo "============================================"
echo " ATSAWIN UBUNTU PRODUCTION SETUP"
echo " $(date)"
echo "============================================"

# ---- 1: System update ----
log "Step 1: System update"
sudo apt update -y && sudo apt upgrade -y

# ---- 2: Install dependencies ----
log "Step 2: Install core dependencies"
sudo apt install -y \
    curl wget git build-essential \
    python3 python3-pip python3-venv \
    docker.io docker-compose-v2 \
    ufw nginx certbot python3-certbot-nginx

sudo systemctl enable docker --now
sudo usermod -aG docker ubuntu

# ---- 3: Install Syncthing ----
log "Step 3: Install Syncthing"
sudo curl -o /usr/share/keyrings/syncthing-archive-keyring.gpg \
    https://syncthing.net/release-key.gpg
echo "deb [signed-by=/usr/share/keyrings/syncthing-archive-keyring.gpg] https://apt.syncthing.net/ syncthing stable" | \
    sudo tee /etc/apt/sources.list.d/syncthing.list
sudo apt update -y && sudo apt install -y syncthing

# Start Syncthing as systemd service
sudo systemctl enable syncthing@ubuntu --now
log "  Syncthing installed and running"

# ---- 4: Create directories ----
log "Step 4: Create workspace"
sudo mkdir -p "$ATSAWIN_HOME"
sudo chown ubuntu:ubuntu "$ATSAWIN_HOME"

mkdir -p "$SYNC_BASE"/{desktop-scripts,trading-signals,hermes-configs,mt5-common}
mkdir -p "$ATSAWIN_HOME"/{logs,backups,data}
mkdir -p /home/ubuntu/repos

# ---- 5: Clone repos from GitHub ----
log "Step 5: Clone repos"
REPOS=(
    "https://github.com/Peezxzx/AI.git"
    "https://github.com/Peezxzx/ai-trading-rpg.git"
    "https://github.com/Peezxzx/atsawin-trading-cafe.git"
)

for url in "${REPOS[@]}"; do
    name=$(basename "$url" .git)
    target="/home/ubuntu/repos/$name"
    if [ -d "$target/.git" ]; then
        warn "  $name: exists, pulling..."
        cd "$target" && git pull origin main
    else
        git clone "$url" "$target"
        log "  $name: cloned"
    fi
done

# ---- 6: Python venv + deps ----
log "Step 6: Python environment"
cd "/home/ubuntu/repos/AI"
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip

if [ -f "backend/requirements.txt" ]; then
    pip install -r backend/requirements.txt
    log "  Python deps installed"
fi

# ---- 7: Docker services (PostgreSQL + Redis) ----
log "Step 7: Docker services"

cat > "$ATSAWIN_HOME/docker-compose.yml" << 'DOCKER'
version: "3.8"
services:
  postgres:
    image: postgres:16
    container_name: atsawin-db
    restart: unless-stopped
    environment:
      POSTGRES_USER: atsawin
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-atsawin_secret}
      POSTGRES_DB: atsawin
    ports:
      - "5433:5432"
    volumes:
      - pg_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U atsawin"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: atsawin-cache
    restart: unless-stopped
    ports:
      - "6380:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  pg_data:
  redis_data:
DOCKER

cd "$ATSAWIN_HOME"
sudo docker compose up -d
log "  Docker services started"

# ---- 8: Firewall ----
log "Step 8: Configure firewall"
sudo ufw allow 22/tcp      # SSH
sudo ufw allow 80/tcp      # HTTP
sudo ufw allow 443/tcp     # HTTPS
sudo ufw allow 8000/tcp    # FastAPI
sudo ufw allow 8384/tcp    # Syncthing GUI
sudo ufw allow 22000/tcp   # Syncthing data
sudo ufw --force enable

# ---- 9: Systemd service for FastAPI ----
log "Step 9: Systemd service for backend"

sudo tee /etc/systemd/system/atsawin-api.service << 'SYSTEMD'
[Unit]
Description=Atsawin FastAPI Backend
After=network.target docker.service
Requires=docker.service

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/repos/AI
Environment="PATH=/home/ubuntu/repos/AI/venv/bin:/usr/bin"
ExecStart=/home/ubuntu/repos/AI/venv/bin/uvicorn backend.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
SYSTEMD

sudo systemctl daemon-reload
sudo systemctl enable atsawin-api
log "  Systemd service created"

# ---- 10: Copy sync scripts ----
log "Step 10: Setup sync bridge"
cp "/home/ubuntu/repos/AI/backups/scripts/"*.sh "$ATSAWIN_HOME/" 2>/dev/null || true

# ---- 11: Syncthing config for auto-connect ----
log "Step 11: Syncthing — add folders"
sleep 5  # Wait for Syncthing to generate config

SYNCTHING_CONFIG="/home/ubuntu/.local/state/syncthing/config.xml"
API_KEY=$(grep -oP '<apikey>\K[^<]+' "$SYNCTHING_CONFIG" 2>/dev/null || echo "")

if [ -n "$API_KEY" ]; then
    UBUNTU_DEVICE_ID=$(grep -oP 'device id="\K[^"]+' "$SYNCTHING_CONFIG" | head -1)
    
    FOLDERS=(
        '{"id":"atsawin-desktop","label":"Desktop Scripts","path":"/home/ubuntu/syncthing/desktop-scripts"}'
        '{"id":"atsawin-signals","label":"Trading Signals","path":"/home/ubuntu/syncthing/trading-signals"}'
        '{"id":"atsawin-hermes","label":"Hermes Configs","path":"/home/ubuntu/syncthing/hermes-configs"}'
        '{"id":"atsawin-mt5","label":"MT5 Common","path":"/home/ubuntu/syncthing/mt5-common"}'
    )
    
    for folder in "${FOLDERS[@]}"; do
        curl -s -X POST "http://127.0.0.1:8384/rest/config/folders" \
            -H "X-API-Key: $API_KEY" \
            -H "Content-Type: application/json" \
            -d "$folder" 2>/dev/null || true
    done
    
    log "  Ubuntu Device ID: $UBUNTU_DEVICE_ID"
else
    warn "  Syncthing API key not found — configure manually at http://<ubuntu-ip>:8384"
fi

# ---- DONE ----
echo ""
echo "============================================"
echo " UBUNTU SETUP COMPLETE"
echo "============================================"
echo ""
echo " Services:"
echo "   PostgreSQL : localhost:5433"
echo "   Redis      : localhost:6380"
echo "   FastAPI    : http://<ip>:8000"
echo "   Syncthing  : http://<ip>:8384"
echo ""
echo " NEXT: เชื่อมกับ Windows"
echo "   1. บน Windows → Syncthing Web UI: http://127.0.0.1:8384"
echo "   2. Add Remote Device → ใส่ Ubuntu Device ID:"
echo "      $UBUNTU_DEVICE_ID"
echo "   3. Share โฟลเดอร์ให้ Ubuntu"
echo "   4. บน Ubuntu → รับ share → ไฟล์ sync ทันที"
echo ""
echo " Files:"
echo "   Repos   : /home/ubuntu/repos/"
echo "   Config  : /opt/atsawin/"
echo "   Sync    : /home/ubuntu/syncthing/"
echo ""