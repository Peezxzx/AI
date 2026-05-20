# HOT MEMORY

## Current Task
Fixing MT5 EA + Python Bridge bugs for Atsawin AI Trading System.

---

## Session 2026-05-20: MT5 EA Bug Fix Session

### Bugs Found & Fixed

#### Python Bridge (atsawin_bridge.py)
1. **aiohttp not installed** — `pip install aiohttp` in global Python
2. **sym_to_mt5() dict comprehension bug** — `{v:k for k,v in CONFIG["sym_map"]}` missing `.items()` → iterate chars instead of key-value pairs → ValueError
3. **API error handling** — No retry logic, no timeout handling → added `api_request()` with 3 retries + exponential backoff
4. **Fallback signal path** — When `/trading/ea/scan` returns empty, fallback to `/trading/analysis/signal` + calculate SL/TP from price
5. **SL/TP = 0** — Fallback signal had no SL/TP → added price fetch + 2%/3% SL/TP calculation
6. **min_confidence too high** — Default 0.5 filtered all signals → lowered to 0.3 for testing
7. **Health check** — Added `--health` flag for API connectivity check
8. **Bridge running** — Started in background (PID 66286), scans every 5 min

#### MQL5 EA (AtsawinEA.mq5)
1. **FolderCreate nested** — `FolderCreate("MQL5\\Files\\atsawin")` fails if parent doesn't exist → create step by step
2. **ORDER_FILLING_IOC** — Some brokers don't support IOC → fallback chain: IOC → FOK → RETURN
3. **Signal expiry parse** — `StringToTime()` can't parse ISO 8601 format → added `ParseISOTime()` function
4. **Version bump** — v1.1 → v1.2

### Service File
- Created `/root/Atsawin-AI-Core/ea/atsawin-bridge.service` (systemd)
- Need sudo to install: `sudo cp ... && sudo systemctl enable --now atsawin-bridge`

### Signal File Format (v1.2)
```json
{
  "version": "1.2",
  "signal": "sell",
  "symbol": "BTCUSD",
  "timeframe": "1h",
  "confidence": 0.333,
  "entry_price": 76651.65,
  "stop_loss": 78184.68,
  "take_profit": 74352.1,
  "risk_reward_ratio": 1.5,
  "timestamp": "2026-05-20T01:31:24.186312+00:00"
}
```

### Known Issues
- XAUUSDT → API returns 500 error (slice bug in market data)
- Signal confidence currently low (0.33) — market conditions
- Bridge needs sudo to install as systemd service

---

### ✅ Running Services (All Persistent)
- **FastAPI Backend**: systemd service `atsawin-api.service` (port 8000) - Restart=always
- **Telegram Bot**: systemd service `atsawin-telegram-bot.service` - Restart=always, uses venv python
- **PostgreSQL**: Docker container `atsawin-postgres` (port 5433) - Restart=unless-stopped
- **Redis**: Docker container `atsawin-redis` (port 6380) - Restart=unless-stopped

### 🔧 Latest Changes (2026-05-17 18:20-18:39)
1. **Added file upload support to Telegram bot**
   - `handle_document()` - handles document/file uploads (.py, .js, .json, .md, etc.)
   - `handle_photo()` - handles photo/image uploads (.jpg, .png, .gif, .webp)
   - Both download from Telegram and send to FastAPI for AI analysis
   - Supports caption as question when sending files
2. **Added `/api/file-analyze` endpoint to FastAPI**
   - Accepts file upload + optional question via API key auth
   - Text files: reads content, sends to AI for analysis (max 8000 chars)
   - Images: sends to vision model (nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free)
   - Max file size: 10MB
3. **Added `ask_ai_vision()` function to ai_client.py**
   - Supports vision-capable models via base64 image encoding
4. **Installed aiohttp** in venv for async HTTP requests from bot to backend
5. **Updated /start and /help** messages to include file upload instructions

### ✅ All Services Now Persistent
- All 4 core services have auto-restart configured
- System survives reboots and crashes

---

## Active Development
- Currently working on Advanced Memory System
- Next: Production Infrastructure (K8s, monitoring)

---

## Session 2026-05-18: Desktop GUI Environment
- Installed + optimized XFCE4 desktop for VPS
- XRDP remote desktop on port 3389 (TLS secured)
- Optimizations: compositor off, 16bpp, no multimon, max 5 sessions
- Apps: xfce4-terminal, thunar, mousepad, ristretto, xfce4-taskmanager, xfce4-screenshooter, network-manager-gnome, firefox
- xrdp + xrdp-sesman both active and running
- Memory: 3.8GB total, ~2.9GB available after GUI install
- Disk: 46GB free (21% used)
- Connect via RDP: server-ip:3389, login with system username/password

## Session 2026-05-19: Thai Language Support for XFCE/XRDP
- Installed Thai fonts: Noto Sans Thai, Noto CJK, full TLWG font set (Garuda, Kinnari, Laksaman, Loma, Mono, Norasi, Purisa, Sawasdee, Typewriter, Typist, Typo, Umpush, Waree)
- Generated locale: th_TH.UTF-8
- Installed IBus Thai input methods: ibus-libthai (LibThai engine) + ibus-m17n (m17n engine)
- Configured IBus auto-start in XRDP session via /etc/xrdp/startwm.sh
- Set environment variables: GTK_IM_MODULE=ibus, QT_IM_MODULE=ibus, XMODIFIERS=@im=ibus
- Configured XFCE keyboard layout: US + Thai with Alt+Shift toggle
- Set system locale: LANG=en_US.UTF-8, LC_CTYPE=th_TH.UTF-8
- Created IBus autostart entries (system-wide + per-user)
- Created XFCE xsettings with GTK IM Module = ibus
- Keyboard shortcut: Alt+Shift to switch between English and Thai
- IBus panel icon visible in system tray for input method selection
- Restarted xrdp + xrdp-sesman services to apply changes

---

## Recent Achievements
- ✅ Fixed all import errors preventing FastAPI from starting
- ✅ Created systemd service for FastAPI with auto-restart
- ✅ System now runs persistently (survives restarts)
- ✅ Added file upload & analysis via Telegram (text + images)

## Notes
- FastAPI service: `/etc/systemd/system/atsawin-api.service`
- Telegram bot token stored in `.env` (masked in logs)
- PostgreSQL password: `password123`
- Vision models: nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free (primary), qwen/qwen-2-vl-7b-instruct:free (alt), google/gemini-2.0-flash-lite-001:free (mini)
- Vision keywords: image, photo, picture, รูป, ภาพ, vision, see, look, scan, screenshot, camera, หน้าจอ, diagram, chart, graph, ใบหน้า, วิเคราะห์รูป, อธิบายรูป, บนรูป, ในรูป
- New functions: get_vision_model(prefer), list_models()
- Keep architecture modular and scalable

## Session 2026-05-18: MT5 EA System
- Created 2-file EA system: atsawin_bridge.py + AtsawinEA.mq5
- Python bridge: scans composite signal from Trading API → writes latest_signal.json
- MT5 EA: reads JSON on new bar → executes buy/sell with SL/TP
- File-based bridge (atomic write to prevent corruption)
- Risk management: position sizing from risk%, spread filter, max trades limit
- Symbol mapping: BTCUSD↔BTCUSDT, ETHUSD↔ETHUSDT, etc.
- Timeframe mapping: H1→1h, M15→15m, etc.
- Config: all parameters in CONFIG dict (Python) / inputs (MQL5)
- Signal filter: min confidence 0.5, min R:R 1.5, expiry 60min
- MQL5 features: JSON parser, lot calculator, PnL tracker, logging to file
- Added 3 vision models to router.py: nvidia/nemotron (primary), qwen-2-vl-7b (alt), gemini-2.0-flash-lite (mini)
- Added VISION_KEYWORDS for auto-routing image-related tasks
- Added get_vision_model() and list_models() helper functions
- Fixed handle_message() to detect vision questions and guide users to send images directly
- Vision flow: Telegram photo → handle_photo() → /api/file-analyze → ask_ai_vision() → vision model
- Text question about images → handle_message() → shows instructions to send image directly
