import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "bridge_mt5_pro.py"
spec = importlib.util.spec_from_file_location("bridge_mt5_pro", MODULE_PATH)
bridge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bridge)


def test_find_pivot_lows_returns_recent_local_lows():
    values = [10, 9, 11, 8, 12, 7, 13]
    assert bridge.find_pivots(values, kind="low", left=1, right=1) == [1, 3, 5]


def test_find_pivot_highs_returns_recent_local_highs():
    values = [10, 12, 9, 13, 8, 14, 7]
    assert bridge.find_pivots(values, kind="high", left=1, right=1) == [1, 3, 5]


def test_detect_regular_bullish_rsi_divergence():
    closes = [100, 98, 101, 96, 102, 94, 103]
    rsi_values = [45, 30, 48, 35, 50, 42, 55]
    assert bridge.detect_rsi_divergence(closes, rsi_values) == "regular_bullish"


def test_detect_regular_bearish_rsi_divergence():
    closes = [100, 103, 99, 105, 98, 108, 97]
    rsi_values = [50, 70, 48, 64, 45, 58, 40]
    assert bridge.detect_rsi_divergence(closes, rsi_values) == "regular_bearish"


def test_detect_hidden_bullish_rsi_divergence():
    closes = [100, 95, 104, 98, 106, 101, 108]
    rsi_values = [50, 45, 55, 38, 57, 30, 60]
    assert bridge.detect_rsi_divergence(closes, rsi_values) == "hidden_bullish"


def test_detect_hidden_bearish_rsi_divergence():
    closes = [100, 110, 98, 107, 96, 104, 94]
    rsi_values = [45, 55, 40, 62, 38, 70, 35]
    assert bridge.detect_rsi_divergence(closes, rsi_values) == "hidden_bearish"


def test_rsi_divergence_metadata_shape():
    meta = bridge.rsi_divergence_payload_metadata("regular_bullish")
    assert meta == {"rsi_divergence": "regular_bullish"}
