# HOT MEMORY

## Session 2026-06-18 09:02 SEAST: Daily Maintenance Check

### Current facts
- Host tools checked: python 3.14.5, pip 26.1.1, uv 0.11.17, git 2.54.0.windows.1, node v22.22.3; docker command missing.
- Memory docs loaded: spec.md, architecture.md, system_state.md, hot.md, hoting_old_knowledge.md, brain/agent_registry.md, brain/task_queue.md.
- backend/requirements.txt still has 17 declarations; backend AST import scan excluding local venv/vendor folders covered 53 backend Python files with 0 parse errors.
- Likely undeclared direct third-party import remains `pydantic` in `backend/auth/models.py` and `backend/office_router.py`; `psycopg2` imports are still fulfilled only via declared package name `psycopg2-binary`.
- MT5 readiness files present: Desktop bridge size 85256 (mtime 2026-06-14T07:43:14.248265+07:00); latest signal size 1515 and parsed OK as v2.4 `sell` for `XAUUSD` / `XAUUSDm`, confidence 1.0, spread 280.0 points, source `bridge_mt5_pro_v2.4_fvg_fib_rsi`, timestamp 2026-06-18T02:03:18.695610+00:00.
- Bridge copy drift still present: repo root and `ea/` copies are byte-identical by sha256; Desktop deployed bridge hash changed but still differs.
- Repo root `.env.example` is present again.

### Carry-forward
- Add explicit `pydantic` to requirements or document FastAPI-transitive reliance.
- Decide whether to declare `psycopg2` directly or keep relying on `psycopg2-binary` naming mismatch in drift checks.
- Docker remains absent on this host; docker-based validation remains blocked.
- Review Desktop bridge drift before next restart/resync so deployed code matches repo/ea copies.

---

## Session 2026-06-13 09:02 SEAST: Daily Maintenance Check

### Current facts
- Host tools checked: python 3.14.5, pip 26.1.1, uv 0.11.17, git 2.54.0.windows.1, node v22.22.3; docker command missing.
- Memory docs loaded: spec.md, architecture.md, system_state.md, hot.md, hoting_old_knowledge.md, brain/agent_registry.md, brain/task_queue.md.
- backend/requirements.txt still has 17 declarations; backend AST import scan covered 53 backend Python files with 0 parse errors.
- Likely undeclared direct third-party import remains `pydantic` in `backend/auth/models.py` and `backend/office_router.py`.
- MT5 readiness files present: Desktop bridge size 80123 (mtime 2026-06-05T15:16:32.298676+07:00); latest signal size 1486 and parsed OK as v2.4 `buy` for `XAUUSD` / `XAUUSDm`, confidence 1.0, spread 280.0 points, source `bridge_mt5_pro_v2.4_fvg_fib_rsi`, timestamp 2026-06-13T02:02:07.221403+00:00.
- Bridge copy drift still present: repo root and `ea/` copies are byte-identical by sha256; Desktop deployed bridge hash still differs.
- Repo root `.env.example` is currently absent.

### Carry-forward
- Add explicit `pydantic` to requirements or document FastAPI-transitive reliance.
- Docker remains absent on this host; docker-based validation remains blocked.
- Review Desktop bridge drift before next restart/resync so deployed code matches repo/ea copies.
- Restore `.env.example` in repo root if it is still expected for local setup.

---

## Session 2026-06-12 09:01 SEAST: Daily Maintenance Check

### Current facts
- Host tools checked: python 3.14.5, pip 26.1.1, uv 0.11.17, git 2.54.0.windows.1, node v22.22.3; docker command missing.
- Memory docs loaded: spec.md, architecture.md, system_state.md, hot.md, hoting_old_knowledge.md, brain/agent_registry.md, brain/task_queue.md.
- backend/requirements.txt still has 17 declarations; backend AST import scan covered 53 backend Python files with 0 parse errors.
- Likely undeclared direct third-party import remains `pydantic` in `backend/auth/models.py` and `backend/office_router.py`; `backend` import hits are local-package imports, not a missing external package.
- MT5 readiness files present: Desktop bridge size 80123 (mtime 2026-06-05T15:16:32.298676+07:00); latest signal size 1318 and parsed OK as v2.4 `buy` for `XAUUSD` / `XAUUSDm`, confidence 0.695, spread 280.0 points, source `bridge_mt5_pro_v2.4_fvg_fib_rsi`, timestamp 2026-06-12T02:01:29.749810+00:00.
- Bridge copy drift still present: repo root and `ea/` copies are byte-identical by sha256; Desktop deployed bridge hash still differs.

### Carry-forward
- Add explicit `pydantic` to requirements or document FastAPI-transitive reliance.
- Docker remains absent on this host; docker-based validation remains blocked.
- Review Desktop bridge drift before next restart/resync so deployed code matches repo/ea copies.

---

## Session 2026-06-11 09:01 SEAST: Daily Maintenance Check

### Current facts
- Host tools checked: python 3.14.5, pip 26.1.1, uv 0.11.17, git 2.54.0.windows.1, node v22.22.3; docker command missing.
- Memory docs loaded: spec.md, architecture.md, system_state.md, hot.md, hoting_old_knowledge.md, brain/agent_registry.md, brain/task_queue.md.
- backend/requirements.txt still has 17 declarations; backend AST import scan covered 53 backend Python files.
- Likely undeclared direct third-party import remains `pydantic` in `backend/auth/models.py` and `backend/office_router.py`.
- MT5 readiness files present: Desktop bridge size 80123 (mtime 2026-06-05 15:16:32 +0700); latest signal size 1319 and parsed OK as v2.4 `sell` for `XAUUSD`, confidence 0.752, spread 260.0 points, source `bridge_mt5_pro_v2.4_fvg_fib_rsi`, timestamp 2026-06-11T02:03:17.754692+00:00.
- Bridge copy drift still present: repo root and `ea/` copies are byte-identical by sha256; Desktop deployed bridge hash still differs.

### Carry-forward
- Add explicit `pydantic` to requirements or document FastAPI-transitive reliance.
- Docker remains absent on this host; docker-based validation remains blocked.
- Review Desktop bridge drift before next restart/resync so deployed code matches repo/ea copies.

---

## Session 2026-06-06 09:04 SEAST: Daily Maintenance Check

### Current facts
- Host tools checked: python 3.14.5, pip 26.1.1, uv 0.11.17, git 2.54.0.windows.1, node v22.22.3; docker command missing.
- Memory docs loaded: spec.md, architecture.md, system_state.md, hot.md, hoting_old_knowledge.md, brain/agent_registry.md, brain/task_queue.md.
- backend/requirements.txt has 17 declarations; AST import scan excluding local/venv folders covered 53 backend Python files with 0 parse errors.
- Likely undeclared direct third-party import remains `pydantic` in `backend/auth/models.py` and `backend/office_router.py`.
- MT5 readiness files present: Desktop bridge size 80123; latest signal size 1381 and parsed OK as v2.4 `sell` for XAUUSDm, confidence 1.0, spread 280.0 points, source `bridge_mt5_pro_v2.4_fvg_fib_rsi`, timestamp 2026-06-06T02:05:06.628282+00:00.
- Bridge copy drift detected: repo root and ea/ copies are byte-identical, but Desktop deployed `bridge_mt5_pro.py` differs; first text diff is at line 1818 in the lock-scope comment/logic area.

### Carry-forward
- Add explicit `pydantic` to requirements or document FastAPI-transitive reliance.
- Docker remains absent on this host; docker-compose validation remains blocked.
- Review Desktop bridge drift before restarting or resyncing the live bridge.

---

## Session 2026-06-05 13:15 SEAST: Builder — Desktop Bridge Cooldown Guard Resync + Test Isolation Fix

### Issue
`C:\Users\Administrator\Desktop\bridge_mt5_pro.py` (the actually running bridge) was **stale** — missing the `session_opt_cooldown_sec` CONFIG entry and the entire cooldown guard in `optimize_session_hours_from_trade_log()`. The repo copies (`bridge_mt5_pro.py` and `ea/bridge_mt5_pro.py`) had been updated in a previous session but the Desktop copy was never synced. This caused the session optimization to run every ~20-30 seconds when invoked by cron, flooding the log with repeated optimization attempts and temp file writes.

Additionally, `ea/tests/test_session_opt_statistical_guard.py` had a test isolation bug: the cooldown guard's result JSON persisted across test runs, causing `test_reject_insufficient_trades_per_hour` and `test_accept_sufficient_data` to be blocked by the cooldown from the previous test (0s elapsed < 3600s required).

### Fix Applied
1. **Desktop sync**: Copied `ea/bridge_mt5_pro.py` → `Desktop/bridge_mt5_pro.py` — all 3 copies now byte-identical (1967 lines)
2. **Test isolation**: Added `Path(_sess_json).unlink()` cleanup at the start of each of the 3 test functions in `ea/tests/test_session_opt_statistical_guard.py` to remove stale cooldown files before running

### Files Changed
- `C:\Users\Administrator\Desktop\bridge_mt5_pro.py` — full resync from ea/ copy (added `session_opt_cooldown_sec` config + 16 lines of cooldown guard)
- `ea/tests/test_session_opt_statistical_guard.py` — added cooldown cleanup in 3 test functions

### Validation
- `diff ea/bridge_mt5_pro.py Desktop/bridge_mt5_pro.py` → IDENTICAL
- `diff repos/AI/bridge_mt5_pro.py ea/bridge_mt5_pro.py` → IDENTICAL
- `python -m py_compile Desktop/bridge_mt5_pro.py` → SYNTAX OK
- `python -m pytest ea/tests/ -v` → 69/69 passed
- `python -m pytest tests/ --ignore=tests/test_office_router.py --ignore=tests/test_pdf_extract.py --ignore=tests/test_office_store.py --ignore=tests/test_office_task_engine.py -v` → 25/25 passed

### Live State
- Bridge will pick up the cooldown guard on next restart (Desktop copy now has the correct code)
- After restart, `--optimize-session` cron calls within the 3600s cooldown window will be skipped with an INFO log instead of running the full optimization pipeline

---

## Session 2026-06-05 10:30 SEAST: Builder — validate_payload position_size Check + Contract Doc Fix

### Issue
`validate_payload()` in `bridge_mt5_pro.py` did not validate `position_size > 0` for non-hold signals. If `calc_position_size()` silently returned `0.0` or a negative value (e.g., due to a future bug or edge case), the EA would receive a signal with `position_size=0`, causing it to skip the trade or use an undefined default. Additionally, the contract doc (`contracts/mt5_signal_v2_4.md`) was missing `bad_hour_penalty` from the `score_breakdown` field list — a contract mismatch since the code produces it.

### Fix Applied
1. **Code**: Added `position_size > 0` validation in `validate_payload()` for buy/sell signals (line ~941)
2. **Doc**: Added `bad_hour_penalty` to the `score_breakdown` field list in `contracts/mt5_signal_v2_4.md`
3. **Tests**: Updated `tests/test_validate_payload_fix.py` — all existing payloads now include `position_size`, added 3 new test cases for zero/negative/missing position_size
4. **Sync**: All 3 copies (repo root, ea/, Desktop) synced and byte-identical

### Validation
- `python tests/test_validate_payload_fix.py` → 16/16 passed (including 3 new position_size tests)
- `python -m pytest tests/test_missing_trade_log_fix.py tests/test_session_opt_fix.py tests/test_chop_regime_fix.py tests/test_ema_bias_fix.py tests/test_atomic_write_fix.py tests/test_bridge_fix.py tests/test_signal_threshold_fix.py -v` → 22/22 passed
- `python -m pytest ea/tests/ -v` → 69/69 passed
- `diff` all 3 copies → IDENTICAL
- `py_compile` → SYNTAX OK

### Live State
- Bridge running; will pick up position_size validation on next restart
- Contract doc now matches actual signal output

---

## Session 2026-06-05 09:05 SEAST: Daily Maintenance Check

### Current facts
- Host tools checked: python 3.14.5, pip 26.1.1, uv 0.11.17, git 2.54.0.windows.1, node v22.22.3; docker command missing.
- Memory docs loaded: spec.md, architecture.md, system_state.md, hot.md, hoting_old_knowledge.md, brain/agent_registry.md, brain/task_queue.md.
- backend/requirements.txt has 17 declarations; AST import scan covered 53 backend Python files with 0 parse errors.
- Likely undeclared direct third-party import remains `pydantic` in `backend/auth/models.py` and `backend/office_router.py`.
- MT5 readiness files present: Desktop bridge size 79109, latest signal size 1381.
- Latest signal JSON parsed OK: v2.4 `sell` for XAUUSDm, confidence 0.872, spread 280.0 points, source `bridge_mt5_pro_v2.4_fvg_fib_rsi`, timestamp 2026-06-05T02:04:21.553294+00:00.

### Carry-forward
- Add explicit `pydantic` to requirements or document FastAPI-transitive reliance.
- Docker remains absent on this host; docker-compose validation remains blocked.
- EA/MT5 trade-allowed runtime state was not verified in this maintenance pass; only bridge/signal files were checked.

---

## Session 2026-06-05 07:22 SEAST: Builder — chop_regime Reason Consistency Fix

### Issue
In `generate_signal()`, the "chop_regime" reason was appended to the reasons list whenever `av < min_atr_price or ema_gap < min_ema_gap_price`, even when the computed `chop_penalty` was 0.0. This created a contract mismatch: `score_breakdown.chop_penalty = 0.0` but `"chop_regime"` appeared in `reasons`. The penalty formula `max(0.0, 0.4*(1-gap_ratio) + 0.3*(1-atr_ratio))` can produce 0.0 when one ratio is above 1.0 (compensating for the other being slightly below threshold), making the reason misleading.

### Fix Applied
- **File**: `bridge_mt5_pro.py` (repo root) → synced to `ea/bridge_mt5_pro.py` and `Desktop/bridge_mt5_pro.py`
- Moved `reasons.append("chop_regime")` inside a `if chop_penalty > 0.0:` guard
- Now "chop_regime" only appears in reasons when there is an actual penalty > 0.0
- Added validation test: `tests/test_chop_regime_fix.py` (3 tests)

### Validation
- `python -m pytest tests/test_chop_regime_fix.py -v` → 3/3 passed
- `python -m pytest tests/test_missing_trade_log_fix.py tests/test_session_opt_fix.py tests/test_ema_bias_fix.py tests/test_atomic_write_fix.py tests/test_validate_payload_fix.py tests/test_bridge_fix.py tests/test_signal_threshold_fix.py tests/test_chop_regime_fix.py -v` → 22/22 passed
- `python -m pytest ea/tests/ -v` → 69/69 passed
- `diff` all 3 copies → IDENTICAL
- `py_compile` → SYNTAX OK

### Live State
- Bridge last ran at 05:03 (log file). Desktop copy synced with fix.
- EA v4.04, 3 open positions, decision SKIP (hard_magic_cap), basket=-48.12
- Fix will activate on next bridge restart.

---

## Session 2026-06-05 02:55 SEAST: Builder — Desktop Bridge Resync + analyze_trade_log log.level Fix

### Issue
`C:\Users\Administrator\Desktop\bridge_mt5_pro.py` (the actually running bridge) was **stale** — it still had the old `log.error` + `return None` in `optimize_session_hours_from_trade_log()` at line 1487. The repo copies (`bridge_mt5_pro.py` and `ea/bridge_mt5_pro.py`) had been fixed in the previous session (01:00 SEAST) but the Desktop copy was never synced. The bridge log showed repeated `[ERROR] session optimize failed: trade log not found` entries every ~2-3 minutes.

Additionally, `analyze_trade_log()` used `log.error` for a missing trade log file — inconsistent with all other rejection paths which use `log.warning`. A missing trade log is a normal condition (e.g., `--analyze` before any backtest), not an error.

### Fix Applied
1. **Desktop sync**: Copied `ea/bridge_mt5_pro.py` → `Desktop/bridge_mt5_pro.py` — all 3 copies now byte-identical
2. **log.level fix**: Changed `log.error` → `log.warning` in `analyze_trade_log()` in both repo root and ea/ copies

### Files Changed
- `bridge_mt5_pro.py` (repo root) — `log.error` → `log.warning` at line 1225
- `ea/bridge_mt5_pro.py` — `log.error` → `log.warning` at line 1225
- `C:\Users\Administrator\Desktop\bridge_mt5_pro.py` — full resync from ea/ copy

### Validation
- `diff ea/bridge_mt5_pro.py Desktop/bridge_mt5_pro.py` → IDENTICAL
- `python -m pytest tests/test_missing_trade_log_fix.py tests/test_session_opt_fix.py -v` → 5/5 passed
- `python -m pytest ea/tests/test_session_opt_statistical_guard.py ea/tests/test_session_opt_safety.py tests/test_ema_bias_fix.py tests/test_atomic_write_fix.py tests/test_validate_payload_fix.py tests/test_bridge_fix.py -v` → 23/23 passed
- `py_compile` all 3 copies → OK

### Live State
- Bridge will pick up both fixes on next restart (Desktop copy now has the correct code)

---

## Session 2026-06-05 01:00 SEAST: Builder — Missing Trade Log ERROR Spam Fix

### Issue
`optimize_session_hours_from_trade_log()` in `bridge_mt5_pro.py` logged `ERROR` and returned `None` when the trade log CSV file didn't exist. The bridge log showed repeated `ERROR] session optimize failed: trade log not found` entries (lines 163-165, 223-225, 244-246) every ~2-3 minutes when `--optimize-session` was invoked without a prior backtest generating the CSV. This was inconsistent with all other rejection paths which (a) use `log.warning`, (b) write a proper result JSON, and (c) return a result dict.

### Fix Applied
- **Files**: `bridge_mt5_pro.py` (repo root) + `ea/bridge_mt5_pro.py` (synced)
- Changed missing-file handler from `log.error` + `return None` to:
  - `log.warning` with descriptive message
  - Writes a proper result JSON with `selection_mode: "skipped_no_trade_log"`
  - Returns the result dict (not `None`) — consistent with all other rejection paths
- Added new validation test: `tests/test_missing_trade_log_fix.py` (2 tests)

### Validation
- `python -m pytest tests/test_session_opt_fix.py tests/test_missing_trade_log_fix.py -v` → 5/5 passed
- `python -m pytest ea/tests/test_session_opt_statistical_guard.py ea/tests/test_session_opt_safety.py -v` → 9/9 passed
- `python -m pytest tests/test_ema_bias_fix.py tests/test_atomic_write_fix.py tests/test_validate_payload_fix.py tests/test_bridge_fix.py -v` → 10/10 passed

### Live State
- Bridge log shows the fix will eliminate ERROR spam on subsequent --optimize-session runs
- Both file copies (repo root, ea/) synced

---

## Session 2026-06-05 00:30 SEAST: Builder — Session Optimization Statistical Significance Guard

### Issue
`optimize_session_hours_from_trade_log()` in `bridge_mt5_pro.py` was accepting trade logs with as few as 12 total trades (3 trades/hour × 4 hours). The bridge log showed wildly inconsistent session hour selections on consecutive runs: `[0,1,5,10,13,14]` → `[0,1,2,3,4,5]` → back to `[0,1,5,10,13,14]`. Each run used only 5 trades per hour with 100% winrate — clear overfitting on tiny samples. The `min_trades_per_hour=3` default was far too low for statistical significance.

### Fix Applied
- **File**: `ea/bridge_mt5_pro.py` → synced to `bridge_mt5_pro.py` (repo root) and `Desktop/bridge_mt5_pro.py`
- Raised `min_trades_per_hour` default from 3 → 10
- Added new `min_total_trades=50` parameter and early-rejection guard in `optimize_session_hours_from_trade_log()`
- Added CONFIG entries: `session_opt_min_trades_per_hour=10`, `session_opt_min_total_trades=50`
- Updated `--optimize-session` handler to read thresholds from CONFIG
- Updated existing tests (`test_session_opt_fix.py`) to use sufficient data (50-60 trades)
- Added new validation tests: `ea/tests/test_session_opt_statistical_guard.py` (4 tests)

### Validation
- `python -m pytest ea/tests/ -q` → 69/69 passed
- `python -m pytest tests/test_session_opt_fix.py tests/test_signal_threshold_fix.py ... -q` → 14/14 passed
- `python -m pytest ea/tests/test_session_opt_statistical_guard.py -v` → 4/4 passed
  - test_reject_insufficient_total_trades: 15 trades → REJECTED ✅
  - test_reject_insufficient_trades_per_hour: 60 trades, 5/hour → handled correctly ✅
  - test_accept_sufficient_data: 120 trades, 20/hour → ACCEPTED ✅
  - test_config_values: CONFIG has new keys ✅

### Live State
- Bridge not currently running (log entries were from previous session)
- All 3 file copies (repo root, ea/, Desktop) synced and byte-identical

---

## Session 2026-06-04 21:48 SEAST: Builder — calc_position_size Silent Fallback Fix

### Issue
`calc_position_size()` in `bridge_mt5_pro.py` had three silent fallback paths that all returned `0.01` (minimum lot) without any log warning. The most impactful: when `tick_value` or `tick_size` was `0` (common for Exness XAUUSDm), the function silently returned `min_lot` instead of computing proper risk-based position size. This caused the bridge to always send `position_size: 0.01` to the EA regardless of account balance and risk settings.

### Fix Applied
- **File**: `ea/bridge_mt5_pro.py` → synced to `bridge_mt5_pro.py` (repo root) and `Desktop/bridge_mt5_pro.py`
- Added fallback tick_value/tick_size when MT5 returns 0: `tick_value = point * 100.0`, `tick_size = point` (correct for XAUUSDm: 1 lot × 1 point = $1)
- All three fallback paths now emit `log.warning` with context (which path was taken, what values were used)
- Added warning when result is at `min_lot` with diagnostic info (balance, risk%, stop_dist, loss_per_lot)

### Validation
- `python -m py_compile ea/bridge_mt5_pro.py` → SYNTAX OK
- `python -m pytest ea/tests/ -q` → 65/65 passed
- `python -m pytest tests/test_ema_bias_fix.py tests/test_atomic_write_fix.py tests/test_validate_payload_fix.py tests/test_bridge_fix.py tests/test_session_opt_fix.py tests/test_signal_threshold_fix.py -q` → 17/17 passed
- Custom validation `_validate_possize_fix.py`: 6/6 scenarios passed
  - Scenario 1 (balance=10000, tick=0): OLD=0.01 → NEW=0.09 ✅
  - Scenario 2 (normal broker): OLD=0.09 → NEW=0.09 (unchanged) ✅
  - Scenario 3 (tick=None): OLD=0.01 → NEW=0.09 ✅
  - Scenario 4 (invalid entry): both return 0.01 ✅
  - Scenario 5 (small balance): correctly returns 0.01 ✅
  - Scenario 6 (fallback math): 0.07 properly computed ✅

### Live State
- Bridge running PID 13788, lock held
- EA v4.04, decision SKIP (basket_loss_guard, basket=-17.18)
- Signal: buy conf=0.763, position_size=0.01 (will improve after bridge restart picks up fix)

### Note
Running bridge still has old code loaded. On next bridge restart, the new calc_position_size with fallback will activate. The fix is backward-compatible: when tick_value/tick_size are properly reported by MT5, behavior is identical to before.

---

## Session 2026-06-04 19:46 SEAST: MT5 Exness Login Verify + One-click Signal Launchers

### Scope
- User manually logged into five Exness portable MT5 apps and asked to verify.
- User asked for scripts that run the signal bridge/file together with MT5 EA apps.

### Verification
- All five portable MT5 clone processes are running under `C:\Users\Administrator\MT5_Clones`.
- `MetaTrader5.initialize(path=<portable terminal>, portable=True)` verified each logged-in account with `trade_allowed=True` and `XAUUSDm` tick OK:
  - `MT5_HYDRA_24H_GRID`: `433684944` / `Exness-MT5Trial7`
  - `MT5_ATSAWIN_V4_04_SIGNAL`: `413855197` / `Exness-MT5Trial6`
  - `MT5_TEMPO_ORDERFLOW_PRO`: `433721852` / `Exness-MT5Trial7`
  - `MT5_REBATE_GUARDIAN`: `415823499` / `Exness-MT5Trial14`
  - `MT5_ATSAWIN_V3_LEGACY`: `433721860` / `Exness-MT5Trial7`
- Credential hygiene verified: no `login_once.ini`, no `*password*`, no `*credential*` under clone base; no password assignment lines in Desktop launchers/scripts.

### Created
- `Desktop\EXNESS_ACCOUNT_MAPPING_NO_PASSWORD.txt` and copy in `Desktop\02_MT5_EA_APPS_LAUNCHERS\`.
- `Desktop\01_ATSAWIN_DASHBOARD_AND_BRIDGE\run_bridge_logged_in_mt5.py` wrapper attaches bridge to already logged-in `MT5_ATSAWIN_V4_04_SIGNAL` terminal, avoiding Exness passwordless API error `Unsupported authorization mode, OTP or certificate password needed`.
- One-click scripts on Desktop and `02_MT5_EA_APPS_LAUNCHERS`:
  - `RUN_ATSAWIN_SIGNAL_BRIDGE_AND_ALL_MT5_EA_APPS.cmd`
  - `RUN_ATSAWIN_SIGNAL_ONCE_AND_OPEN_V4_EA.cmd`
  - `RUN_ATSAWIN_SIGNAL_ONCE_ONLY.cmd`

### Runtime Test
- `python ...\run_bridge_logged_in_mt5.py --once` succeeded.
- `RUN_ATSAWIN_SIGNAL_ONCE_ONLY.cmd` via `cmd /c` succeeded and updated `latest_signal.json` + `ea_status.json`.
- Latest signal: schema `2.4`, `buy`, confidence `0.793`, `XAUUSDm`, entry `4501.3`, SL `4481.18`, TP `4529.48`, timestamp `2026-06-04T12:46:23.418781+00:00`.

### Log
- `logs/2026-06-04-mt5-exness-login-signal-launcher.md`

---

## Session 2026-06-04 10:19 SEAST: Session Filter + Live Execution Compare

### Scope
- User requested only two items: bad-hour score reduction and backtest-vs-live execution comparison (spread/slippage/late-entry/actual-RR/stacking).

### Changes
- Added soft bad-hour filter in `ea/bridge_mt5_pro.py` and synced to `C:\Users\Administrator\Desktop\bridge_mt5_pro.py`.
- `score_breakdown` now includes `bad_hour_penalty`; this lowers the leading buy/sell score, not a hard block.
- Added CLI `--compare-live-execution --compare-days 30` and outputs:
  - `C:\Users\Administrator\Desktop\bridge_mt5_live_execution_compare.json`
  - `C:\Users\Administrator\Desktop\bridge_mt5_live_execution_compare.txt`
- Added tests: `ea/tests/test_session_filter_and_live_compare.py`.

### Verification
- Full EA tests: `61 passed in 33.42s`.
- Desktop deployed bridge backtest/analyze/compare executed successfully.
- Live bridge restarted on Hermes bg `proc_d85ff4b5ccb1`, Python PID `11452`; latest signal fresh and contains `bad_hour_penalty`.

### Latest Results
- Backtest: trades `1116`, winrate `49.19%`, pnl_r `218.57`.
- Live 30d EA magic `20260601`: trades `56`, winrate `33.93%`, net `-368.66`; winrate gap `-15.26 pct`.
- Current bad UTC hours from backtest: h13 penalty `0.227`, h15 `0.053`, h16 `0.050`, h23 `0.120`.
- Execution compare: spread OK (`280 <= 450`), actual_rr OK latest (`1.429`), stacking BAD (`magic_positions=3`, reason `hard_magic_cap`), slippage exact remains unknown until EA logs requested vs actual fill.

### Log
- `logs/2026-06-04-session-filter-live-compare.md`

---

## Session 2026-06-04 09:38 SEAST: Bridge Restart Fix + Server Assessment

### User Report
- User reported Bridge could not run.

### Root Cause
- Desktop bridge manual launch was exiting because a previous background bridge was already running and held lock PID `12952`.
- Reproduced output: `bridge_mt5_pro lock held by PID 12952 — another instance is running. Exiting.`

### Fix / Verification
- Terminated old bridge process tree PIDs `2836`, `10824`, `12952`; removed lock.
- `--health` passed: `account_ok=True symbol_tick_ok=True`.
- `--once` passed and wrote a BUY signal.
- Restarted bridge without noisy `watch_patterns`: Hermes bg `proc_92686a95bd5e`, python PID `13240`, lock now held by `13240`.
- Latest signal verified fresh: schema `2.4`, source `bridge_mt5_pro_v2.4_fvg_fib_rsi`, signal `buy`, confidence `1.0`, `rsi_divergence=none`, `fib_nearest_ratio=0.57`.
- Created Desktop helper: `C:\Users\Administrator\Desktop\Restart_Atsawin_Bridge.cmd`.

### Server Assessment
- FastAPI `127.0.0.1:8000` open and `/api/office/status` responds.
- PostgreSQL `5433` and Redis `6380` closed on this Windows host; Docker missing from previous maintenance.
- CPU was 100% at status snapshot; backend usable for local read-only dashboard/dev, not yet production-grade.

### Log
- `logs/2026-06-04-bridge-restart-fix-server-assessment.md`

### Follow-up notification note
- A later Telegram `IMPORTANT` block referenced old Hermes session `proc_d941d49849d7`; `process kill proc_d941d49849d7` returned `not_found` and live OS process scan showed only the new bridge tree (bash PIDs `13560/3192`, python PID `13240`). Treat that notification as delayed/backlog from the old noisy watcher, not a current live duplicate.

---

## Session 2026-06-04 09:05 SEAST: Daily Maintenance Check

### Current facts
- Host tools checked: python 3.14.5, pip 26.1.1, uv 0.11.17, git 2.54.0.windows.1, node v22.22.3; docker command missing.
- Memory docs loaded: spec.md, architecture.md, system_state.md, hot.md, hoting_old_knowledge.md, brain/agent_registry.md, brain/task_queue.md.
- backend/requirements.txt has 17 declarations; AST import scan covered 53 backend Python files with 0 parse errors.
- Likely undeclared direct third-party import remains `pydantic` in `backend/auth/models.py` and `backend/office_router.py`.
- MT5 readiness files present: Desktop bridge size 62369, latest signal size 1305.
- Desktop bridge `py_compile` passed; latest signal JSON parsed OK.
- Latest signal: v2.4 `buy` for XAUUSDm, confidence 0.883, RR 1.4, source `bridge_mt5_pro_v2.4_fvg_fib_rsi`, timestamp 2026-06-04T02:05:03.713071+00:00.

### Carry-forward
- Add explicit `pydantic` to requirements or document FastAPI-transitive reliance.
- Docker remains absent on this host; docker-compose validation remains blocked.
- EA/MT5 trade-allowed runtime state was not verified in this maintenance pass; only bridge/signal files were checked.

---

## Session 2026-06-04 07:51 SEAST: Builder — Desktop Bridge Status Dict Resync

### Issue
`C:\Users\Administrator\Desktop\bridge_mt5_pro.py` (the deployed/running bridge) was 11 lines behind the repo copy at `ea/bridge_mt5_pro.py` (1620 vs 1631 lines). The Desktop status dict in `scan_once()` was missing 11 fields that the repo version had:
- `contract`, `confirm_timeframe`, `entry_price`, `stop_loss`, `take_profit`, `atr`, `rsi`, `ema_fast`, `ema_slow`, `timestamp`, `timestamp_epoch`

The Desktop file had last been modified at 03:22 while the repo was updated at 05:38. Although the running bridge process happened to produce correct `ea_status.json` (likely restarted from a different code path), the stale Desktop file would cause missing status fields on next bridge restart.

### Fix
Synced Desktop copy with repo copy:
```
cp repos/AI/ea/bridge_mt5_pro.py Desktop/bridge_mt5_pro.py
```
All three copies (repo root, ea/, Desktop) are now byte-identical at 1631 lines.

### Validation
- `diff ea/bridge_mt5_pro.py Desktop/bridge_mt5_pro.py` → IDENTICAL
- `diff repos/AI/bridge_mt5_pro.py ea/bridge_mt5_pro.py` → IDENTICAL
- `python -m py_compile Desktop/bridge_mt5_pro.py` → SYNTAX OK
- `python -m pytest ea/tests/ -q` → 58/58 passed in 32.75s
- `python -m pytest tests/test_ema_bias_fix.py tests/test_atomic_write_fix.py tests/test_validate_payload_fix.py tests/test_bridge_fix.py tests/test_session_opt_fix.py tests/test_signal_threshold_fix.py -q` → 17/17 passed in 1.84s
- Live bridge still running; will pick up full status dict on next restart

### Note
Running bridge process still has the old code loaded; it will pick up the fix on next restart. Consider restarting the bridge to immediately activate the complete status dict.

---

## Session 2026-06-03 18:22 SEAST: Desktop Bridge Sync — ea_status Metadata Recovery

### Issue
`_diag_signal.py` runtime check showed `rsi_divergence in status=False` and `fib_nearest_ratio in status=False` in `ea_status.json`. The repo/ea copies had the 4 metadata fields (line 826-829) but the **Desktop deployed copy** (the actually running bridge) was missing them — the sync from the previous builder session only covered repo↔ea, not Desktop.

### Fix
Added the 4 missing fields to the status payload dict in `Desktop/bridge_mt5_pro.py`:
- `fib_nearest_ratio`
- `fib_nearest_level`
- `fib_distance`
- `rsi_divergence`

### Post-fix State
- `diff ea/bridge_mt5_pro.py Desktop/bridge_mt5_pro.py` → IDENTICAL (all 3 copies in sync)
- `_validate_fix.py` → ALL CHECKS PASSED (30 status keys)
- `py_compile` → OK for all copies
- Test suite: `58 passed in 32.83s`
- After next bridge scan cycle (≤60s), `ea_status.json` on MT5 will include the new fields

### Note
Running bridge process still has the OLD code loaded; it will pick up the fix on next restart. Consider killing/restarting the bridge if immediate pickup is desired.

## Session 2026-06-03 18:06 SEAST: Builder — ea_status.json Metadata Fix

### Issue
`ea_status.json` (read by EA for runtime dashboard) was missing 4 strategy metadata fields that `latest_signal.json` already carried: `fib_nearest_ratio`, `fib_nearest_level`, `fib_distance`, `rsi_divergence`. EA v4.04 metadata dashboard labels (`FVG`, `FIB`, `RSI_DIV`) could not display these values from the status file.

### Fix
Added the 4 missing fields to the status payload dict in `scan_once()` in both `bridge_mt5_pro.py` and `ea/bridge_mt5_pro.py` (identical copies). Updated `contracts/mt5_signal_v2_4.md` to document the status file field set.

### Validation
- AST check: status dict now contains all 4 required keys (total 30 keys)
- `py_compile` passed for both bridge files
- Files remain byte-identical
- Test suite: `58 passed in 32.37s`

### Live State
- Bridge live, latest signal: `sell conf=1.0 rsi_divergence=none fib_nearest_ratio=0.242`
- After next bridge scan cycle (≤60s), `ea_status.json` will include the new fields


## Session 2026-06-03 17:29 SEAST: EA v4.04 Strategy Metadata Release

### User Request
- User said "เอาใหม่" after prior blocked edit attempt; proceeded with clean redo.

### Completed
- Implemented EA v4.04 display/status-only bridge strategy metadata integration in `ea/AtsawinEA.mq5`.
- Added v2.4 metadata globals + parser + runtime JSON fields + compact dashboard labels: `STRATEGY`, `FVG`, `FIB`, `RSI_DIV`.
- Execution behavior unchanged: safety guards/confidence/spread/symbol/expiry/live-RR/caps still control orders.
- TDD: RED `5 failed`; GREEN `5 passed`; regression bundle `24 passed in 0.87s`.
- Compiled/deployed Desktop and MT5 Experts artifacts. MetaEditor log: `0 errors, 0 warnings` for Desktop `AtsawinEA_v4_04.mq5` and Experts `AtsawinEA.mq5`.
- Visible Desktop: `AtsawinEA_v4_04.mq5/.ex5`, `AtsawinEA_v4.mq5/.ex5`, `AtsawinEA.mq5/.ex5`.

### Live State
- Bridge latest signal remains v2.4 and includes metadata (`fib_nearest_ratio=0.242`, `rsi_divergence=regular_bullish`).
- Runtime status still shows `ea_version=4.02`; MT5 attached chart must be reattached/restarted to load compiled v4.04 before live runtime can verify `ea_version=4.04`.


## Session 2026-06-03 17:12 SEAST: Full Power Preflight

### User Request
- User said "เดินระบบเต็มกำลัง555".

### Completed
- Live bridge checked: v2.4 `bridge_mt5_pro_v2.4_fvg_fib_rsi`, latest SELL conf `1.0`, RSI divergence `regular_bullish`.
- EA runtime checked: still attached old `ea_version=4.02`, decision `SKIP`, reason `hard_magic_cap`; live runtime does not yet show v4.03/v4.04 because MT5 chart EA has not been reattached/restarted.
- Wrote RED tests for planned EA v4.04 metadata dashboard/status parser: `ea/tests/test_ea_strategy_metadata_v404.py` → `5 failed` as expected.
- Bridge verification still green: `19 passed in 0.90s`; backtest `trades=1128 wins=564 losses=564 winrate=50.0% pnl_r=242.87 skipped=72`.

### Blocker
- Attempted file edit for `ea/AtsawinEA.mq5` was blocked by tool consent guard. Do not retry same edit in this turn. Need user permission to proceed with file edits.

### Next After Permission
- Implement EA v4.04 display/status-only parser for v2.4 metadata, compile, deploy Desktop + Experts artifacts, then ask/guide user to reattach/restart EA and verify runtime version.


## Session 2026-06-03 16:55 SEAST: RSI Divergence v2.4 Bridge Integration

### User Check-in
- User asked "เป็นไงบ้างครับ" while only pending item was RSI divergence scaffold/test.

### Implementation
- Added RSI divergence in bridge only; EA execution remains unchanged/safe.
- New functions: `rolling_rsi_values`, `find_pivots`, `detect_rsi_divergence`, `rsi_divergence_payload_metadata`.
- Supports: `regular_bullish`, `regular_bearish`, `hidden_bullish`, `hidden_bearish`, `none`.
- Strategy/schema bumped to `2.4` / `bridge_mt5_pro_v2.4_fvg_fib_rsi`.
- Metadata includes `rsi_divergence`; `score_breakdown` includes `rsi_divergence_bonus`.
- Contract added: `contracts/mt5_signal_v2_4.md`.

### Verification
- TDD RED first: 7 failures due missing APIs.
- Green tests: `19 passed in 0.82s` for RSI/Fib/FVG/contract tests using Python314.
- `py_compile` passed for repo, EA copy, and Desktop bridge.
- Backtest improved vs v2.3: `trades=1128 wins=564 losses=564 winrate=50.0% pnl_r=242.87 skipped=72`.
- Analyze generated Desktop JSON/TXT reports.
- Live bridge restarted as bg session `proc_d941d49849d7`.
- Live latest signal verified: schema `2.4`, source `bridge_mt5_pro_v2.4_fvg_fib_rsi`, signal `sell`, confidence `1.0`, `rsi_divergence=regular_bullish`, score breakdown buy `0.35` vs sell `2.8`.
- Note: bullish divergence is treated as counter-pressure/score offset and metadata; it does not force EA buy.
- Log saved: `logs/2026-06-03-rsi-divergence-v24-bridge-implementation.md`.


## Session 2026-06-03 13:35 SEAST: Fibonacci v2.3 Bridge Integration

### User Direction
- User confirmed they authored the FVG PDF and approved using its ideas fully in Atsawin.

### Implementation
- Added PDF Fibonacci ratios: `0.242, 0.57, 1.617, 3.097, 5.165, 7.044, 8.237`.
- Added `compute_fib_levels`, `nearest_fib_level`, `fib_payload_metadata`.
- Strategy/schema bumped to `2.3` / `bridge_mt5_pro_v2.3_fvg_fib`.
- Signal metadata now includes `fib_nearest_ratio`, `fib_nearest_level`, `fib_distance`.
- If active FVG sits near PDF fib confluence, bridge adds `fib_confluence` reason and small `fib_bonus`.

### Verification
- Tests: `12 passed in 0.82s` for fib/fvg/contract tests using Python314.
- `py_compile` passed for repo, EA copy, and Desktop bridge.
- Backtest: `trades=1128 wins=563 losses=565 winrate=49.9% pnl_r=240.47 skipped=72`.
- Live bridge restarted as bg session `proc_3a8975a340e5`.
- Live latest signal verified: schema `2.3`, source `bridge_mt5_pro_v2.3_fvg_fib`, signal `sell`, fib ratio `0.242`, fib level `4475.53663`, fib distance `12.08163`.
- Log saved: `logs/2026-06-03-fib-v23-bridge-implementation.md`.


## Session 2026-06-03 13:20 SEAST: FVG v2.2 Bridge Live Integration

### User Request
- User asked to bring FVG PDF ideas into the current Atsawin system.

### Implementation
- Implemented strategy enhancement in Python bridge first, not EA execution logic.
- Files changed/synced:
  - `ea/bridge_mt5_pro.py`
  - `bridge_mt5_pro.py`
  - `C:\Users\Administrator\Desktop\bridge_mt5_pro.py`
  - `ea/tests/test_bridge_fvg_v22.py`
  - `ea/tests/test_bridge_signal_contract_v21.py`
- Added `FVGZone`, `detect_fvg_zones`, `nearest_active_fvg`, `fvg_payload_metadata`.
- Signal schema bumped to `2.2`; source/strategy version `bridge_mt5_pro_v2.2_fvg`.
- Additive metadata: `setup_type`, `fvg_direction`, `fvg_low/high/mid`, `fvg_age_bars`, `fvg_width`, `fvg_distance`, placeholder fib/RSI-div fields, `score_breakdown`.
- FVG scoring: trend up + nearby bullish FVG adds buy bonus; trend down + nearby bearish FVG adds sell bonus.

### Verification
- TDD red observed first; green tests passed: `8 passed in 0.59s` using Python314.
- `py_compile` passed for root + ea bridge copies.
- MT5 health passed: `account_ok=True symbol_tick_ok=True`.
- Backtest after FVG integration: `trades=1128 wins=563 losses=565 winrate=49.9% pnl_r=240.47 skipped=72`.
- Live once wrote v2.2 signal: SELL conf `1.0`, setup `fvg_fib_rsi`, bearish FVG near price, reasons include `bearish_fvg_near_price`.
- Old Desktop bridge processes were terminated; updated Desktop bridge started as Hermes bg session `proc_bedae08eed2a`.

### Note
- EA runtime may still show `ea_version=4.02` until MT5 chart EA is reattached/reloaded to compiled v4.03+.
- New bridge fields are backward-compatible; current EA parser ignores unknown metadata and still uses core SL/TP/signal fields.
- Log saved: `logs/2026-06-03-fvg-v22-bridge-implementation.md`.


## Session 2026-06-03 12:45 SEAST: PDF FVG → AtsawinEA v4.04 Plan

### User Direction
- Website/Virtual Office is paused.
- Focus is EA first.
- User sent PDF: `จากแนวคิดสู่การลงทุนจริง_การสร้างระบบเทรดบน Linux ด้วยกลยุทธ์_FVG.pdf` and approved recommended flow: read PDF → extract FVG strategy → compare current EA/bridge → propose v4.04 plan.

### PDF Extract
- Extracted via `pdftotext -layout` to `logs/fvg_pdf_extract.txt`.
- Thai glyph extraction degraded but technical structure readable.
- Main ideas: Human-First, dry-run/safety gate, docs/memory constitution, logs/audit trail, MetaApi optional Linux bridge, strategy = FVG + Fibonacci + RSI divergence + risk-based sizing.

### Current Bridge/EA Gap
- Current `bridge_mt5_pro.py` uses EMA30/40 + RSI range + ATR SL/TP + H1 EMA confirmation + session/spread filters.
- No FVG detection, no Fibonacci confluence, no RSI divergence yet.
- Current EA only needs signal/SL/TP; it can ignore new metadata safely.
- Live state checked: latest signal `sell` conf `1.0` RR `1.4`; attached EA status still `v4.02`, `SKIP hard_magic_cap`, 3/3 positions. v4.03 compiled earlier but likely not reattached/reloaded.

### Recommended v4.04 Path
- Phase 1 first: bridge-only FVG scanner + dry-run metadata + tests; do NOT change live EA execution logic yet.
- Add `FVGZone`, `detect_fvg_zones`, nearest active FVG scoring, payload metadata: `setup_type`, `strategy_version`, `fvg_low/high/mid`, `fib_nearest_level`, `rsi_divergence`, `score_breakdown`.
- Later: Fibonacci confluence, RSI divergence, backtest compare, then minimal EA v4.04 status/dashboard parse.
- Analysis saved: `logs/2026-06-03-fvg-pdf-to-ea-v4-04-plan.md`.
- Verification: `Python314 -m pytest ea/tests/test_bridge_signal_contract_v21.py -q` → `4 passed in 0.65s`. Hermes venv lacks MetaTrader5, so bridge tests should use Python 3.14.


## Session 2026-06-03 12:20 SEAST: EA v4.03 Runtime Status Observability

### Live Findings
- Virtual Office work paused; focus moved back to MT5 EA.
- Fresh XAUUSDm M15 SELL signal was being read correctly from Common Files.
- Live EA runtime was `SKIP / hard_magic_cap` with 3 open XAUUSDm positions under magic `20260601`.
- Python MT5 check showed 3 positions, balance about 1099.50, equity about 1094.72 during inspection.
- Current attached EA kept writing `ea_version=4.02` after compile, meaning MT5 had not hot-reloaded the attached EA.

### Change Applied
- **File**: `ea/AtsawinEA.mq5` bumped v4.02 → v4.03.
- Moved tick/spread/live actual-RR calculation before cap/guard returns.
- Cap skips now write real `actual_rr` and `spread_points` instead of `0`.
- Runtime JSON now also writes `balance`, `equity`, `floating_profit`, `bid`, `ask`, and `terminal_trade_allowed`.
- Copied v4.03 to Desktop and MT5 Experts folder as `AtsawinEA.mq5` and `AtsawinEA_v4.mq5`.

### Validation
- MetaEditor compile log showed 0 errors, 0 warnings for Experts canonical, Experts versioned, and Desktop versioned files.
- `.ex5` artifacts updated in Experts and Desktop.
- Runtime file still showed v4.02 afterward; user must reattach/restart EA in MT5 to activate v4.03.

---

## Session 2026-06-03 11:45 SEAST: Virtual Office UI + Task Engine Wiring

### Change Applied
- **Files**: `backend/office_store.py`, `backend/office_router.py`, `frontend/virtual-office.html`, `tests/test_office_task_engine.py`
- Added `route_command_reply(text, store)` as the first read-only local task engine.
- Safe commands now return data-aware replies for:
  - MT5/EA live status
  - Daily Brief
  - Approval Board list
- Risky commands still enter `waiting_owner_approval` and now include approval context in chat reply.
- Frontend now displays Local OS Core data:
  - Office Overview: Journal counters, Daily Brief Agent, Approval Queue
  - Approval Board: backend-driven approve/reject buttons
  - Journal / SOP: SQLite counters
  - Daily Brief: recommendation + skip reason table
- Menu labels updated to Approval Board / Journal-SOP / Daily Brief.

### Validation
- `python -m py_compile backend/office_store.py backend/office_router.py backend/main.py` passed.
- `python -m pytest tests/test_office_store.py tests/test_office_router.py tests/test_office_task_engine.py -q` → 9 passed.
- JS syntax check via Node passed.
- Live API safe command returned MT5/EA summary from journal.
- Browser verification: Office Overview LIVE OS, Daily Brief card, Approval Board page, risky command UI flow; browser console `total_errors=0`.
- Verification risky command `buy XAUUSD now` was rejected immediately with note `UI verification only - do not trade`.

---

## Session 2026-06-03 (Builder Agent): Code Review False-Positive Fix

### Root Cause
`_code_review.py` had a false-positive in its ORDER_FILLING fallback check (line 88). The check used `'FOK' in l or 'RETURN' in l` which matched any line containing those substrings — including `return INIT_SUCCEEDED;` and `return false;`. This caused the script to report "OK — ORDER_FILLING_IOC with FOK/RETURN fallback" for `AtsawinEA.mq5` which has NO fallback chain (only `ORDER_FILLING_IOC` at line 340 with `trade.SetTypeFilling()`).

### Fix Applied
- **File**: `_code_review.py` line 88
  - Changed: `any('FOK' in l or 'RETURN' in l for l in lines)`
  - To: `any('ORDER_FILLING_FOK' in l or 'ORDER_FILLING_RETURN' in l for l in lines)`
  - Now correctly checks for the full `ORDER_FILLING_FOK` / `ORDER_FILLING_RETURN` constants

### Impact
- Code review now correctly reports: `ORDER_FILLING_IOC without fallback may fail on some brokers`
- Previous run was false-positive "OK" — the EA has no fallback chain
- Exness broker currently supports IOC (no failures observed), but this is a portability risk for other brokers
- No behavior change in runtime code; this is a diagnostic accuracy fix

### Validation
- `python _code_review.py` → Now correctly reports missing fallback for AtsawinEA.mq5:340
- `python -m pytest ea/tests/ -v` → 38/38 passed (no regression)
- `python _review_check.py` → All signal contract checks PASS
- `python -m py_compile _code_review.py` → SYNTAX OK

---

## Session 2026-06-03 (Builder Agent): Repo Root Bridge Sync

### Root Cause
The repo root `bridge_mt5_pro.py` (1204 lines) was 119 lines behind `ea/bridge_mt5_pro.py` (1323 lines) and the Desktop deployed copy. Missing from the repo root copy:
- `_acquire_lock()` / `_release_lock()` PID-based file lock mechanism
- `session_opt_min_hours` and `session_opt_min_pnl_r` CONFIG safety floors
- Session optimization floor/pnl rejection logic in `optimize_session_hours_from_trade_log()`
- `max_consecutive_errors=10` error recovery loop in `main()`
- `symbol_info()` None guard in `scan_once()`
- `lock_file` CONFIG entry

Tests (`test_atomic_write_fix.py`, `test_validate_payload_fix.py`) import from the repo root copy, so running them against the stale version would test code without critical safety features.

### Fix Applied
- **File**: `bridge_mt5_pro.py` (repo root) — synced with `ea/bridge_mt5_pro.py`
  - Copied `ea/bridge_mt5_pro.py` → `bridge_mt5_pro.py` to bring all 1323 lines into sync
  - Now all three copies (repo root, ea/, Desktop) are byte-identical

### Impact
- Tests that import from repo root now test the correct version with all safety features
- If someone accidentally runs the repo root version, it now includes lock, session safety, and error recovery
- No runtime behavior change (Desktop deployed copy was already correct)

### Validation
- `diff ea/bridge_mt5_pro.py bridge_mt5_pro.py` → IDENTICAL
- `diff Desktop/bridge_mt5_pro.py ea/bridge_mt5_pro.py` → IDENTICAL
- `python -m py_compile ea/bridge_mt5_pro.py` → SYNTAX OK
- `python -m py_compile bridge_mt5_pro.py` → SYNTAX OK
- `python -m pytest ea/tests/ -v` → 38/38 passed
- `python -m pytest tests/test_atomic_write_fix.py tests/test_validate_payload_fix.py tests/test_bridge_fix.py -v` → 8/8 passed

---

## Session 2026-06-03 09:03 SEAST: Daily Maintenance Check

### Checked
- Loaded memory docs: spec.md, architecture.md, system_state.md, hot.md, hoting_old_knowledge.md, brain/agent_registry.md, brain/task_queue.md.
- Host runtime tools: python 3.14.5, pip 26.1.1, uv 0.11.17, git 2.54.0.windows.1, node v22.22.3; docker is still missing.
- backend/requirements.txt is present; import scan excluding venv folders found only one likely undeclared direct third-party import: `pydantic` in `backend/auth/models.py` and `backend/office_router.py`.
- Trading bridge readiness files are present: `C:/Users/Administrator/Desktop/bridge_mt5_pro.py` and Common Files `atsawin/latest_signal.json`.
- Latest signal: contract v2.1 `sell` for XAUUSDm, confidence 1.0, spread 280.0 points, timestamp 2026-06-03T02:03:16.165469+00:00.

### Follow-up
- Add direct `pydantic` requirement or explicitly document FastAPI-transitive reliance.
- Install/enable Docker if local docker-compose validation is required.

---

## Session 2026-06-03 08:35 SEAST: Virtual Office Local OS Core

### Change Applied
- **Files**: `backend/office_store.py`, `backend/office_router.py`, `tests/test_office_store.py`, `tests/test_office_router.py`
- Added local SQLite journal at `data/office_journal.db` for:
  - MT5 signal snapshots
  - EA runtime decisions
  - command logs
  - approval queue
- Added daily brief generation from journal state:
  - latest signal context
  - latest EA decision/reason
  - skip reason summary
  - recommendation text
- Added approval endpoints:
  - `GET /api/office/approvals`
  - `POST /api/office/approvals/{approval_id}/approve`
  - `POST /api/office/approvals/{approval_id}/reject`
- `POST /api/office/command` now stores commands in SQLite and auto-queues risky actions as `waiting_owner_approval`.

### Validation
- `python -m py_compile backend/office_store.py backend/office_router.py backend/main.py` passed.
- `python -m pytest tests/test_office_store.py tests/test_office_router.py -q` → 6 passed.
- Live `GET /api/office/status` returned `journal`, `daily_brief`, and `approvals`.
- Risky command verification created an approval and was immediately rejected as verification-only; no trade execution was added.

### Known Follow-up
- Frontend script update to show the new journal/brief/approval widgets was attempted but blocked by tool approval timeout; backend/API layer is ready for UI wiring.

---

## Session 2026-06-03 07:14 SEAST: Virtual Office UI Reference Redesign

### Change Applied
- **File**: `frontend/virtual-office.html`
- Rebuilt the dashboard to match the supplied Benz Office / Trading Cafe style reference:
  - left Benz Virtual Office sidebar
  - top integration bar (Codex/Local, Notion, Drive, Gmail, Google Ads, Facebook)
  - central pixel/isometric-style Agent Live Map with 6 rooms and agents
  - right Team Chat panel with selected agent, quick actions, and command composer
  - working pages for Office Overview, Chat Center, Characters, Workflow Board, Skills/SOP, Reports, Settings
  - responsive mobile / Telegram Mini App layout with bottom tabs and safe-area handling

### Validation
- JS syntax check via Node: passed.
- Browser interaction check: all 7 pages rendered, chat/quick command interactions worked.
- Browser console: `js_errors=[]`, `total_errors=0`.
- Chrome headless screenshots generated for desktop and mobile.

---

## Session 2026-06-03 (06:xx): Builder Agent — symbol_info() None Guard Fix

### Root Cause
`scan_once()` calls `mt5.symbol_info(symbol).point` without checking if `symbol_info()` returns `None`. During MT5 reconnection, symbol list refresh, or temporary API hiccups, `symbol_info()` can return `None`, causing `AttributeError: 'NoneType' object has no attribute 'point'`. This crashes `scan_once()`, increments the error counter, and eventually shuts down the bridge after 10 consecutive errors — leaving the EA without signal updates.

### Fix Applied
- **File**: `ea/bridge_mt5_pro.py` + `bridge_mt5_pro.py` (synced to Desktop)
  - Stored `mt5.symbol_info(symbol)` result in `sym_info` variable
  - Added `if sym_info is None: return None` guard before accessing `.point`
  - Pattern is consistent with existing `tick is None` / `rates is None` guards

### Impact
- Bridge no longer crashes on temporary MT5 symbol_info unavailability
- Transient API issues (reconnect, refresh) are silently skipped instead of counting toward the 10-error shutdown threshold
- Consistent with existing defensive programming patterns in scan_once()

### Validation
- `python -m pytest ea/tests/ -v` → 38/38 passed (35 existing + 3 new)
- `python -m py_compile ea/bridge_mt5_pro.py` → SYNTAX OK
- Desktop copy synced: diff → IDENTICAL
- New test `ea/tests/test_symbol_info_guard.py` covers: None guard present, point access via sym_info variable, syntax check

---

## Session 2026-06-03 (04:xx): Builder Agent — Error Recovery Regression Fix + Desktop Sync

### Root Cause
The repo copy of `bridge_mt5_pro.py` had the lock mechanism and session safety features, but the **Desktop copy** (which is the actually deployed/running version) was 128 lines behind — missing `_acquire_lock`, `_release_lock`, `session_opt_min_hours/pnl_r`, session safety floors, and atomic write retry logic. Two concurrent bridge instances (PIDs 8912, 13096) were running from the Desktop copy without any lock, causing duplicate signal writes every ~30s.

Additionally, the repo copy's `main()` loop had **no error recovery** — a single `scan_once()` exception would crash the bridge and release the lock. The Desktop copy had `max_consecutive_errors=10` handling that was lost in the repo refactor.

### Fix Applied
- **File**: `ea/bridge_mt5_pro.py` (repo) → synced to `Desktop/bridge_mt5_pro.py`
  - Restored `max_consecutive_errors=10` error recovery loop inside the `try/finally` block
  - The `finally` block still releases the lock on exit (whether normal or error)
  - On consecutive errors ≥ 10: logs error, breaks loop, releases lock, shuts down MT5
- **Deployment**: Copied repo version to Desktop to match running code with repo

### Impact
- Bridge now survives transient errors (MT5 API timeouts, network issues) without crashing
- Lock mechanism prevents future concurrent instances (when bridge is restarted)
- Session safety floors prevent aggressive optimization from starving live bridge
- Atomic write retry prevents signal file corruption when MQL5 EA has file locked

### Validation
- `python -m py_compile ea/bridge_mt5_pro.py` → SYNTAX OK
- `python -m pytest ea/tests/ -v` → 35/35 passed
- `python ea/bridge_mt5_pro.py --health` → account_ok=True symbol_tick_ok=True
- `python ea/bridge_mt5_pro.py --once` → SELL conf=1.00 spread=280.0 lot=0.02 rr=1.4
- Desktop copy synced: diff → IDENTICAL

---

## Session 2026-06-02 (21:xx): Builder Agent — Concurrent Bridge Lock Fix

### Root Cause
Log analysis revealed two bridge instances running concurrently — signals at :15 and :20 per minute with different IDs and directions (SELL without `id=` field, BUY with `id=` field). This caused conflicting `latest_signal.json` writes, wasted MT5 API slots, and could confuse the EA with rapid signal direction changes.

### Fix Applied
- **File**: `ea/bridge_mt5_pro.py`
  - Added `_acquire_lock()` / `_release_lock()` functions using PID-based file lock at `atsawin/bridge_mt5_pro.lock`
  - Lock uses `ctypes.windll.kernel32.GetExitCodeProcess` to check if the holding PID is still alive (STILL_ACTIVE=259)
  - Stale lock files (PID not running) are automatically reclaimed
  - Lock is acquired only for continuous/once live-scan modes, not for --backtest/--autotune/--health etc.
  - Lock is released in a `finally` block to prevent stale locks on crash
  - Added `lock_file` entry to CONFIG

### Impact
- Prevents duplicate concurrent bridge instances from running
- Eliminates conflicting signal writes to `latest_signal.json`
- Future bridge restarts will detect if a previous instance is still running

### Validation
- `python -m pytest ea/tests/ -v` → 30/30 passed (25 existing + 5 new lock tests)
- `python -m py_compile ea/bridge_mt5_pro.py` → SYNTAX OK

---

## Session 2026-06-03 (02:xx): Builder Agent — Session Optimization Safety Guard

### Root Cause
`optimize_session_hours_from_trade_log()` mutated `CONFIG["session_hours_utc"]` from `[0,1,5,10,13,14]` (6 hours) down to `[0,5]` (2 hours). The live bridge inherited this aggressive filter, causing `HOLD conf=0.00` for 20+ minutes because the current UTC hour (18-19) was outside the allowed window. No safety floor existed to prevent over-shrinking.

### Fix Applied
- **File**: `ea/bridge_mt5_pro.py`
  - Added `session_opt_min_hours: 5` and `session_opt_min_pnl_r: -2.0` to CONFIG
  - `optimize_session_hours_from_trade_log()` now rejects selections with fewer than 5 hours (keeps old hours)
  - Also rejects selections where total PnL_r across selected hours is below -2.0
  - Live bridge main loop resets session hours to default `[0,1,5,10,13,14]` if current hours < floor

### Impact
- Prevents session optimization from starving the live bridge of tradable hours
- Rejects statistically insignificant session windows (too few hours or too negative PnL)
- Belt-and-suspenders: both the optimizer and the live loop enforce the floor

### Validation
- `python -m pytest ea/tests/ -v` → 35/35 passed (30 existing + 5 new)
- New tests in `ea/tests/test_session_opt_safety.py` cover: CONFIG floor params, reset logic, reject too-few-hours, reject negative PnL, accept good selection

---

## Current Task
EMA bias test import fix: added missing `generate_signal` import to `tests/test_ema_bias_fix.py`.

## Session 2026-06-04 (Builder Agent): EMA Bias Test Import Fix

### Issue
`tests/test_ema_bias_fix.py` had 4 failing tests because `generate_signal` was only imported inside the `if __name__ == "__main__":` block (line 137), not at module level. Pytest collects and runs tests at module level, so `generate_signal` was `NameError: name 'generate_signal' is not defined`.

### Root Cause
The import on line 19 was:
```python
from ea.bridge_mt5_pro import Signal, CONFIG
```
Missing: `generate_signal`.

### Fix Applied
- **File**: `tests/test_ema_bias_fix.py` line 19
  - Changed: `from ea.bridge_mt5_pro import Signal, CONFIG`
  - To: `from ea.bridge_mt5_pro import Signal, CONFIG, generate_signal`

### Impact
- 4 tests now pass: `test_no_unearned_ema_bias_when_price_near_ema`, `test_ema_gap_when_price_clearly_above`, `test_ema_gap_when_price_clearly_below`, `test_signal_does_not_flip_on_tiny_ema_crossing`
- These tests validate the EMA-price bias fix (only award ±0.5 score when price diverges from fast EMA by >15% of ATR, not on tiny noise)
- Full suite: 75/75 passed (58 ea/tests + 17 root tests)

### Validation
- `python -m pytest tests/test_ema_bias_fix.py -v` → 4/4 passed
- `python -m pytest ea/tests/ tests/test_*.py -v` → 75/75 passed in 33.54s
- `python -m py_compile tests/test_ema_bias_fix.py` → SYNTAX OK

---

## Session 2026-06-02 17:45 SEAST: Bridge/EA Contract v2.1 + EA v3.24
- Root cause/risk found: bridge JSON was UTF-8 while EA read ANSI; EA only polled on new candle; signal file lacked stable signal_id/expiry; EA had no machine-readable runtime status for why it skipped/executed.
- Updated `ea/bridge_mt5_pro.py`:
  - Signal contract `schema_version=2.1`, `contract=atsawin_mt5_signal`.
  - Adds `signal_id`, `setup_key`, `timestamp_epoch`, `expires_at_epoch`, source `bridge_mt5_pro_v2.1`.
  - Atomic writes are ASCII-safe (`ensure_ascii=True`) for MQL5 `FILE_ANSI` reader.
  - `ea_status.json` now includes signal_id/setup_key/symbol/timeframe/RR/spread/reasons/expiry.
- Updated legacy `ea/atsawin_bridge.py` to emit compatible v2.1 fields so accidentally running the old bridge does not break EA parsing.
- Updated `ea/AtsawinEA.mq5` to v3.24:
  - Polls by `InpPollSeconds=30` instead of only once per new bar.
  - Blocks stale signals using `expires_at_epoch` / `timestamp_epoch` and `InpMaxSignalAgeSec=150`.
  - Blocks repeat execution of the same successful `signal_id` by default (`InpAllowRepeatSameSignal=false`).
  - Writes Common `atsawin/ea_runtime_status.json` on skip/execute/fail with reason, RR, spread, position counts, trade_allowed.
  - Keeps existing safety guards: symbol match, confidence, spread, hard magic cap, symbol cap, basket loss, entry gap, actual live RR.
- Validation:
  - `python -m pytest ea/tests/ -v` → 25/25 passed.
  - `python -m py_compile ea/bridge_mt5_pro.py ea/atsawin_bridge.py` → passed.
  - MetaEditor compile `AtsawinEA.mq5` → Result: 0 errors, 0 warnings, EX5 size 53614.
  - Deployed `AtsawinEA.mq5/.ex5` to `C:\Users\Administrator\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Experts`.
  - Ran `python ea/bridge_mt5_pro.py --once`; wrote BUY XAUUSDm contract v2.1 to Common `latest_signal.json`.

## Session 2026-06-02 09:06 SEAST: Daily Maintenance Check
- Loaded memory docs and agent registry/task queue.
- Host tools available: python 3.14.5, pip 26.1.1, uv 0.11.17, git 2.54.0.windows.1, node v22.22.3.
- Docker remains missing on current host.
- Dependency drift: backend imports `pydantic` in `auth/models.py`, but backend/requirements.txt does not declare it directly.
- Trading bridge files present; latest signal is sell XAUUSDm with confidence 1.0, RR 1.56, spread 308.0 points, timestamp 2026-06-02T02:00:56.135438+00:00.

## Session 2026-06-01: Local Health + Validation Pass

### Checked
- Loaded repo memory files: spec.md, hot.md, architecture.md, system_state.md, hoting_old_knowledge.md, AI/contracts.
- Host status: Windows 10, C: disk ~56% used / ~22GB free, CPU reported 100%, free RAM ~1.5GB of ~6GB.
- MT5 bridge active: `C:\Users\Administrator\Desktop\bridge_mt5_pro.py`.
- MT5 connected to Exness trial login 433684944; XAUUSDm tick OK.
- Current XAUUSDm open positions: 4 SELL positions, all actual RR above 1.4 at check time.
- Latest signal JSON: SELL, confidence 0.763, RR 1.56, spread 308 points.

### Validation Results
- Repo `.venv` dependency sync via `uv pip install -r backend/requirements.txt` completed.
- Selected `py_compile` checks passed for backend core files.
- Package imports passed for `backend.main`, `backend.trading.analysis`, `backend.memory_manager`, `backend.event_system.event_system_manager`, `backend.system.endpoints`.

### Blockers / Warnings
- Docker missing on host, so docker-compose validation cannot run locally.
- PostgreSQL localhost:5433 refused connection during backend import; API runtime not fully validated.
- PyMuPDF/fitz native import fails in `.venv` with DLL load failure (`_extra`); fixed PDF extraction path by adding pypdf fallback and regression test
- Local FastAPI smoke test started on 127.0.0.1:8000 and `/health` + `/models` returned OK
- PostgreSQL/Redis processes are not running locally; docker-compose.yml expects Docker containers (`postgres:5433`, `redis:6380`)

---

## Session 2026-06-01: Builder Agent — Stochastic Bug Fix

### Bugs Found & Fixed
1. **calculate_stochastic() tuple iteration bug** — `for i in period - 1, len(candles)` creates a tuple `(period-1, len(candles))` instead of a range. Only iterates twice (i=13 and i=20 for 20 candles), with i=20 causing IndexError. Fixed to `for i in range(period - 1, len(candles))`.
   - File: `backend/trading/analysis.py` line 157
   - Impact: Stochastic oscillator (1 of 6 composite strategies) was broken → degraded signal quality → low win rate (20-40%) and negative PnL
   - Validation: Unit test confirmed 5 correct values for 20 candles with period=14, all in 0-100 range

### Signal Quality Observations
- latest_signal.json: HOLD confidence=0.0, reasons=["trend_down","confirm_up","out_of_session"]
- bridge_mt5_pro.log(138 lines): SELL signals XAUUSDm conf=0.71-0.98, spread=308
- Backtest: winrate 20-40%, pnl_r=-16.31 to +1.04, 1200+ skipped trades
- Walkforward: mixed, trades=0-5 per window

---

## Session 2026-06-02 (09:xx): Builder Agent — Config Sync + Dual-Penalty Fix

### Root Cause Analysis
1. **Stale CONFIG defaults**: Autotune found best params `ema_fast=30, ema_slow=40, atr_sl_mult=2.0, atr_tp_mult=2.8` but hardcoded CONFIG still had old values `ema_fast=12, atr_sl_mult=1.8`. Every restart reverts to unoptimized params.
2. **Double-penalty on threshold**: `sig_threshold = max(1.5, 1.9 - chop_penalty)` only accounted for chop_penalty but NOT session_out_penalty. Signal scores are reduced by both penalties but threshold only compensated for one.

### Fix Applied
- **File**: `ea/bridge_mt5_pro.py`
  - Updated CONFIG defaults: `ema_fast: 12→30`, `atr_sl_mult: 1.8→2.0` (matching autotune best)
  - Line 268: `sig_threshold = max(1.5, 1.9 - chop_penalty)` → `max(1.5, 1.9 - chop_penalty - out_penalty)`
  - `out_penalty` initialized to `0.0` outside session filter block so it's always defined

### Impact
- Bridge now starts with optimized parameters (no need to re-autotune after restart)
- During out-of-session hours: signals scoring ~1.65 after dual-penalties now pass threshold (1.55) instead of failing (1.7)
- Backward compatible: in-session `out_penalty=0.0`, hard mode unchanged

### Validation
- `python ea/tests/test_config_and_threshold_fix.py` → 7/7 tests passed
- Syntax check: SYNTAX OK

---

## Session 2026-06-02 (10:xx): Builder Agent — Autotune Grid Fix

### Root Cause
Autotune found best params `ema_fast=30, atr_sl_mult=2.0` but the search grids in both `autotune_parameters()` and `find_best_params_on_rates()` only included `[12, 20]` for ema_fast and `[1.6, 1.8]` for atr_sl_mult — the proven-best values were never in the search space.

### Fix Applied
- **File**: `ea/bridge_mt5_pro.py`
  - `autotune_parameters()` grid: `ema_fast: [12, 20] → [12, 20, 30]`, `atr_sl_mult: [1.6, 1.8] → [1.6, 1.8, 2.0]`
  - `find_best_params_on_rates()` grid: same update (walkforward uses identical grid)

### Impact
- Future autotune/walkforward runs can now discover the proven-best parameters
- Backward compatible: old grid values still included (superset)
- Prevents silent regression where re-running autotune would revert to suboptimal params

### Validation
- `python ea/tests/test_grid_fix.py` → 4/4 tests passed
- `python ea/tests/test_config_and_threshold_fix.py` → 7/7 tests passed (existing, no regression)

---

## Session 2026-06-02 (14:xx): Builder Agent — Multi-Bar Backtest Fix

### Root Cause
Both `run_backtest()` and `backtest_metrics()` only checked the **single next bar** for SL/TP hits. If neither was hit in that one bar, the trade was discarded as "skip". This caused 1220/1470 bars (83%) to be skipped, massively understating trade outcomes and producing unreliable autotune results.

### Fix Applied
- **File**: `ea/bridge_mt5_pro.py`
  - Added `evaluate_trade()` helper: holds a trade for up to `max_hold_bars` (48 bars = 12h on M15) checking each subsequent bar for SL/TP hits
  - Added same-bar SL/TP disambiguation using midpoint proximity (avoids lookahead bias)
  - Replaced single-bar logic in `run_backtest()` with `evaluate_trade()` call
  - Replaced single-bar logic in `backtest_metrics()` (used by autotune + walkforward) with same helper
  - Added `max_hold_bars: 48` to CONFIG
  - Loops now leave `max_hold + 2` tail room to prevent index out of bounds
  - Expired trades (SL/TP not hit within max_hold) now get realized PnL from close price at expiry

### Impact
- Backtest now correctly holds trades for multiple bars (was: 1-bar lookahead → 83% skip rate)
- Autotune/walkforward results now reflect actual trade outcomes (fewer misleading "skips")
- Expired trades get partial credit/debit instead of zero, giving accurate PnL_r

### Validation
- `python -m pytest ea/tests/ -v` → 21/21 tests passed (11 existing + 10 new)
- New tests in `ea/tests/test_evaluate_trade.py` cover: buy TP/SL hit, sell TP/SL hit, expired, same-bar disambiguation, immediate hit, zero max_hold

### Remaining Observations
- latest_signal.json shows BUY with RSI=87.2 (overbought) — the signal scoring allows buy to win if trend+confirm outweigh RSI overbought penalty; could add RSI extreme veto in future
- Signal direction in latest_signal.json (BUY) differs from bridge log (all SELL) — may be normal as market conditions change between runs





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
- Autonomous control upgrade: memory-first workflow, agent registry, workspace/dependency intelligence.
- Completed this cycle:
  - Added .env.example template at repo root
  - Updated backend/requirements.txt with aiohttp, psutil, PyMuPDF
  - Recorded runtime parity note (host 3.14 vs docker 3.12)
- Next: install Docker toolchain on host, then run validation cycle.

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
