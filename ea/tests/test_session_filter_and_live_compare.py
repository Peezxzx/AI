import csv
import json
import os
import tempfile
from datetime import datetime, timezone

import ea.bridge_mt5_pro as bridge


def _write_trade_log(rows):
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8", newline="")
    writer = csv.DictWriter(tmp, fieldnames=[
        "timestamp", "bar_index", "symbol", "timeframe", "side", "entry", "stop_loss",
        "take_profit", "rr", "confidence", "outcome", "pnl_r", "reason"
    ])
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    tmp.close()
    return tmp.name


def test_bad_hour_penalty_map_flags_negative_hours_only():
    path = _write_trade_log([
        {"timestamp": "2026-06-02T13:15:00+00:00", "bar_index": 1, "symbol": "XAUUSDm", "timeframe": "M15", "side": "buy", "entry": 1, "stop_loss": 0.9, "take_profit": 1.2, "rr": 1.4, "confidence": 0.8, "outcome": "loss", "pnl_r": -1.0, "reason": "sl_hit"},
        {"timestamp": "2026-06-02T13:30:00+00:00", "bar_index": 2, "symbol": "XAUUSDm", "timeframe": "M15", "side": "buy", "entry": 1, "stop_loss": 0.9, "take_profit": 1.2, "rr": 1.4, "confidence": 0.8, "outcome": "loss", "pnl_r": -1.0, "reason": "sl_hit"},
        {"timestamp": "2026-06-02T13:45:00+00:00", "bar_index": 3, "symbol": "XAUUSDm", "timeframe": "M15", "side": "buy", "entry": 1, "stop_loss": 0.9, "take_profit": 1.2, "rr": 1.4, "confidence": 0.8, "outcome": "win", "pnl_r": 1.4, "reason": "tp_hit"},
        {"timestamp": "2026-06-02T08:15:00+00:00", "bar_index": 4, "symbol": "XAUUSDm", "timeframe": "M15", "side": "sell", "entry": 1, "stop_loss": 1.1, "take_profit": 0.8, "rr": 1.4, "confidence": 0.8, "outcome": "win", "pnl_r": 1.4, "reason": "tp_hit"},
        {"timestamp": "2026-06-02T08:30:00+00:00", "bar_index": 5, "symbol": "XAUUSDm", "timeframe": "M15", "side": "sell", "entry": 1, "stop_loss": 1.1, "take_profit": 0.8, "rr": 1.4, "confidence": 0.8, "outcome": "win", "pnl_r": 1.4, "reason": "tp_hit"},
        {"timestamp": "2026-06-02T08:45:00+00:00", "bar_index": 6, "symbol": "XAUUSDm", "timeframe": "M15", "side": "sell", "entry": 1, "stop_loss": 1.1, "take_profit": 0.8, "rr": 1.4, "confidence": 0.8, "outcome": "loss", "pnl_r": -1.0, "reason": "sl_hit"},
    ])
    try:
        penalties = bridge.build_bad_hour_penalty_map(path, min_trades=3, max_penalty=0.35)
        assert penalties[13]["penalty"] > 0
        assert penalties[13]["pnl_r"] < 0
        assert 8 not in penalties
    finally:
        os.unlink(path)


def test_apply_session_hour_quality_penalty_reduces_leading_score():
    penalties = {13: {"penalty": 0.25, "pnl_r": -1.6, "winrate": 33.3, "trades": 3}}
    buy, sell, penalty, reason = bridge.apply_session_hour_quality_penalty(2.0, 1.0, 13, penalties)
    assert buy == 1.75
    assert sell == 1.0
    assert penalty == 0.25
    assert reason == "bad_hour_penalty_h13"


def test_compare_live_execution_report_flags_execution_gaps():
    backtest_summary = {"winrate": 49.38, "pnl_r": 225.38, "trades": 1124}
    live_stats = {"winrate": 34.55, "net_profit": -338.27, "trades": 55}
    runtime = {"spread_points": 280.0, "actual_rr": 0.82, "magic_positions": 3, "symbol_positions": 3, "decision": "SKIP", "reason": "hard_magic_cap"}
    report = bridge.build_live_execution_comparison_report(backtest_summary, live_stats, runtime, configured_max_spread=450)
    assert report["winrate_gap_pct"] == -14.83
    assert report["diagnostics"]["spread_real"]["status"] == "ok"
    assert report["diagnostics"]["actual_rr"]["status"] == "bad"
    assert report["diagnostics"]["max_position_stacking"]["status"] == "bad"
