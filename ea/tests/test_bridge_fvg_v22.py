import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "bridge_mt5_pro.py"

spec = importlib.util.spec_from_file_location("bridge_mt5_pro", MODULE_PATH)
bridge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bridge)


def test_detects_bullish_and_bearish_fvg_zones():
    highs = [10.0, 11.0, 12.0, 15.0, 14.0, 13.0]
    lows = [9.0, 10.0, 13.0, 14.0, 9.0, 8.0]
    closes = [9.5, 10.5, 13.5, 14.5, 9.5, 8.5]

    zones = bridge.detect_fvg_zones(highs, lows, closes, lookback=6)

    bullish = [z for z in zones if z.direction == "bullish"]
    bearish = [z for z in zones if z.direction == "bearish"]
    assert bullish, zones
    assert bearish, zones
    assert any(z.low == 10.0 and z.high == 13.0 and z.mid == 11.5 for z in bullish)
    assert any(z.low == 13.0 and z.high == 14.0 for z in bearish)


def test_nearest_active_fvg_prefers_matching_zone_near_price():
    zones = [
        bridge.FVGZone("bullish", low=3300.0, high=3310.0, mid=3305.0, index=10, age_bars=4, width=10.0, filled=False),
        bridge.FVGZone("bearish", low=3390.0, high=3400.0, mid=3395.0, index=11, age_bars=3, width=10.0, filled=False),
    ]

    z, distance = bridge.nearest_active_fvg(3306.0, zones, direction="bullish")

    assert z.direction == "bullish"
    assert distance == 1.0


def test_signal_fingerprint_changes_when_fvg_metadata_changes():
    base = {
        "mt5_symbol": "XAUUSDm",
        "timeframe": "M15",
        "signal": "buy",
        "entry_price": 3380.0,
        "stop_loss": 3370.0,
        "take_profit": 3400.0,
        "confidence": 0.7,
        "setup_type": "fvg_fib_rsi",
        "fvg_mid": 3378.0,
    }
    changed = dict(base)
    changed["fvg_mid"] = 3388.0

    assert bridge.signal_fingerprint(base) != bridge.signal_fingerprint(changed)


def test_build_hold_payload_contains_v22_strategy_metadata_defaults():
    sig = bridge.Signal("hold", 0, 3380, 0, 0, 0, 3.2, 50, 3375, 3370, ["no_fvg_setup"])
    payload = bridge.build_hold_payload("validation_failed:test", sig, "XAUUSDm", 300.0, 0.3)

    assert payload["schema_version"] == "2.4"
    assert payload["strategy_version"] == "bridge_mt5_pro_v2.4_fvg_fib_rsi"
    assert payload["setup_type"] in ("none", "fvg_fib_rsi")
    assert "score_breakdown" in payload
    assert "fvg_mid" in payload
