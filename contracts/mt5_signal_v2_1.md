# MT5 Signal Contract v2.1

File: `%APPDATA%/MetaQuotes/Terminal/Common/Files/atsawin/latest_signal.json`

Producer: `ea/bridge_mt5_pro.py` (`source=bridge_mt5_pro_v2.1`) or compatible legacy `ea/atsawin_bridge.py` (`source=atsawin_bridge_v1.3`).

Consumer: `ea/AtsawinEA.mq5` v3.24+.

## Required fields

- `schema_version`: `"2.1"`
- `contract`: `"atsawin_mt5_signal"`
- `signal`: `"buy" | "sell" | "hold"`
- `confidence`: float 0.0-1.0
- `symbol`: base symbol, e.g. `XAUUSD`
- `mt5_symbol`: broker symbol, e.g. `XAUUSDm`
- `timeframe`: e.g. `M15`
- `entry_price`: signal-generation price
- `stop_loss`: 0 for hold, positive for buy/sell
- `take_profit`: 0 for hold, positive for buy/sell
- `risk_reward_ratio`: bridge-side RR at signal-generation price
- `timestamp`: ISO timestamp
- `timestamp_epoch`: UTC epoch seconds for MQL5 age checks
- `expires_at_epoch`: UTC epoch seconds when EA must stop using the signal
- `setup_key`: stable fingerprint of mt5_symbol/timeframe/signal/entry/SL/TP/confidence
- `signal_id`: currently same as `setup_key`; EA uses it for duplicate execution guard

## Safety rules

EA v3.24 validates before any order:

1. `mt5_symbol` must match chart `_Symbol` when `InpEnforceSymbolMatch=true`.
2. Signal must not be expired (`expires_at_epoch`) or older than `InpMaxSignalAgeSec`.
3. Same successful `signal_id` is not executed twice when `InpAllowRepeatSameSignal=false`.
4. Confidence, SL/TP geometry, spread, position caps, basket loss, entry gap, and live actual RR all pass.
5. EA writes skip/execute/fail reason to Common `atsawin/ea_runtime_status.json`.

## Encoding

Bridge writes JSON with `ensure_ascii=True` so the file is ASCII-safe for MQL5 `FILE_ANSI` reads. Thai/non-ASCII text is escaped as JSON unicode sequences and still round-trips through Python JSON.
