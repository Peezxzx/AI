# System State

## Daily maintenance check - 2026-06-18 09:02 SEAST
- Host tools: python 3.14.5, pip 26.1.1, uv 0.11.17, git 2.54.0.windows.1, node v22.22.3; docker command missing.
- Memory docs loaded: spec.md, architecture.md, system_state.md, hot.md, hoting_old_knowledge.md, brain/agent_registry.md, brain/task_queue.md.
- backend/requirements.txt present with 17 declarations; backend AST import scan excluding local venv/vendor folders scanned 53 Python files with 0 parse errors.
- Likely undeclared direct third-party imports: `pydantic` (`backend/auth/models.py`, `backend/office_router.py`) and `psycopg2` imports satisfied only indirectly by declared package `psycopg2-binary` (`backend/auth/user_database.py`, `backend/memory_manager.py`).
- MT5 bridge readiness files present: Desktop bridge size 85256, mtime 2026-06-14T07:43:14.248265+07:00; latest signal size 1515, mtime 2026-06-18T09:03:18.696575+07:00.
- Latest signal file parsed OK: contract `atsawin_mt5_signal` v2.4, `sell` for `XAUUSD` / `XAUUSDm`, confidence 1.0, spread 280.0 points, timestamp 2026-06-18T02:03:18.695610+00:00, source `bridge_mt5_pro_v2.4_fvg_fib_rsi`, setup `fvg_fib_rsi`.
- Bridge copy drift still present: repo root and `ea/` bridge files share sha256 `0a383f4d46964ddc0c4de781bd7619fcce064d9bae1c6048ce1bef313afa6fd6`, while Desktop deployed bridge is `3d611ff679ca42002a7b2ddf180eba0784695396ee078ec8e1a1be7b25793de0`.
- Repo root `.env.example` is present again: size 484, mtime 2026-06-01T19:26:58.578005+07:00.

## Daily maintenance check - 2026-06-13 09:02 SEAST
- Host tools: python 3.14.5, pip 26.1.1, uv 0.11.17, git 2.54.0.windows.1, node v22.22.3; docker command missing.
- Memory docs loaded: spec.md, architecture.md, system_state.md, hot.md, hoting_old_knowledge.md, brain/agent_registry.md, brain/task_queue.md.
- backend/requirements.txt present with 17 declarations; backend AST import scan excluding dot/venv folders scanned 53 Python files with 0 parse errors.
- Likely undeclared direct third-party import remains `pydantic` (`backend/auth/models.py`, `backend/office_router.py`).
- MT5 bridge readiness files present: Desktop bridge size 80123, mtime 2026-06-05T15:16:32.298676+07:00; latest signal size 1486, mtime 2026-06-13T09:02:07.210436+07:00.
- Latest signal file parsed OK: contract `atsawin_mt5_signal` v2.4, `buy` for `XAUUSD` / `XAUUSDm`, confidence 1.0, spread 280.0 points, timestamp 2026-06-13T02:02:07.221403+00:00, source `bridge_mt5_pro_v2.4_fvg_fib_rsi`, setup `fvg_fib_rsi`.
- Bridge copy drift still present: repo root and `ea/` bridge files share sha256 `0a383f4d46964ddc0c4de781bd7619fcce064d9bae1c6048ce1bef313afa6fd6`, while Desktop deployed bridge is `9b13965696a86787c54ab6c1651847aecd2b89dbee515c50aa6f4603b1cd14cc`.
- Repo root `.env.example` is currently absent.

## Daily maintenance check - 2026-06-12 09:01 SEAST
- Host tools: python 3.14.5, pip 26.1.1, uv 0.11.17, git 2.54.0.windows.1, node v22.22.3; docker command missing.
- Memory docs loaded: spec.md, architecture.md, system_state.md, hot.md, hoting_old_knowledge.md, brain/agent_registry.md, brain/task_queue.md.
- backend/requirements.txt present with 17 declarations; backend AST import scan excluding dot/venv folders scanned 53 Python files with 0 parse errors.
- Likely undeclared direct third-party import remains `pydantic` (`backend/auth/models.py`, `backend/office_router.py`). `backend` import hits in `backend/main.py` and `backend/office_router.py` are local-package imports, not dependency drift.
- MT5 bridge readiness files present: Desktop bridge size 80123, mtime 2026-06-05T15:16:32.298676+07:00; latest signal size 1318, mtime 2026-06-12T09:01:29.752882+07:00.
- Latest signal file parsed OK: contract `atsawin_mt5_signal` v2.4, `buy` for `XAUUSD` / `XAUUSDm`, confidence 0.695, spread 280.0 points, timestamp 2026-06-12T02:01:29.749810+00:00, source `bridge_mt5_pro_v2.4_fvg_fib_rsi`.
- Bridge copy drift still present: repo root and `ea/` bridge files share sha256 `0a383f4d46964ddc0c4de781bd7619fcce064d9bae1c6048ce1bef313afa6fd6`, while Desktop deployed bridge is `9b13965696a86787c54ab6c1651847aecd2b89dbee515c50aa6f4603b1cd14cc`.

## Daily maintenance check - 2026-06-11 09:01:00 SEAST
- Host tools: python 3.14.5, pip 26.1.1, uv 0.11.17, git 2.54.0.windows.1, node v22.22.3; docker command missing.
- Memory docs loaded: spec.md, architecture.md, system_state.md, hot.md, hoting_old_knowledge.md, brain/agent_registry.md, brain/task_queue.md.
- backend/requirements.txt present with 17 declarations; backend AST import scan excluding dot-directories/venv folders scanned 53 Python files and found one likely undeclared direct third-party import: `pydantic` (`backend/auth/models.py`, `backend/office_router.py`).
- MT5 bridge readiness files present: Desktop bridge size 80123, mtime 2026-06-05 15:16:32 +0700; latest signal size 1319, mtime 2026-06-11 09:00:17 +0700.
- Latest signal file parsed OK: contract `atsawin_mt5_signal` v2.4, `sell` for `XAUUSD`, confidence 0.752, spread 260.0 points, timestamp 2026-06-11T02:03:17.754692+00:00, source `bridge_mt5_pro_v2.4_fvg_fib_rsi`, setup `fvg_fib_rsi`.
- Bridge copy drift still present: repo root and `ea/` bridge files share sha256 `0a383f4d46964ddc0c4de781bd7619fcce064d9bae1c6048ce1bef313afa6fd6`, while Desktop deployed bridge is `9b13965696a86787c54ab6c1651847aecd2b89dbee515c50aa6f4603b1cd14cc`.

Last updated: 2026-06-02 09:06:34 SEAST
Workspace: C:/Users/Administrator/repos/AI

## Runtime availability (host)
- python: installed (3.14.5)
- pip: installed (26.1.1)
- uv: installed (0.11.17)
- git: installed (2.54.0.windows.1)
- node: installed (v22.22.3)
- docker: missing
- docker compose: missing (because docker missing)

## Project dependency state
- Declared requirements file: backend/requirements.txt
- Reconciled declarations added:
  - aiohttp
  - psutil
  - PyMuPDF (imported as fitz)
- Runtime parity note:
  - Host Python: 3.14.5
  - Dockerfile Python: 3.12-slim
  - Recommendation: use Python 3.12 for local parity when possible

## Project memory files
- spec.md: present
- hot.md: present
- architecture.md: present
- system_state.md: present
- hoting_old_knowledge.md: present

## Agent status (current session)
- Memory Loader: completed initial load
- Project Scanner: completed inventory
- Dependency Checker: completed audit + requirements reconciliation
- Builder/Optimizer: completed repo hygiene updates (.env.example + compile validation)

## Immediate blockers
1. Docker not available on host
2. PostgreSQL on localhost:5433 is not reachable during local validation
3. Native PyMuPDF/fitz import still fails in repo .venv on Windows with DLL load failure (`_extra`), but PDF extraction now has a pure-Python `pypdf` fallback
4. MT5 terminal is connected but `terminal_trade_allowed=False` until AutoTrading is enabled/reloaded in MT5 GUI

## Latest local validation (2026-06-01)
- Host health: C: disk 56% used / ~22GB free; CPU load reported 100%; free RAM ~1.5GB of ~6.0GB
- MT5 bridge process active: `C:\Users\Administrator\Desktop\bridge_mt5_pro.py`
- MT5 account reachable: Exness trial login 433684944; XAUUSDm tick OK
- Open XAUUSDm positions at check time: 4 SELL positions, all actual RR > 1.4
- Latest bridge signal: SELL, confidence 0.763, RR 1.56, spread 308 points
- Repo `.venv` uses Python 3.11.15; dependencies synced with `uv pip install -r backend/requirements.txt`
- Selected `py_compile` checks pass for backend core files
- Package imports pass for `backend.main`, `backend.trading.analysis`, `backend.memory_manager`, `backend.event_system.event_system_manager`, `backend.system.endpoints`
- Backend import logs PostgreSQL connection refused on localhost:5433; full API runtime not validated yet

## Readiness watch note (2026-06-02 02:05:58 SEAST)
- Critical files present and `python -m compileall C:/Users/Administrator/repos/AI/backend` passed.
- Blocking state changed: docker is still missing; current cron Python cannot import `uvicorn` even though a Hermes venv uvicorn CLI exists; direct backend import scan shows `pydantic` is imported but not declared in `backend/requirements.txt`.

## Readiness watch - 2026-06-02 08:09:48
Blockers changed: missing docker, missing uvicorn in active Python environment, import not declared in requirements.txt: pydantic, import not declared in requirements.txt: trading. compileall=ok; critical_files=ok.

## Daily maintenance check - 2026-06-02 09:06:34 SEAST
- Host tools: python 3.14.5, pip 26.1.1, uv 0.11.17, git 2.54.0.windows.1, node v22.22.3; docker command missing.
- Memory docs loaded: spec.md, architecture.md, system_state.md, hot.md, hoting_old_knowledge.md, brain/agent_registry.md, brain/task_queue.md.
- backend/requirements.txt present; backend import scan found one likely undeclared direct third-party import: pydantic (auth/models.py).
- MT5 bridge readiness files present: Desktop/bridge_mt5_pro.py (mtime 2026-06-01 23:16:28 +0700) and atsawin/latest_signal.json (mtime 2026-06-02 09:01:56 +0700).
- Latest signal file: sell XAUUSDm, confidence 1.0, RR 1.56, spread 308.0 points, timestamp 2026-06-02T02:00:56.135438+00:00.

## Readiness watch - 2026-06-03 02:17:26 SEAST
Blockers changed: missing docker, missing uvicorn in active Python 3.14.5 environment, import not declared in requirements.txt: pydantic. compileall=ok; critical_files=ok. Previous extra `trading` drift is no longer detected by the local-module-aware scan.

## Daily maintenance check - 2026-06-03 09:03:47 SEAST
- Host tools: python 3.14.5, pip 26.1.1, uv 0.11.17, git 2.54.0.windows.1, node v22.22.3; docker command missing.
- Memory docs loaded: spec.md, architecture.md, system_state.md, hot.md, hoting_old_knowledge.md, brain/agent_registry.md, brain/task_queue.md.
- backend/requirements.txt present; backend import scan excluding local venv folders scanned 53 Python files with 0 parse errors and found one likely undeclared direct third-party import: pydantic (`backend/auth/models.py`, `backend/office_router.py`).
- MT5 bridge readiness files present: Desktop/bridge_mt5_pro.py (size 50400, mtime 2026-06-03 07:00:03 +0700) and atsawin/latest_signal.json (size 725, mtime 2026-06-03 09:01:16 +0700).
- Latest signal file: contract atsawin_mt5_signal v2.1, sell XAUUSDm, confidence 1.0, spread 280.0 points, timestamp 2026-06-03T02:03:16.165469+00:00, source bridge_mt5_pro_v2.1.

## Daily maintenance check - 2026-06-04 09:05:20 SEAST
- Host tools: python 3.14.5, pip 26.1.1, uv 0.11.17, git 2.54.0.windows.1, node v22.22.3; docker command missing.
- Memory docs loaded: spec.md, architecture.md, system_state.md, hot.md, hoting_old_knowledge.md, brain/agent_registry.md, brain/task_queue.md.
- backend/requirements.txt present with 17 declarations; backend import scan excluding local/venv folders scanned 53 Python files with 0 parse errors and found one likely undeclared direct third-party import: pydantic (`backend/auth/models.py`, `backend/office_router.py`).
- MT5 bridge readiness files present: Desktop bridge size 62369, latest signal size 1305.
- Latest signal file parsed OK: contract atsawin_mt5_signal v2.4, buy XAUUSDm, confidence 0.883, RR 1.4, spread 280.0 points, timestamp 2026-06-04T02:05:03.713071+00:00, source bridge_mt5_pro_v2.4_fvg_fib_rsi, setup fvg_fib_rsi.

## Daily maintenance check - 2026-06-05 09:05:11 SEAST
- Host tools: python 3.14.5, pip 26.1.1, uv 0.11.17, git 2.54.0.windows.1, node v22.22.3; docker command missing.
- Memory docs loaded: spec.md, architecture.md, system_state.md, hot.md, hoting_old_knowledge.md, brain/agent_registry.md, brain/task_queue.md.
- backend/requirements.txt present with 17 declarations; backend import scan excluding local/venv folders scanned 53 Python files with 0 parse errors and found one likely undeclared direct third-party import: pydantic (`backend/auth/models.py`, `backend/office_router.py`).
- MT5 bridge readiness files present: Desktop bridge size 79109, mtime 2026-06-05T07:50:37.825065+07:00; latest signal size 1381, mtime 2026-06-05T09:04:21.571249+07:00.
- Latest signal file parsed OK: contract atsawin_mt5_signal v2.4, sell XAUUSDm, confidence 0.872, spread 280.0 points, timestamp 2026-06-05T02:04:21.553294+00:00, source bridge_mt5_pro_v2.4_fvg_fib_rsi, setup fvg_fib_rsi.

## Daily maintenance check - 2026-06-06 09:04:04 SEAST
- Host tools: python 3.14.5, pip 26.1.1, uv 0.11.17, git 2.54.0.windows.1, node v22.22.3; docker command missing.
- Memory docs loaded: spec.md, architecture.md, system_state.md, hot.md, hoting_old_knowledge.md, brain/agent_registry.md, brain/task_queue.md.
- backend/requirements.txt present with 17 declarations; backend import scan excluding local/venv folders scanned 53 Python files with 0 parse errors and found one likely undeclared direct third-party import: pydantic (`backend/auth/models.py`, `backend/office_router.py`).
- MT5 bridge readiness files present: Desktop bridge size 80123, mtime 2026-06-05T15:16:32.298676+07:00; latest signal size 1381, mtime 2026-06-06T09:05:06.627384+07:00.
- Latest signal file parsed OK: contract atsawin_mt5_signal v2.4, sell XAUUSDm, confidence 1.0, spread 280.0 points, timestamp 2026-06-06T02:05:06.628282+00:00, source bridge_mt5_pro_v2.4_fvg_fib_rsi, setup fvg_fib_rsi.
- Bridge copy drift: repo root and ea/ bridge files are byte-identical (sha256 `0a383f4d46964ddc0c4de781bd7619fcce064d9bae1c6048ce1bef313afa6fd6`), but Desktop deployed bridge differs (sha256 `9b13965696a86787c54ab6c1651847aecd2b89dbee515c50aa6f4603b1cd14cc`); first text diff at line 1818 lock-scope comment/logic area.

## Readiness watch - 2026-06-06 15:06:09 SEAST
Blockers changed: `.env.example` is missing; docker command missing; active Python 3.14.5 cannot import `uvicorn` (CLI exists in Hermes venv path); `pydantic` is imported directly but not declared in `backend/requirements.txt`. `python -m compileall C:/Users/Administrator/repos/AI/backend` passed.

## Readiness watch - 2026-06-12 15:36:48 SEAST
Blockers changed: critical files are now complete including `.env.example`; `python -m compileall C:/Users/Administrator/repos/AI/backend` passed; docker command is still missing; active Python 3.14.5 still cannot import `uvicorn`; direct dependency drift still shows `pydantic` missing from `backend/requirements.txt`.

## Readiness watch - 2026-06-12 21:41:53 SEAST
Blockers changed: `.env.example` is missing again; `python -m compileall C:/Users/Administrator/repos/AI/backend` passed; docker command is still missing; active Python 3.14.5 still cannot import `uvicorn`; direct dependency drift still shows `pydantic` imported in `backend/auth/models.py` and `backend/office_router.py` but not declared in `backend/requirements.txt`.

## Readiness watch - 2026-06-13 15:52:11 SEAST
Blockers changed: critical files are complete again including `.env.example`; `python -m compileall C:/Users/Administrator/repos/AI/backend` passed; docker command is still missing; active Python still cannot import `uvicorn`; direct dependency drift still shows `pydantic` imported in `backend/auth/models.py` and `backend/office_router.py` but not declared in `backend/requirements.txt`.

## Readiness watch - 2026-06-13 21:55:53 SEAST
Blockers changed: `.env.example` is missing again; `python -m compileall C:/Users/Administrator/repos/AI/backend` passed; docker command is still missing; active Python 3.14.5 has no `uvicorn` package in `pip list`; direct dependency drift still shows `pydantic` imported in `backend/auth/models.py` and `backend/office_router.py` but not declared in `backend/requirements.txt`.

## Readiness watch - 2026-06-18 10:19:06 SEAST
Blockers changed: critical files are complete again including `.env.example`; `python -m compileall C:/Users/Administrator/repos/AI/backend` passed; docker command is still missing; active Python 3.14.5 still has no `uvicorn` module; direct dependency drift still shows `pydantic` imported in `backend/auth/models.py` and `backend/office_router.py` but not declared in `backend/requirements.txt`.
