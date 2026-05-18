# HOT MEMORY

## Current Task
Building AI Operating System with Trading AI Infrastructure.

---

## Current State Analysis (2026-05-17 18:39:00 UTC)

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
