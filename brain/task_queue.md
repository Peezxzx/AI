# Autonomous Task Queue

Updated: 2026-06-18 09:02 SEAST

## Current maintenance checkpoint
- Host runtime check unchanged: python/pip/uv/git/node available; docker command still missing.
- Dependency drift unchanged for `pydantic`; import scan also still sees `psycopg2` imports while the manifest declares only `psycopg2-binary`.
- MT5 readiness files are present and latest signal is fresh on 2026-06-18; Desktop bridge copy still differs from repo root + `ea/` copies.
- Repo root `.env.example` is present again.

## Queue
1. [done] Add .env.example template at repo root
   - Completed: C:/Users/Administrator/repos/AI/.env.example
2. [done] Reconcile backend/requirements.txt with actual imports
   - Added: aiohttp, psutil, PyMuPDF
3. [done] Add runtime parity note (local Python 3.14 vs Docker Python 3.12)
4. [todo] Install/enable Docker toolchain on host (if required for local deployment)
5. [partial] Run validation cycle (API health + core trading pipeline tests)
   - Completed: repo .venv dependency sync via uv, selected py_compile checks pass, backend package imports pass
   - Completed: PDF extraction fallback to pypdf with regression test
   - Completed: local FastAPI smoke test `/health` and `/models` on 127.0.0.1:8000
   - Blocked: Docker missing, PostgreSQL localhost:5433 and Redis localhost:6380 not running locally
6. [todo] Add direct `pydantic` declaration to backend/requirements.txt or document reliance on FastAPI transitive dependency
   - 2026-06-03 scan: still undeclared; imported by `backend/auth/models.py` and `backend/office_router.py`.
   - 2026-06-04 scan: still undeclared; imported by `backend/auth/models.py` and `backend/office_router.py`.
   - 2026-06-05 scan: still undeclared; imported by `backend/auth/models.py` and `backend/office_router.py`.
   - 2026-06-06 scan: still undeclared; imported by `backend/auth/models.py` and `backend/office_router.py`.
   - 2026-06-11 scan: still undeclared; AST scan covered 53 backend Python files and still flags `backend/auth/models.py` and `backend/office_router.py`.
   - 2026-06-12 scan: still undeclared; AST scan covered 53 backend Python files with 0 parse errors and still flags `backend/auth/models.py` and `backend/office_router.py`.
   - 2026-06-13 scan: still undeclared; AST scan covered 53 backend Python files with 0 parse errors and still flags `backend/auth/models.py` and `backend/office_router.py`.
   - 2026-06-18 scan: still undeclared; AST scan covered 53 backend Python files with 0 parse errors and still flags `backend/auth/models.py` and `backend/office_router.py`.
7. [partial] Re-check MT5 latest_signal freshness and EA trade-allowed state in next maintenance cycle
   - 2026-06-03: bridge script and latest_signal.json present; latest signal mtime 2026-06-03 09:01:16 +0700. EA trade-allowed state not verified in this maintenance pass.
   - 2026-06-04: bridge script and latest_signal.json present; latest signal mtime 2026-06-04 09:05:03 +0700. Latest signal is v2.4 buy XAUUSDm and parses OK. EA trade-allowed state not verified in this maintenance pass.
   - 2026-06-05: bridge script and latest_signal.json present; latest signal mtime 2026-06-05 09:04:21 +0700. Latest signal is v2.4 sell XAUUSDm and parses OK. EA trade-allowed state not verified in this maintenance pass.
   - 2026-06-06: bridge script and latest_signal.json present; latest signal mtime 2026-06-06 09:05:06 +0700. Latest signal is v2.4 sell XAUUSDm and parses OK. EA trade-allowed state not verified in this maintenance pass.
   - 2026-06-11: bridge script and latest_signal.json present; latest signal mtime 2026-06-11 09:00:17 +0700. Latest signal is v2.4 sell XAUUSD and parses OK. EA trade-allowed state not verified in this maintenance pass.
   - 2026-06-12: bridge script and latest_signal.json present; latest signal mtime 2026-06-12 09:01:29 +0700. Latest signal is v2.4 buy XAUUSD / XAUUSDm and parses OK. EA trade-allowed state not verified in this maintenance pass.
   - 2026-06-13: bridge script and latest_signal.json present; latest signal mtime 2026-06-13 09:02:07 +0700. Latest signal is v2.4 buy XAUUSD / XAUUSDm and parses OK. EA trade-allowed state not verified in this maintenance pass.
   - 2026-06-18: bridge script and latest_signal.json present; latest signal mtime 2026-06-18 09:03:18 +0700. Latest signal is v2.4 sell XAUUSD / XAUUSDm and parses OK. EA trade-allowed state not verified in this maintenance pass.
8. [todo] Review Desktop deployed bridge drift vs repo/ea copies before restart/resync
   - 2026-06-06: repo root and ea/ copies are byte-identical; Desktop copy differs, first text diff at line 1818 in lock-scope comment/logic area.
   - 2026-06-11: drift still present by sha256; repo root + `ea/` = `0a383f4d46964ddc0c4de781bd7619fcce064d9bae1c6048ce1bef313afa6fd6`, Desktop = `9b13965696a86787c54ab6c1651847aecd2b89dbee515c50aa6f4603b1cd14cc`.
   - 2026-06-12: drift still present by sha256; repo root + `ea/` = `0a383f4d46964ddc0c4de781bd7619fcce064d9bae1c6048ce1bef313afa6fd6`, Desktop = `9b13965696a86787c54ab6c1651847aecd2b89dbee515c50aa6f4603b1cd14cc`.
   - 2026-06-13: drift still present by sha256; repo root + `ea/` = `0a383f4d46964ddc0c4de781bd7619fcce064d9bae1c6048ce1bef313afa6fd6`, Desktop = `9b13965696a86787c54ab6c1651847aecd2b89dbee515c50aa6f4603b1cd14cc`.
   - 2026-06-18: drift still present by sha256; repo root + `ea/` = `0a383f4d46964ddc0c4de781bd7619fcce064d9bae1c6048ce1bef313afa6fd6`, Desktop = `3d611ff679ca42002a7b2ddf180eba0784695396ee078ec8e1a1be7b25793de0`.
9. [done] Restore `.env.example` at repo root if local setup still depends on it
   - 2026-06-18 scan: `C:/Users/Administrator/repos/AI/.env.example` present (size 484, mtime 2026-06-01T19:26:58.578005+07:00).
10. [todo] Decide whether to normalize `psycopg2` dependency naming in drift checks or add an explicit manifest note
   - 2026-06-18 scan: imports found in `backend/auth/user_database.py` and `backend/memory_manager.py`, while manifest declares `psycopg2-binary`.

## Dependency map
- (1) and (2) should complete before deployment-quality verification.
- (4) required before docker-compose based local integration test.

## Execution policy
- Always load memory docs first.
- Execute highest-priority unblocked task.
- Write results back to system_state.md and hot.md.
