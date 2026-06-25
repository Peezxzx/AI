# Hoting Old Knowledge (Archive + Carry-Forward)

Purpose: keep important prior lessons without overwriting active memory.

## Carry-forward knowledge
- MT5/EA integration path is file-based JSON handoff.
- Symbol for Exness is typically XAUUSDm (suffix matters).
- Spread calibration and session filters heavily affect trade frequency.
- Backtest improvement does not guarantee walk-forward quality.
- Keep payload contract stable for EA parser compatibility.

## Archived signals
- Older hard session filters produced many HOLD/out_of_session outcomes.
- Parser/encoding issues in EA can silently produce conf=0 and no trades.

## Policy
- Keep this file append-only for durable lessons.
- Promote still-relevant lessons into spec.md / architecture.md / system_state.md.

## Readiness watch note (2026-06-02 02:05:58 SEAST)
- Current cron Python environment may differ from repo/runtime env: `uvicorn` CLI exists under Hermes venv, but `import uvicorn` failed in cron Python. Keep environment checks tied to the exact interpreter used for launch.

## Readiness watch - 2026-06-02 08:09:48
Blockers changed: missing docker, missing uvicorn in active Python environment, import not declared in requirements.txt: pydantic, import not declared in requirements.txt: trading. compileall=ok; critical_files=ok.

## Readiness watch - 2026-06-03 02:17:26 SEAST
Blockers changed: missing docker, missing uvicorn in active Python 3.14.5 environment, import not declared in requirements.txt: pydantic. compileall=ok; critical_files=ok. Previous extra `trading` drift is no longer detected by the local-module-aware scan.

## Readiness watch - 2026-06-06 15:06:09 SEAST
Blockers changed: `.env.example` is now missing in repo root; docker command missing; active Python 3.14.5 cannot import `uvicorn`; direct import drift remains `pydantic` missing from requirements. compileall=ok.

## Readiness watch - 2026-06-12 15:36:48 SEAST
Blockers changed: `.env.example` has been restored, but docker is still missing, active Python 3.14.5 still lacks `uvicorn`, and `pydantic` is still imported without a declaration in `backend/requirements.txt`. compileall=ok.

## Readiness watch - 2026-06-12 21:41:53 SEAST
Blockers changed: `.env.example` disappeared again after the earlier restore; docker is still missing, active Python 3.14.5 still lacks `uvicorn`, and `pydantic` is still imported without a declaration in `backend/requirements.txt`. compileall=ok.

## Readiness watch - 2026-06-13 15:52:11 SEAST
Blockers changed: `.env.example` has been restored again; docker is still missing, active Python still lacks `uvicorn`, and `pydantic` is still imported without a declaration in `backend/requirements.txt`. compileall=ok.

## Readiness watch - 2026-06-13 21:55:53 SEAST
Blockers changed: `.env.example` disappeared again; docker is still missing, active Python 3.14.5 still has no `uvicorn` package in `pip list`, and `pydantic` is still imported without a declaration in `backend/requirements.txt`. compileall=ok.

## Readiness watch - 2026-06-18 10:19:06 SEAST
Blockers changed: `.env.example` is present again, but docker is still missing, active Python 3.14.5 still has no `uvicorn` module, and `pydantic` is still imported without a declaration in `backend/requirements.txt`. compileall=ok.
