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

Build scalable AI operating system with autonomous coding pipeline, memory system, trading AI, and multi-agent architecture.

**Status**: Phase 4 Complete - All core infrastructure operational

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
5. Update memory state (spec.md, hot.md)
6. Suggest next steps

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
