import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "bridge_mt5_pro.py"

spec = importlib.util.spec_from_file_location("bridge_mt5_pro", MODULE_PATH)
bridge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bridge)


def test_signal_fingerprint_is_stable_for_same_setup():
    payload = {
        "mt5_symbol": "XAUUSDm",
        "timeframe": "M15",
        "signal": "sell",
        "entry_price": 3380.123,
        "stop_loss": 3390.456,
        "take_profit": 3360.789,
        "confidence": 0.7654,
    }
    assert bridge.signal_fingerprint(payload) == bridge.signal_fingerprint(dict(payload))
    assert bridge.signal_fingerprint(payload).startswith("XAUUSDm|M15|sell|")


def test_signal_fingerprint_changes_when_geometry_changes():
    a = {
        "mt5_symbol": "XAUUSDm",
        "timeframe": "M15",
        "signal": "buy",
        "entry_price": 3380.0,
        "stop_loss": 3370.0,
        "take_profit": 3400.0,
        "confidence": 0.7,
    }
    b = dict(a)
    b["take_profit"] = 3401.0
    assert bridge.signal_fingerprint(a) != bridge.signal_fingerprint(b)


def test_hold_payload_contains_ea_contract_fields():
    sig = bridge.Signal("hold", 0, 3380, 0, 0, 0, 3.2, 50, 3375, 3370, ["ทดสอบ"])
    payload = bridge.build_hold_payload("validation_failed:test", sig, "XAUUSDm", 308.2, 0.308)
    assert payload["schema_version"] == "2.4"
    assert payload["strategy_version"] == "bridge_mt5_pro_v2.4_fvg_fib_rsi"
    assert payload["contract"] == "atsawin_mt5_signal"
    assert payload["signal_id"] == payload["setup_key"]
    assert payload["timestamp_epoch"] > 0
    assert payload["expires_at_epoch"] > payload["timestamp_epoch"]
    assert payload["mt5_symbol"] == "XAUUSDm"


def test_atomic_write_is_ascii_safe_for_mql5_ansi_reader(tmp_path):
    out = tmp_path / "latest_signal.json"
    bridge.atomic_write(out, {"signal": "hold", "reasons": ["ภาษาไทย"], "confidence": 0})
    raw = out.read_bytes()
    raw.decode("ascii")
    data = json.loads(raw.decode("ascii"))
    assert data["reasons"] == ["ภาษาไทย"]
