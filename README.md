# 🤖 Atsawin AI Operating System

ระบบ AI อัตโนมัติครบวงจร — FastAPI Backend + Telegram Bot + Trading AI + MT5 EA

---

## 📋 สิ่งที่ระบบทำได้

| ระบบ | อธิบาย |
|------|--------|
| **FastAPI Backend** | REST API พร้อม JWT Auth, RBAC, Multi-Agent Coordinator |
| **Trading AI** | 6 กลยุทธ์ (SMA, RSI, MACD, Bollinger, Stochastic+RSI, ATR), Backtest, Risk Management |
| **Telegram Bot** | แชทกับ AI, ดูราคา, ดูสัญญาณ, อัพโหลดไฟล์/รูป |
| **MT5 EA** | อ่านสัญญาณจาก Python → Execute บน MT5 พร้อม SL/TP |
| **Auto Pipeline** | สแกนโปรเจค, วิเคราะห์ code, CI/CD, รัน test |
| **Event System** | Message queue, pub/sub, event routing |
| **Memory System** | PostgreSQL + Redis cache |

---

## 🏗️ โครงสร้างโปรเจกต์

```
/root/AI/
├── backend/                  # FastAPI Backend
│   ├── main.py              # Entry point
│   ├── router.py            # API router
│   ├── ai_client.py         # OpenRouter AI client
│   ├── config.py            # Configuration
│   ├── models.py            # Database models
│   ├── memory.py            # Memory management
│   ├── memory_manager.py    # Memory manager
│   ├── multi_agent_coordinator.py
│   ├── hermes_integration.py
│   ├── telegram_bot.py      # Telegram bot
│   ├── requirements.txt
│   ├── auth/                # JWT Authentication
│   │   ├── auth_utils.py
│   │   ├── endpoints.py
│   │   ├── models.py
│   │   └── user_database.py
│   ├── trading/             # Trading AI
│   │   ├── market_data.py   # Binance API
│   │   ├── analysis.py      # Technical indicators
│   │   ├── strategy_engine.py   # 6 strategies
│   │   ├── signal_generator.py  # Composite signal
│   │   ├── auto_executor.py     # Paper trading
│   │   ├── backtest.py      # Backtesting
│   │   ├── risk.py          # Risk management
│   │   ├── portfolio.py     # Portfolio tracker
│   │   ├── router.py        # Trading API endpoints
│   │   ├── models.py        # Trading data models
│   │   └── trading_agent.py # Trading agent
│   ├── event_system/        # Event system
│   │   ├── event_processor.py
│   │   ├── event_publisher.py
│   │   ├── event_router.py
│   │   ├── event_subscriber.py
│   │   ├── event_system_manager.py
│   │   ├── endpoints.py
│   │   └── models.py
│   ├── system/              # System resource manager
│   │   ├── resource_manager.py
│   │   ├── manager.py
│   │   └── endpoints.py
│   └── pipeline/            # Autonomous coding pipeline
│       ├── engine.py
│       ├── scanner.py
│       ├── quality.py
│       ├── git_manager.py
│       ├── cicd.py
│       ├── testing.py
│       ├── router.py
│       └── models.py
├── ea/                      # MT5 EA System
│   ├── atsawin_bridge.py    # Python signal generator
│   └── AtsawinEA.mq5        # MT5 Expert Advisor
├── ai_core/                 # AI Core agents
│   └── agents/
│       ├── coordinator.py
│       ├── coding_agent.py
│       ├── code_quality.py
│       ├── project_scanner.py
│       ├── git_integration.py
│       ├── cicd_pipeline.py
│       ├── automated_testing.py
│       ├── task_manager.py
│       ├── state_manager.py
│       ├── conflict_resolution.py
│       ├── enhanced_agent.py
│       └── communication/
├── pipeline/                # Pipeline modules
│   ├── pipeline.py
│   ├── code_writer.py
│   ├── project_scanner.py
│   ├── task_manager.py
│   ├── memory_updater.py
│   └── logger.py
├── agents/
│   └── telegram_agent.py
├── memory/                  # Memory storage
│   ├── chat/
│   ├── projects/
│   └── tasks/
├── AI/                      # AI knowledge base
│   ├── contracts/
│   ├── knowledge/
│   ├── logs/
│   ├── reports/
│   ├── scratch/
│   └── sessions/
├── docker-compose.yml       # Docker setup
├── Dockerfile
├── .env.example             # Environment template
├── spec.md                  # Architecture spec
├── hot.md                   # Active state
└── CLAUDE.md                # Development rules
```

---

## 🚀 วิธีติดตั้ง

### วิธีที่ 1: ติดตั้งอัตโนมัติ (แนะนำ)

```bash
git clone git@github.com:Peezxzx/AI.git
cd AI
chmod +x install.sh
./install.sh
```

### วิธีที่ 2: ติดตั้งเองทีละขั้น

#### 1. เตรียม Environment

```bash
# Copy env template
cp .env.example .env

# แก้ไข .env ใส่ค่าจริง
nano .env
```

**ต้องใส่:**
- `OPENROUTER_API_KEY` — API key จาก [openrouter.ai](https://openrouter.ai)
- `TELEGRAM_BOT_TOKEN` — Bot token จาก @BotFather
- `POSTGRES_PASSWORD` — Password สำหรับ PostgreSQL
- `JWT_SECRET_KEY` — Secret key สำหรับ JWT

#### 2. ติดตั้ง Docker (ถ้ายังไม่มี)

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
```

#### 3. รัน Backend

```bash
# วิธีที่ 1: Docker (แนะนำ)
docker-compose up -d

# วิธีที่ 2: รันตรงๆ
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

#### 4. รัน Telegram Bot

```bash
cd backend
source venv/bin/activate
python telegram_bot.py
```

#### 5. รัน MT5 EA Bridge

```bash
cd ea
pip install aiohttp
python atsawin_bridge.py
```

#### 6. ติดตั้ง MT5 EA

1. คัดลอก `ea/AtsawinEA.mq5` ไปที่ `MQL5/Experts/` ใน MT5 Terminal
2. Compile ใน MetaEditor
3. ลาก EA ไปที่ chart
4. ตั้งค่า input parameters ตามต้องการ

---

## ⚙️ การตั้งค่า

### Environment Variables (.env)

```env
# AI
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxx

# Telegram
TELEGRAM_BOT_TOKEN=123456:ABC-DEF

# Database
POSTGRES_USER=atsawin
POSTGRES_PASSWORD=your_password
POSTGRES_DB=atsawin_db
POSTGRES_HOST=localhost
POSTGRES_PORT=5433

# Redis
REDIS_HOST=localhost
REDIS_PORT=6380

# Security
JWT_SECRET_KEY=your-secret-key-change-this
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440

# API
API_KEY=atsawin-ea-bridge-key
```

### MT5 EA Parameters

| Parameter | Default | อธิบาย |
|-----------|---------|--------|
| InpSignalFile | atsawin\latest_signal.json | ไฟล์สัญญาณ |
| InpMagicNumber | 20250518 | Magic number |
| InpRiskPercent | 2.0 | Risk % ต่อเทรด |
| InpMaxLot | 1.0 | Lot สูงสุด |
| InpMinLot | 0.01 | Lot ต่ำสุด |
| InpMaxSpreadPt | 30 | Spread สูงสุด (points) |
| InpMaxOpenTrades | 3 | จำนวนเทรดสูงสุด |
| InpMinConfidence | 0.5 | ความมั่นใจขั้นต่ำ |
| InpSignalExpiry | 60 | อายุสัญญาณ (นาที) |

### Python Bridge Config

แก้ไขใน `ea/atsawin_bridge.py` → `CONFIG` dict:

```python
CONFIG = {
    "api_url": "http://localhost:8000",  # FastAPI URL
    "api_key": "atsawin-ea-bridge-key",   # ตรงกับ API_KEY ใน .env
    "capital": 10000.0,                   # เงินทุน
    "symbols": ["BTCUSD", "ETHUSD"],      # สินค้า
    "timeframe": "H1",                    # ไทม์เฟรม
    "scan_interval": 300,                 # สแกนทุก 5 นาที
    "min_confidence": 0.5,
    "min_risk_reward": 1.5,
}
```

---

## 📡 API Endpoints

### Authentication
| Method | Endpoint | อธิบาย |
|--------|----------|--------|
| POST | `/auth/register` | สมัครสมาชิก |
| POST | `/auth/login` | เข้าสู่ระบบ |
| GET | `/auth/me` | ข้อมูลผู้ใช้ |

### Trading
| Method | Endpoint | อธิบาย |
|--------|----------|--------|
| GET | `/trading/market/price` | ราคาปัจจุบัน |
| GET | `/trading/market/data` | ข้อมูลแท่งเทียน |
| GET | `/trading/market/ticker` | ข้อมูล 24 ชม. |
| POST | `/trading/analysis/indicators` | คำนวณ indicators |
| GET | `/trading/analysis/signal` | สัญญาณการเทรด |
| POST | `/trading/backtest/run` | รัน backtest |
| GET | `/trading/backtest/results/{id}` | ผล backtest |
| GET | `/trading/risk/assessment` | ประเมินความเสี่ยง |
| GET | `/trading/portfolio` | พอร์ตโฟลิโอ |

### EA (Enhanced Agent)
| Method | Endpoint | อธิบาย |
|--------|----------|--------|
| POST | `/trading/ea/strategies/analyze` | วิเคราะห์ multi-strategy |
| POST | `/trading/ea/signal/recommendation` | คำแนะนำเทรด |
| GET | `/trading/ea/executor/state` | สถานะ executor |
| POST | `/trading/ea/executor/scan` | สแกนสัญญาณ |

### System
| Method | Endpoint | อธิบาย |
|--------|----------|--------|
| GET | `/system/status` | สถานะระบบ |
| GET | `/system/health` | Health check |
| GET | `/system/resources/history` | ประวัติ resource |

---

## 🔄 การอัพเดท

```bash
# Pull โค้ดล่าสุด
cd /root/AI
git pull

# รันใหม่
docker-compose up -d --build
```

---

## 🛡️ ความปลอดภัย

- API keys เก็บใน `.env` (ไม่ commit ขึ้น git)
- JWT authentication สำหรับ API
- Role-based access control (RBAC)
- GitHub push protection ป้องัน secret leakage

---

## 📝 License

MIT License — ใช้ได้อิสระ

---

## 👨‍💻 ผู้พัฒนา

สร้างโดย Atsawin AI Operating System — ระบบ AI อัตโนมัติครบวงจร
