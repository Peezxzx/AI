# Architecture Snapshot (Autonomous Control)

Last updated: 2026-06-01
Workspace: C:/Users/Administrator/repos/AI

## 1) Control Plane (MCP-style)
- Master Controller: Hermes orchestrator (this session)
- Worker roles:
  - Memory Loader
  - Project Scanner
  - Dependency Checker
  - Builder/Optimizer
- Coordination model:
  - Task queue + dependency-aware execution
  - File-backed memory + agent registry
  - Continuous scan -> evaluate -> improve loop

## 2) Runtime Services
- FastAPI backend (backend/main.py)
- Telegram bot integration (backend/telegram_bot.py)
- Trading stack (backend/trading/*)
- Event system (backend/event_system/*)
- System resource manager (backend/system/*)
- Autonomous coding pipeline (backend/pipeline/*)
- MT5 bridge layer (backend/trading/mt5_api.py + ea/atsawin_bridge.py + EA .mq5)

## 3) Data & Infra
- PostgreSQL + Redis expected (docker-compose.yml)
- .env-driven secrets/config
- Dockerfile runtime targets Python 3.12

## 4) Current Risks
- Missing .env.example template
- Missing docker command on current host
- requirements.txt missing some imported libs (aiohttp, psutil, PyMuPDF)
- Local Python runtime is 3.14.5, while container runtime is 3.12

## 5) Next Architecture Actions
1. Add/normalize environment template files
2. Reconcile dependency manifest with imports
3. Standardize local dev runtime (prefer Python 3.12 for parity)
4. Add autonomous task queue + scheduled health/dependency scans
