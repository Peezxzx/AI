# MT5 Signal Contract v2.4

File: `%APPDATA%/MetaQuotes/Terminal/Common/Files/atsawin/latest_signal.json`

Producer: `ea/bridge_mt5_pro.py` / `bridge_mt5_pro.py` / Desktop deployed bridge with `source=bridge_mt5_pro_v2.4_fvg_fib_rsi`.

Consumer: `ea/AtsawinEA.mq5` v3.24+ / v4.x.

## Compatibility

v2.4 is backward-compatible for the current EA: all EA-required execution fields are unchanged. New strategy fields are additive metadata and can be ignored by older EA parsers.

## Required execution fields

- `schema_version`: `"2.4"`
- `contract`: `"atsawin_mt5_signal"`
- `signal`: `"buy" | "sell" | "hold"`
- `confidence`: float 0.0-1.0
- `symbol`: base symbol, e.g. `XAUUSD`
- `mt5_symbol`: broker symbol, e.g. `XAUUSDm`
- `timeframe`: e.g. `M15`
- `confirm_timeframe`: e.g. `H1`
- `entry_price`: signal-generation price
- `stop_loss`: 0 for hold, positive for buy/sell
- `take_profit`: 0 for hold, positive for buy/sell
- `risk_reward_ratio`: bridge-side RR at signal-generation price
- `timestamp`: ISO timestamp
- `timestamp_epoch`: UTC epoch seconds for MQL5 age checks
- `expires_at_epoch`: UTC epoch seconds when EA must stop using the signal
- `setup_key`: stable fingerprint of mt5_symbol/timeframe/signal/entry/SL/TP/confidence/setup metadata
- `signal_id`: currently same as `setup_key`; EA uses it for duplicate execution guard

## Strategy metadata fields

- `strategy_version`: `bridge_mt5_pro_v2.4_fvg_fib_rsi`
- `setup_type`: `none` or `fvg_fib_rsi`
- `fvg_direction`: `none | bullish | bearish`
- `fvg_low`, `fvg_high`, `fvg_mid`, `fvg_age_bars`, `fvg_width`, `fvg_distance`
- `fib_nearest_ratio`, `fib_nearest_level`, `fib_distance`
- `rsi_divergence`: `none | regular_bullish | regular_bearish | hidden_bullish | hidden_bearish`
- `score_breakdown`: includes `buy_score`, `sell_score`, `edge`, `fvg_bonus`, `fib_bonus`, `rsi_divergence_bonus`, `chop_penalty`, `session_out_penalty`, `bad_hour_penalty`

## Safety rules

EA validates before any order:

1. `mt5_symbol` must match chart `_Symbol` when `InpEnforceSymbolMatch=true`.
2. Signal must not be expired (`expires_at_epoch`) or older than `InpMaxSignalAgeSec`.
3. Same successful `signal_id` is not executed twice when `InpAllowRepeatSameSignal=false`.
4. Confidence, SL/TP geometry, spread, position caps, basket loss, entry gap, and live actual RR all pass.
5. EA writes skip/execute/fail reason to Common `atsawin/ea_runtime_status.json`.

## Encoding

Bridge writes JSON with `ensure_ascii=True` so the file is ASCII-safe for MQL5 `FILE_ANSI` reads. Thai/non-ASCII text is escaped as JSON unicode sequences and still round-trips through Python JSON.

## ea_status.json fields

The status file (`%APPDATA%/MetaQuotes/Terminal/Common/Files/atsawin/ea_status.json`) is a mirror of the latest signal payload, written atomically alongside `latest_signal.json`. As of v2.4 it includes all strategy metadata fields needed by the EA dashboard:

- All required execution fields from `latest_signal.json`
- `strategy_version`, `setup_type`, `fvg_direction`, `fvg_low`, `fvg_high`, `fvg_mid`, `fvg_age_bars`, `fvg_width`, `fvg_distance`
- `fib_nearest_ratio`, `fib_nearest_level`, `fib_distance`
- `rsi_divergence`
- `score_breakdown`, `reasons`
