import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "bridge_mt5_pro.py"
spec = importlib.util.spec_from_file_location("bridge_mt5_pro", MODULE_PATH)
bridge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bridge)


def test_pdf_fib_ratios_are_available():
    assert bridge.PDF_FIB_RATIOS == [0.242, 0.57, 1.617, 3.097, 5.165, 7.044, 8.237]


def test_fib_levels_from_swing_low_to_high_include_pdf_ratios():
    levels = bridge.compute_fib_levels(100.0, 200.0)
    assert levels[0.57] == 157.0
    assert levels[1.617] == 261.7


def test_nearest_fib_level_finds_pdf_ratio_near_price():
    nearest = bridge.nearest_fib_level(156.8, bridge.compute_fib_levels(100.0, 200.0))
    assert nearest["ratio"] == 0.57
    assert nearest["level"] == 157.0
    assert nearest["distance"] == 0.2


def test_fib_metadata_can_merge_with_fvg_payload():
    meta = bridge.fib_payload_metadata({"ratio": 0.57, "level": 157.0, "distance": 0.2})
    assert meta["fib_nearest_ratio"] == 0.57
    assert meta["fib_nearest_level"] == 157.0
    assert meta["fib_distance"] == 0.2
