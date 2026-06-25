# ATSAWIN AI CORE SPEC

# Architecture

## Current Architecture (Phase 1-4 Complete)
Ubuntu VPS
├── FastAPI Backend (Port 8000)
│   ├── Authentication System (JWT + RBAC)
│   ├── Multi-Agent Coordinator
│   ├── Memory Manager (PostgreSQL + Redis)
│   ├── Model Router
│   ├── AI Client (OpenRouter)
│   ├── Hermes Integration
│   ├── System Resource Manager
│   │   ├── Task Scheduling
│   │   ├── Resource Monitoring
│   │   ├── Load Balancing
│   │   └── System Manager
│   ├── Event System & Message Queue
│   ├── Autonomous Coding Pipeline
│   │   ├── Project Scanner
│   │   ├── Code Quality Analyzer
│   │   ├── Git Integration
│   │   ├── CI/CD Pipeline
│   │   └── Test Runner
│   ├── Trading AI Infrastructure
│   │   ├── Market Data (Binance API)
│   │   ├── Technical Analysis (SMA, EMA, RSI, MACD, BB, ATR, Stochastic)
│   │   ├── Backtesting Engine
│   │   ├── Risk Management
│   │   └── Portfolio Management
│   ├── File Analysis (Text + Image + PDF)
│   └── System API Endpoints
├── Docker Infrastructure
│   ├── PostgreSQL (Port 5433)
│   └── Redis (Port 6380)
├── Telegram Bot Interface
│   ├── Text Messages
│   ├── File Upload (Code + Docs)
│   ├── Image Analysis (Vision AI)
│   └── Trading Commands
└── Multi-Agent System
    ├── Coding Agent
    ├── Trading Agent
    ├── Monitoring Agent
    ├── Research Agent
    └── Coordination Agent

---

## Target Architecture (Full AI Operating System)

### Core Layer
├── System Resource Manager ✅
├── Event System & Message Queue ✅
├── Process Scheduler & Orchestration ✅
├── Fault Tolerance & Recovery
└── Service Discovery & Load Balancing

### AI Layer
├── Multi-Agent Coordination Enhanced ✅
├── Autonomous Coding Pipeline ✅
├── Trading AI Infrastructure ✅
├── Advanced Memory System (In Progress)
└── Model Management & Fine-tuning

### Data Layer
├── PostgreSQL (Primary) ✅
├── Redis (Cache) ✅
├── Vector Database (Semantic Memory) - Planned
├── Time-Series Database (Market Data) - Planned
└── Graph Database (Knowledge Graph) - Planned

### Infrastructure Layer
├── Kubernetes Orchestration - Planned
├── Service Mesh (Istio/Linkerd) - Planned
├── Monitoring (Prometheus + Grafana) - Planned
├── Logging (ELK Stack) - Planned
└── Security (OAuth2 + RBAC) ✅

---

## Current Goal

Build scalable AI operating system with autonomous coding pipeline, memory system, trading AI, multi-agent architecture, and a Telegram-friendly virtual office command center UI.

**Status**: Phase 4 Complete - All core infrastructure operational; Virtual Office prototype active in `frontend/virtual-office.html`. Local OS Core started: `backend/office_store.py` persists MT5/EA journal, commands, approval queue, and daily brief data in SQLite.

**Operational note 2026-06-04**: FastAPI local server responds on `127.0.0.1:8000` and `/api/office/status` is usable for read-only dashboard/dev. PostgreSQL `5433` and Redis `6380` are not open on this Windows host, Docker is unavailable, and a status snapshot reported CPU at 100%; treat the server layer as local/dev-ready, not production-ready, until process supervision/resource monitoring/DB-cache plan are cleaned up.

### Frontend / Virtual Office State (2026-06-03)
- `frontend/virtual-office.html` is a self-contained Benz Command Center prototype.
- Layout follows the supplied Benz Office / Trading Cafe reference: left sidebar, top integration bar, central pixel/isometric Agent Live Map, right Team Chat.
- Pages implemented: Office Overview, Chat Center, Characters, Approval Board, Journal/SOP, Daily Brief, Settings.
- Telegram Mini App responsive mode uses bottom tabs and safe-area viewport handling.
- Frontend now displays Local OS Core widgets:
  - Office Overview shows journal counters, Daily Brief Agent, and Approval Queue.
  - Approval Board uses backend approve/reject endpoints.
  - Journal/SOP shows SQLite journal counters.
  - Daily Brief shows recommendation and skip reason table.
- Backend Local OS Core active:
  - `GET /api/office/status` returns live MT5/EA/system status plus `journal`, `daily_brief`, and `approvals`.
  - `POST /api/office/command` stores command audit records, queues risky actions for owner approval, and returns read-only task-engine replies for status/brief/approval-list commands.
  - `GET /api/office/brief` returns a trading coach style daily brief.
  - `GET/POST /api/office/approvals` endpoints support approval/reject status updates without executing risky actions.

---

## Current State

### Completed (Phase 1 - 2026-05-17)
- Ubuntu installed
- Docker installed
- Project structure initialized
- FastAPI backend with all core endpoints
- JWT authentication system with role-based access
- Multi-agent coordinator with 5 specialized agents
- PostgreSQL + Redis memory system
- Model routing system (GLM 4.5 Air, DeepSeek V3, Hy3, Owl Alpha)
- Telegram bot integration
- Docker-compose setup

### Completed (Phase 2 - 2026-05-17)
- System Resource Manager with task scheduling
- Resource monitoring and optimization
- System Manager for component coordination
- REST API endpoints for system management
- Health monitoring and alerts
- Task lifecycle management
- Load balancing and resource allocation
- Event System & Message Queue

### Completed (Phase 3 - 2026-05-17)
- Autonomous Coding Pipeline orchestrator
- Project scanner (file/language/dependency analysis)
- Code quality analyzer (syntax, style, complexity, security)
- Git integration (status, commit, branch, log, diff)
- CI/CD pipeline (lint, test, build, deploy stages)
- Test runner (pytest integration with coverage)
- Pipeline API endpoints

### Completed (Phase 4 - 2026-05-17)
- Trading AI Infrastructure: Market data, analysis, backtest, risk, portfolio
- Telegram Bot: python-telegram-bot 22.7, connected to FastAPI backend
- File upload support (text files + images + PDF)
- Vision AI integration (3 vision models)
- systemd services for FastAPI + Telegram bot (auto-restart)
- API key authentication for bot-to-backend communication

### In Progress (Phase 5 - 2026-05-18)
- Advanced Memory System (semantic search, vector DB)
- System documentation and log updates
- Production hardening

### Phase 5.5 — MT5 EA System (2026-05-18)
- Python EA Bridge (atsawin_bridge.py) — composite signal → JSON file
- MT5 EA (AtsawinEA.mq5) — read JSON signal → execute on MT5
- File-based bridge: Python writes → MT5 reads on new bar
- Config: symbols, risk%, SL/TP, position sizing, spread filter
- 6 strategies composite: SMA crossover, RSI, MACD, Bollinger, Stochastic+RSI, ATR trend

### Phase 5.6 — Continuous Bug Fix & Optimization (2026-06-01 → 2026-06-02)
- Builder Agent cron job running autonomous bug fixes
- Fixed: calculate_stochastic() tuple iteration bug in analysis.py
- Fixed: CONFIG defaults stale after autotune — synced ema_fast 12→30, atr_sl_mult 1.8→2.0
- Fixed: sig_threshold double-penalty bug — now accounts for both chop_penalty and session_out_penalty
- Fixed: autotune/walkforward grid stale — added ema_fast=30 and atr_sl_mult=2.0 to search grids to match proven-best params
- Signal quality: winrate 34.5%, pnl_r=-5.0 (best autotune result), skipped=1220/1470 bars
- Remaining: high skipped rate due to session filter + chop regime, walk-forward inconsistent
- Bridge/EA safety contract v2.1 (2026-06-02): bridge writes ASCII-safe JSON with signal_id/setup_key, timestamp_epoch/expires_at_epoch, symbol/mt5_symbol; EA v3.24 polls every 30s, blocks stale/duplicate executed signal_id, writes ea_runtime_status.json, and compiles 0 errors/0 warnings.
- Bridge concurrency lock (2026-06-02): PID-based file lock at atsawin/bridge_mt5_pro.lock prevents duplicate bridge instances from running simultaneously, eliminating conflicting signal writes and wasted MT5 API slots.
|- Session optimization safety guard (2026-06-03): added session_opt_min_hours=5 and session_opt_min_pnl_r=-2.0 floors to prevent optimize_session_hours_from_trade_log() from shrinking the session window below 5 hours or accepting negative-PnL configurations; live bridge main loop also resets to default if session hours fall below floor.
|- Error recovery + Desktop sync (2026-06-03): restored max_consecutive_errors=10 loop in main() to prevent bridge crash on transient MT5 API errors; synced repo copy to Desktop (was 128 lines behind, missing lock + session safety + atomic write retry); killed duplicate bridge instances.
- Bridge symbol_info() None guard (2026-06-03): scan_once() now guards against mt5.symbol_info() returning None before accessing .point — prevents AttributeError crash that would eventually shut down bridge after 10 consecutive errors during MT5 reconnection/symbol refresh.
- Repo root bridge sync (2026-06-03): synced repo root bridge_mt5_pro.py with ea/ copy — was 119 lines behind, missing lock mechanism, session safety floors, error recovery loop, and symbol_info guard; all three copies (repo root, ea/, Desktop) now identical at 1323 lines.
- FVG/Fib/RSI bridge strategy v2.4 (2026-06-03): user-authored PDF strategy concepts are now integrated in Python bridge first (EA execution unchanged). Signal schema/source `2.4` / `bridge_mt5_pro_v2.4_fvg_fib_rsi`; metadata includes FVG zone, PDF Fibonacci ratios, RSI divergence, and score_breakdown. Latest verification: 19 tests passed, backtest `trades=1128 wins=564 losses=564 winrate=50.0% pnl_r=242.87 skipped=72`; contract documented in `contracts/mt5_signal_v2_4.md`.
- Desktop bridge sync + ea_status metadata recovery (2026-06-03): `_diag_signal.py` showed `ea_status.json` was missing `fib_nearest_ratio/level/distance` and `rsi_divergence` — repo/ea copies had them but Desktop deployed copy was stale. Added 4 missing fields to Desktop `bridge_mt5_pro.py`. All 3 copies (repo, ea/, Desktop) now in sync. 58 tests passed.
- EMA bias test import fix (2026-06-04): `tests/test_ema_bias_fix.py` had `generate_signal` only imported inside `if __name__=="__main__":` block, causing `NameError` when pytest collected the module. Added `generate_signal` to module-level import. 4 tests now pass, full suite 75/75.
- Desktop bridge status dict resync (2026-06-04): Desktop `bridge_mt5_pro.py` was 1620 lines vs repo 1631 lines — missing 11 status dict fields (contract, confirm_timeframe, entry_price, stop_loss, take_profit, atr, rsi, ema_fast, ema_slow, timestamp, timestamp_epoch). Desktop file was last modified at 03:22 while repo was updated at 05:38. Synced all three copies (repo root, ea/, Desktop) — all now 1631 lines, byte-identical. 58 ea tests + 17 root tests passed.
- calc_position_size silent fallback fix (2026-06-04): `calc_position_size()` had 3 silent fallback paths returning 0.01 min lot — most impactful when `tick_value`/`tick_size` is 0 (common for Exness XAUUSDm). Added fallback `tick_value=point*100, tick_size=point` so position size is computed from actual risk parameters instead of silently returning 0.01. All fallback paths now emit `log.warning`. Synced all 3 copies (repo root, ea/, Desktop) — all now 1907 lines, byte-identical. 65 ea tests + 17 root tests passed. Validation: with balance=10000 and tick=0, OLD=0.01 → NEW=0.09 (proper risk-based sizing).
- Session optimization statistical significance guard (2026-06-05): `optimize_session_hours_from_trade_log()` was accepting trade logs with as few as 12 total trades (3/hour × 4 hours), causing wildly inconsistent session hour selections (e.g., [0,1,5,10,13,14] → [0,1,2,3,4,5] → back). Raised `min_trades_per_hour` default from 3→10, added `min_total_trades=50` guard, added CONFIG entries `session_opt_min_trades_per_hour` and `session_opt_min_total_trades`. Updated `--optimize-session` handler to read from CONFIG. Updated existing tests to use sufficient data. Synced all 3 copies (repo root, ea/, Desktop). 69 ea tests + 14 root tests + 4 new validation tests passed.

---

## Models

- GLM 4.5 Air (z-ai/glm-4.5-air:free) - cheap/fast tasks
- DeepSeek V3 (deepseek/deepseek-chat-v3) - reasoning/analysis
- Hy3 (tencent/hunyuan) - planning
- Owl Alpha (openrouter/owl-alpha) - coding
- Vision Primary (nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free) - image analysis
- Vision Alt (qwen/qwen-2-vl-7b-instruct:free) - lighter vision, good Thai
- Vision Mini (google/gemini-2.0-flash-lite-001:free) - fastest vision

---

## Implementation Roadmap

### Phase 1 ✅ (Completed - 2026-05-17)
- Basic infrastructure setup
- Authentication system
- Multi-agent framework
- Memory system
- Model routing
- Telegram integration

### Phase 2 ✅ (Completed - 2026-05-17)
- System Resource Manager
- Task scheduling and optimization
- System Manager coordination
- Health monitoring
- Resource allocation
- System API endpoints

### Phase 3 ✅ (Completed - 2026-05-17)
- Enhanced multi-agent communication
- Autonomous Coding Pipeline
- Project scanner, code quality analyzer
- Git integration, CI/CD pipeline, test runner

### Phase 4 ✅ (Completed - 2026-05-17)
- Trading AI Infrastructure (market data, analysis, backtest, risk, portfolio)
- Telegram Bot file upload (text + image + PDF)
- Vision AI with 3 models
- systemd services with auto-restart

### Phase 5 🚀 (In Progress - Start 2026-05-18)
- Advanced Memory System (semantic search)
- Vector database integration
- Production monitoring (Prometheus/Grafana)
- API rate limiting
- Enhanced error handling and logging

### Phase 6 📋 (Planned)
- Kubernetes orchestration
- Service mesh
- ELK stack logging
- Advanced trading strategies
- Web dashboard

---

## Architecture Principles

1. **Modular Design**: Each component independently deployable
2. **Scalability**: Horizontal scaling for all services
3. **Resilience**: Fault tolerance and graceful degradation
4. **Observability**: Comprehensive monitoring and logging
5. **Security**: End-to-end encryption and access control

---

## Development Workflow

1. Analyze current architecture
2. Identify missing components
3. Implement modular improvements
4. Validate functionality
5. Update memory state (spec.md, hot.md, architecture.md, system_state.md)
6. Suggest next steps

## Autonomous Brain Workflow (MCP-style)
- Memory-first execution: load/update spec.md, architecture.md, system_state.md, hoting_old_knowledge.md before major tasks.
- Maintain agent registry and role map for helper agents.
- Maintain task queue with dependencies and execution order.
- Perform periodic workspace scans and dependency drift checks.
- Capture durable lessons in hoting_old_knowledge.md and keep spec/architecture synchronized.

---

## Key Metrics

### Technical Metrics
- System Uptime: 99.9%+
- Response Time: <100ms
- Throughput: 10,000+ requests/sec
- Error Rate: <0.1%
- Memory Efficiency: <2GB per agent

### Business Metrics
- Task Success Rate: 95%+
- Agent Coordination Efficiency: 90%+
- Trading Signal Accuracy: 85%+
- Code Quality Score: 90%+

---

## System Resource Manager Features

### Task Management
- Priority-based task scheduling
- Resource-aware task allocation
- Task lifecycle tracking
- Automatic cleanup and optimization

### Resource Monitoring
- Real-time CPU, memory, disk, network monitoring
- Historical usage tracking
- Alert system for resource limits
- Automatic optimization

### System Coordination
- Component registration and management
- Cross-component communication
- Fault tolerance and recovery
- Load balancing

### API Endpoints
- `/system/status` - System status
- `/system/resources/history` - Resource history
- `/system/tasks/*` - Task management
- `/system/manager/*` - System manager control
- `/system/health` - Health monitoring

## Autonomous Coding Pipeline Features

### Pipeline Orchestration
- Multi-phase execution: scan, plan, code, validate, update memory
- Dry-run mode for validation
- Progress tracking and error reporting
- File action support: create, modify, append, patch, delete

### Project Scanner
- File and directory analysis
- Language detection and line counting
- Dependency discovery
- Structure analysis (depth, largest files)

### Code Quality Analyzer
- Syntax checking (AST-based)
- Style checks (line length, trailing whitespace, TODO format)
- Cyclomatic complexity analysis
- Security scanning (eval, exec, hardcoded secrets, SSL)
- Code duplication detection

### Git Integration
- Repository status tracking
- Commit creation with optional push
- Branch creation and checkout
- Commit log and diff viewing

### CI/CD Pipeline
- Multi-stage execution: lint, test, build, deploy
- Environment-aware (development, staging, production)
- Async execution with status tracking
- Production safety checks

### Test Runner
- pytest integration with auto-discovery
- Coverage reporting
- Parallel test execution
- Multiple test types: unit, integration, e2e

## Trading AI Features

### Market Data
- Real-time price from Binance API
- Candlestick data (klines) with multiple timeframes
- Order book depth
- 24h ticker statistics
- Available symbols listing

### Technical Analysis
- SMA, EMA, RSI, MACD, Bollinger Bands, ATR, Stochastic
- Composite trading signal (BUY/SELL/HOLD) with confidence
- Multi-indicator summary

### Backtesting
- SMA crossover strategy (default)
- Configurable parameters (capital, position size, stop loss, take profit)
- Performance metrics (Sharpe, drawdown, win rate, profit factor)
- Equity curve and trade history

### Risk Management
- Position sizing based on risk percentage
- Stop loss / take profit calculation (ATR-based)
- Risk assessment per symbol
- Configurable risk limits

### Portfolio
- Track open positions (long/short)
- Real-time PnL calculation
- Position add/close/reset

## Telegram Bot Features

### Commands
- `/start` - Welcome message
- `/help` - Usage instructions
- `/ask <question>` - Ask AI
- `/status` - System status
- `/price <symbol>` - Crypto price
- `/signal <symbol>` - Trading signal
- `/portfolio` - Portfolio status

### File Support
- Text files: .py, .js, .ts, .json, .html, .css, .md, .csv, .sh, .sql, etc.
- Images: .jpg, .png, .gif, .webp (vision AI analysis)
- PDF: text extraction + AI analysis
- Max file size: 10MB
- Caption as question when sending files

### Vision AI
- Auto-detects image-related questions
- 3 vision models: primary (nvidia/nemotron), alt (qwen-2-vl), mini (gemini-flash-lite)
- Base64 encoding for API transmission
