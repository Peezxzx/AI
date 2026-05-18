#!/bin/bash
#================================================================
# ATSAWIN AI — Auto Install Script
# รัน: chmod +x install.sh && ./install.sh
#================================================================

set -e  # ถ้า error หยุดทันที

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}"
echo "╔══════════════════════════════════════════════════════════╗"
echo "║          🤖 ATSAWIN AI — Auto Installer v1.0            ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# ─── ตรวจสอบว่ารันบน Linux ──────────────────────────────────
if [[ "$OSTYPE" != "linux-gnu"* ]]; then
    echo -e "${YELLOW}⚠️  Script นี้ออกแบบสำหรับ Linux (Ubuntu/Debian)${NC}"
    echo -e "${YELLOW}   ถ้ารันบน Windows ใช้ WSL หรือติดตั้งเองทีละขั้น${NC}"
    read -p "รันต่อไหม? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# ─── ตรวจสอบ root/sudo ──────────────────────────────────────
if [[ $EUID -ne 0 ]]; then
    echo -e "${YELLOW}⚠️  แนะนำรันด้วย sudo สำหรับติดตั้ง system packages${NC}"
    SUDO="sudo"
else
    SUDO=""
fi

INSTALL_DIR="/root/AI"
BACKEND_DIR="$INSTALL_DIR/backend"
EA_DIR="$INSTALL_DIR/ea"

# ══════════════════════════════════════════════════════════════
# STEP 1: ติดตั้ง System Dependencies
# ══════════════════════════════════════════════════════════════
echo -e "\n${GREEN}[1/7] ติดตั้ง System Dependencies...${NC}"

$SUDO apt-get update -qq
$SUDO apt-get install -y -qq \
    python3 \
    python3-pip \
    python3-venv \
    git \
    curl \
    wget \
    build-essential \
    libpq-dev \
    docker.io \
    docker-compose \
    2>/dev/null || true

echo -e "  ${GREEN}✓ System packages OK${NC}"

# ══════════════════════════════════════════════════════════════
# STEP 2: Clone Repo (ถ้ายังไม่มี)
# ══════════════════════════════════════════════════════════════
echo -e "\n${GREEN}[2/7] เตรียมโปรเจกต์...${NC}"

if [ ! -d "$INSTALL_DIR" ]; then
    echo "  Cloning repo..."
    git clone https://github.com/Peezxzx/AI.git "$INSTALL_DIR"
else
    echo "  Repo มีอยู่แล้ว → pull ล่าสุด..."
    cd "$INSTALL_DIR" && git pull
fi

echo -e "  ${GREEN}✓ Repo ready${NC}"

# ══════════════════════════════════════════════════════════════
# STEP 3: สร้าง .env
# ══════════════════════════════════════════════════════════════
echo -e "\n${GREEN}[3/7] ตั้งค่า Environment...${NC}"

if [ ! -f "$INSTALL_DIR/.env" ]; then
    echo -e "  ${YELLOW}สร้าง .env จาก template...${NC}"

    # สร้าง random keys
    JWT_SECRET=$(python3 -c "import secrets; print(secrets.token_hex(32))")
    API_KEY="atsawin-$(python3 -c "import secrets; print(secrets.token_hex(8))")"

    cat > "$INSTALL_DIR/.env" << ENVEOF
# ══════════════════════════════════════════════════════════
# ATSAWIN AI — Environment Configuration
# ══════════════════════════════════════════════════════════

# ⚠️  แก้ค่าเหล่านี้ก่อนใช้งานจริง!

# AI (จำเป็น — สมัครที่ https://openrouter.ai)
OPENROUTER_API_KEY=sk-or-v1-YOUR_API_KEY_HERE

# Telegram (จำเป็น — สร้าง bot ที่ @BotFather)
TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN_HERE

# Database
POSTGRES_USER=atsawin
POSTGRES_PASSWORD=password123
POSTGRES_DB=atsawin_db
POSTGRES_HOST=localhost
POSTGRES_PORT=5433

# Redis
REDIS_HOST=localhost
REDIS_PORT=6380

# Security (auto-generated — เปลี่ยนได้)
JWT_SECRET_KEY=${JWT_SECRET}
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440

# API Key สำหรับ EA Bridge
API_KEY=${API_KEY}
ENVEOF

    echo -e "  ${YELLOW}⚠️  กรุณาแก้ OPENROUTER_API_KEY และ TELEGRAM_BOT_TOKEN ใน .env${NC}"
    echo -e "  ${YELLOW}   ไฟล์: $INSTALL_DIR/.env${NC}"
else
    echo -e "  ${GREEN}.env มีอยู่แล้ว → ข้าม${NC}"
fi

echo -e "  ${GREEN}✓ Environment ready${NC}"

# ══════════════════════════════════════════════════════════════
# STEP 4: ติดตั้ง Python Dependencies
# ══════════════════════════════════════════════════════════════
echo -e "\n${GREEN}[4/7] ติดตั้ง Python Dependencies...${NC}"

cd "$BACKEND_DIR"

# สร้าง venv
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "  สร้าง venv แล้ว"
fi

# Activate + install
source venv/bin/activate
pip install -q --upgrade pip
pip install -q -r requirements.txt

echo -e "  ${GREEN}✓ Python packages installed${NC}"

# ติดตั้ง aiohttp สำหรับ EA bridge
pip install -q aiohttp 2>/dev/null || true

# ══════════════════════════════════════════════════════════════
# STEP 5: รัน Database (Docker)
# ══════════════════════════════════════════════════════════════
echo -e "\n${GREEN}[5/7] เริ่ม Database (PostgreSQL + Redis)...${NC}"

cd "$INSTALL_DIR"

# เริ่ม docker-compose
$SUDO docker-compose up -d 2>/dev/null || {
    echo -e "  ${YELLOW}⚠️  Docker compose failed — ลองรัน PostgreSQL/Redis เอง${NC}"
    echo -e "  ${YELLOW}   หรือรัน: sudo apt install postgresql redis-server${NC}"
}

# รอ database พร้อม
echo "  รอ database พร้อม..."
for i in {1..30}; do
    if $SUDO docker exec atsawin-postgres pg_isready -U atsawin 2>/dev/null | grep -q "accepting"; then
        echo -e "  ${GREEN}✓ PostgreSQL ready${NC}"
        break
    fi
    sleep 1
done

# ══════════════════════════════════════════════════════════════
# STEP 6: สร้าง systemd Services
# ══════════════════════════════════════════════════════════════
echo -e "\n${GREEN}[6/7] สร้าง systemd Services...${NC}"

# FastAPI Service
$SUDO tee /etc/systemd/system/atsawin-api.service > /dev/null << 'SERVICEEOF'
[Unit]
Description=Atsawin AI FastAPI Backend
After=network.target docker.service
Requires=docker.service

[Service]
Type=simple
WorkingDirectory=/root/AI/backend
ExecStart=/root/AI/backend/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5
Environment=PATH=/root/AI/backend/venv/bin:/usr/bin:/bin
EnvironmentFile=/root/AI/.env

[Install]
WantedBy=multi-user.target
SERVICEEOF

# Telegram Bot Service
$SUDO tee /etc/systemd/system/atsawin-telegram-bot.service > /dev/null << 'SERVICEEOF'
[Unit]
Description=Atsawin AI Telegram Bot
After=network.target atsawin-api.service
Requires=atsawin-api.service

[Service]
Type=simple
WorkingDirectory=/root/AI/backend
ExecStart=/root/AI/backend/venv/bin/python telegram_bot.py
Restart=always
RestartSec=10
Environment=PATH=/root/AI/backend/venv/bin:/usr/bin:/bin
EnvironmentFile=/root/AI/.env

[Install]
WantedBy=multi-user.target
SERVICEEOF

# EA Bridge Service
$SUDO tee /etc/systemd/system/atsawin-ea-bridge.service > /dev/null << 'SERVICEEOF'
[Unit]
Description=Atsawin EA Bridge (Signal Generator)
After=network.target atsawin-api.service
Requires=atsawin-api.service

[Service]
Type=simple
WorkingDirectory=/root/AI/ea
ExecStart=/root/AI/backend/venv/bin/python atsawin_bridge.py
Restart=always
RestartSec=15
Environment=PATH=/root/AI/backend/venv/bin:/usr/bin:/bin
EnvironmentFile=/root/AI/.env

[Install]
WantedBy=multi-user.target
SERVICEEOF

# Reload + enable
$SUDO systemctl daemon-reload
$SUDO systemctl enable atsawin-api.service
$SUDO systemctl enable atsawin-telegram-bot.service
$SUDO systemctl enable atsawin-ea-bridge.service

echo -e "  ${GREEN}✓ systemd services created${NC}"

# ══════════════════════════════════════════════════════════════
# STEP 7: เริ่ม Services
# ══════════════════════════════════════════════════════════════
echo -e "\n${GREEN}[7/7] เริ่ม Services...${NC}"

$SUDO systemctl start atsawin-api.service
echo "  ✓ FastAPI started (port 8000)"

# รอ API พร้อม
sleep 3
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "  ${GREEN}✓ API responding${NC}"
else
    echo -e "  ${YELLOW}⚠️  API ยังไม่ตอบ — ดู log: journalctl -u atsawin-api${NC}"
fi

# ══════════════════════════════════════════════════════════════
# เสร็จ!
# ══════════════════════════════════════════════════════════════
echo -e "\n${CYAN}"
echo "╔══════════════════════════════════════════════════════════╗"
echo "║              ✅ ติดตั้งเสร็จสมบูรณ์!                      ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo -e "${NC}"

echo -e "${GREEN}Services:${NC}"
echo "  FastAPI:     http://localhost:8000"
echo "  API Docs:    http://localhost:8000/docs"
echo "  Health:      http://localhost:8000/health"
echo ""
echo -e "${GREEN}Commands:${NC}"
echo "  ดูสถานะ:     systemctl status atsawin-api"
echo "  ดู log:      journalctl -u atsawin-api -f"
echo "  รีสตาร์ท:    systemctl restart atsawin-api"
echo "  หยุด:        systemctl stop atsawin-api"
echo ""
echo -e "${YELLOW}⚠️  อย่าลืม:${NC}"
echo "  1. แก้ OPENROUTER_API_KEY ใน .env"
echo "  2. แก้ TELEGRAM_BOT_TOKEN ใน .env"
echo "  3. รีสตาร์ท services: systemctl restart atsawin-api atsawin-telegram-bot"
echo "  4. ติดตั้ง MT5 EA: คัดลอก ea/AtsawinEA.mq5 → MT5/Experts/"
echo ""
echo -e "${GREEN}ขอให้สนุกกับการเทรด! 🚀${NC}"
