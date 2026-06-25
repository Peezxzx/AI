from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EA = ROOT / "AtsawinEA.mq5"
SRC = EA.read_text(encoding="utf-8")


def test_ea_version_bumped_to_404_and_trade_comment_updated():
    assert '#property version   "4.04"' in SRC
    assert 'ATSAWIN v4.04' in SRC
    assert 'Atsawin v4.04' in SRC


def test_signal_metadata_globals_exist_for_dashboard_and_status():
    for name in [
        "g_strategyVersion",
        "g_setupType",
        "g_fvgDirection",
        "g_fvgMid",
        "g_fibRatio",
        "g_fibLevel",
        "g_rsiDivergence",
    ]:
        assert name in SRC


def test_ea_parses_v24_strategy_metadata_from_signal_json():
    for key in [
        'JS(json, "strategy_version")',
        'JS(json, "setup_type")',
        'JS(json, "fvg_direction")',
        'JS(json, "fvg_mid")',
        'JS(json, "fib_nearest_ratio")',
        'JS(json, "fib_nearest_level")',
        'JS(json, "rsi_divergence")',
    ]:
        assert key in SRC


def test_runtime_status_writes_strategy_metadata():
    for key in [
        '\"strategy_version\"',
        '\"setup_type\"',
        '\"fvg_direction\"',
        '\"fvg_mid\"',
        '\"fib_nearest_ratio\"',
        '\"fib_nearest_level\"',
        '\"rsi_divergence\"',
    ]:
        assert key in SRC


def test_dashboard_shows_strategy_setup_fvg_fib_and_rsi_divergence():
    for label in ["STRATEGY", "FVG", "FIB", "RSI_DIV"]:
        assert f'SetDashLabel("{label}"' in SRC
