"""ATSAWIN Review Check — Signal contract + risk validation."""
import json
import sys

# 1. Read latest signal
try:
    signal = json.loads(open(
        'C:/Users/Administrator/AppData/Roaming/MetaQuotes/Terminal/Common/Files/atsawin/latest_signal.json'
    ).read())
except Exception as e:
    print(f"ERROR reading latest_signal.json: {e}")
    sys.exit(1)

print("=" * 60)
print("LATEST SIGNAL CONTRACT VALIDATION")
print("=" * 60)

required = [
    'schema_version', 'contract', 'signal', 'confidence', 'symbol',
    'mt5_symbol', 'timeframe', 'entry_price', 'stop_loss', 'take_profit',
    'risk_reward_ratio', 'timestamp', 'timestamp_epoch', 'expires_at_epoch',
    'setup_key', 'signal_id'
]

missing = [k for k in required if k not in signal]
if missing:
    print(f"FAIL: Missing required fields: {missing}")
else:
    print("PASS: All required fields present")

print(f"  schema_version: {signal.get('schema_version')}")
print(f"  contract: {signal.get('contract')}")
print(f"  source: {signal.get('source')}")
print(f"  signal: {signal.get('signal')}")
print(f"  confidence: {signal.get('confidence')}")
print(f"  symbol: {signal.get('symbol')}")
print(f"  mt5_symbol: {signal.get('mt5_symbol')}")
print(f"  timeframe: {signal.get('timeframe')}")
print(f"  setup_key == signal_id: {signal.get('setup_key') == signal.get('signal_id')}")

# 2. Validate confidence range
c = float(signal.get('confidence', -1))
if 0.0 <= c <= 1.0:
    print(f"PASS: Confidence {c} in [0, 1]")
else:
    print(f"FAIL: Confidence {c} out of range [0, 1]")

# 3. Validate sell/buy geometry
sig = signal.get('signal', 'hold')
entry = float(signal.get('entry_price', 0))
sl = float(signal.get('stop_loss', 0))
tp = float(signal.get('take_profit', 0))

if sig == 'buy':
    if sl < entry < tp:
        print(f"PASS: Buy geometry valid (sl={sl} < entry={entry} < tp={tp})")
    else:
        print(f"FAIL: Buy geometry invalid (sl={sl}, entry={entry}, tp={tp})")
elif sig == 'sell':
    if tp < entry < sl:
        print(f"PASS: Sell geometry valid (tp={tp} < entry={entry} < sl={sl})")
    else:
        print(f"FAIL: Sell geometry invalid (tp={tp}, entry={entry}, sl={sl})")
elif sig == 'hold':
    print(f"INFO: Hold signal (SL={sl}, TP={tp})")

# 4. Validate source
src = signal.get('source', '')
if src in ('bridge_mt5_pro_v2.1', 'atsawin_bridge_v1.3'):
    print(f"PASS: Source '{src}' is a known producer")
else:
    print(f"WARN: Unknown source '{src}'")

# 5. Validate all keys present in signal (no unexpected keys that EA can't parse)
optional_ok = {'atr', 'rsi', 'ema_fast', 'ema_slow', 'reasons', 'spread_points',
               'spread_price', 'position_size', 'confirm_timeframe', 'source',
               'risk_reward_ratio', 'position_size'}
all_expected = set(required) | optional_ok
unexpected = set(signal.keys()) - all_expected
if unexpected:
    print(f"WARN: Unexpected keys in signal (EA will ignore): {unexpected}")
else:
    print("PASS: No unexpected keys in signal")

print("=" * 60)
