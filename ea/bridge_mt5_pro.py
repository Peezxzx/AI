import argparse
import csv
import json
import logging
import math
import os
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from logging.handlers import RotatingFileHandler
from pathlib import Path


def _acquire_lock(lock_path: str, log: logging.Logger) -> bool:
    """PID-based file lock — returns True if we acquired it, False if another instance is running."""
    p = Path(lock_path)
    if p.exists():
        try:
            old_pid = int(p.read_text(encoding="utf-8").strip())
        except Exception:
            old_pid = 0
        if old_pid > 0:
            # Check if process is still alive using OpenProcess + GetExitCodeProcess
            try:
                import ctypes
                PROCESS_QUERY_LIMITED = 0x1000
                ERROR_ACCESS_DENIED = 5
                ERROR_INVALID_PARAMETER = 87
                handle = ctypes.windll.kernel32.OpenProcess(PROCESS_QUERY_LIMITED, 0, old_pid)
                if handle:
                    exit_code = ctypes.c_ulong(0)
                    result = ctypes.windll.kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code))
                    ctypes.windll.kernel32.CloseHandle(handle)
                    if result and exit_code.value == 259:  # STILL_ACTIVE = 259
                        log.warning(f"bridge_mt5_pro lock held by PID {old_pid} — another instance is running. Exiting.")
                        return False
                else:
                    # OpenProcess returned NULL — check GetLastError to distinguish
                    # "process does not exist" (safe to reclaim) from
                    # "access denied" (process IS running, must NOT steal lock)
                    err = ctypes.windll.kernel32.GetLastError()
                    if err == ERROR_ACCESS_DENIED:
                        log.warning(f"bridge_mt5_pro lock held by PID {old_pid} — OpenProcess access denied, process may be running. Exiting.")
                        return False
                    elif err == ERROR_INVALID_PARAMETER:
                        # Process definitely does not exist — safe to reclaim below
                        pass
                    else:
                        # Unknown error: err={err}. Treat as potentially alive to be safe.
                        log.warning(f"bridge_mt5_pro lock held by PID {old_pid} — OpenProcess failed (GetLastError={err}). Exiting.")
                        return False
            except Exception:
                pass
        # Stale lock file (PID not running) — remove it
        try:
            p.unlink()
        except Exception:
            pass
    # Write our PID
    p.write_text(str(os.getpid()), encoding="utf-8")
    return True


def _release_lock(lock_path: str):
    try:
        Path(lock_path).unlink(missing_ok=True)
    except Exception:
        pass

try:
    import MetaTrader5 as mt5
except ImportError:
    print("ERROR: MetaTrader5 not installed")
    sys.exit(1)

CONFIG = {
    "mt5_login": 433684944,
    "mt5_server": "Exness-MT5Trial7",
    "symbol": "XAUUSDm",
    "timeframe": mt5.TIMEFRAME_M15,
    "timeframe_name": "M15",
    "confirm_timeframe": mt5.TIMEFRAME_H1,
    "confirm_timeframe_name": "H1",
    "scan_interval": 60,
    "risk_percent": 2.5,
    "min_confidence": 0.35,
    "max_spread_points": 450,
    "max_spread_price": 0.50,
    "ema_fast": 30,
    "ema_slow": 40,
    "rsi_period": 14,
    "atr_period": 14,
    "atr_sl_mult": 2.0,
    "atr_tp_mult": 2.8,
    "signal_dir": r"C:\Users\Administrator\AppData\Roaming\MetaQuotes\Terminal\Common\Files\atsawin",
    "signal_file": "latest_signal.json",
    "status_file": "ea_status.json",
    "log_file": r"C:\Users\Administrator\Desktop\bridge_mt5_pro.log",
    "trade_log_csv": r"C:\Users\Administrator\Desktop\bridge_mt5_backtest_trades.csv",
    "trade_summary_json": r"C:\Users\Administrator\Desktop\bridge_mt5_backtest_summary.json",
    "trade_analysis_json": r"C:\Users\Administrator\Desktop\bridge_mt5_trade_analysis.json",
    "trade_analysis_txt": r"C:\Users\Administrator\Desktop\bridge_mt5_trade_analysis.txt",
    "autotune_json": r"C:\Users\Administrator\Desktop\bridge_mt5_autotune_result.json",
    "autotune_txt": r"C:\Users\Administrator\Desktop\bridge_mt5_autotune_result.txt",
    "walkforward_json": r"C:\Users\Administrator\Desktop\bridge_mt5_walkforward_result.json",
    "walkforward_txt": r"C:\Users\Administrator\Desktop\bridge_mt5_walkforward_result.txt",
    "session_hours_utc": [0, 1, 5, 10, 13, 14],
    "session_filter_mode": "soft",
    "session_in_bonus": 0.12,
    "session_out_penalty": 0.15,
    "min_atr_price": 3.0,
    "min_ema_gap_price": 0.8,
    "session_opt_json": r"C:\\Users\\Administrator\\Desktop\\bridge_mt5_session_opt_result.json",
    "session_opt_txt": r"C:\\Users\\Administrator\\Desktop\\bridge_mt5_session_opt_result.txt",
    "live_execution_compare_json": r"C:\Users\Administrator\Desktop\bridge_mt5_live_execution_compare.json",
    "live_execution_compare_txt": r"C:\Users\Administrator\Desktop\bridge_mt5_live_execution_compare.txt",
    "bad_hour_filter_enabled": True,
    "bad_hour_min_trades": 20,
    "bad_hour_max_penalty": 0.35,
    "bad_hour_winrate_threshold": 45.0,
    "bad_hour_pnl_threshold": 0.0,
    "max_hold_bars": 48,
    "lock_file": r"C:\\Users\\Administrator\\AppData\\Roaming\\MetaQuotes\\Terminal\\Common\\Files\\atsawin\\bridge_mt5_pro.lock",
    "session_opt_min_hours": 5,
    "session_opt_min_pnl_r": -2.0,
    "session_opt_min_trades_per_hour": 10,
    "session_opt_min_total_trades": 50,
    "session_opt_cooldown_sec": 3600,
}

PDF_FIB_RATIOS = [0.242, 0.57, 1.617, 3.097, 5.165, 7.044, 8.237]

Path(CONFIG["signal_dir"]).mkdir(parents=True, exist_ok=True)
log = logging.getLogger("BridgeMT5Pro")
log.setLevel(logging.INFO)
fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
sh = logging.StreamHandler(sys.stdout)
sh.setFormatter(fmt)
fh = RotatingFileHandler(CONFIG["log_file"], maxBytes=5 * 1024 * 1024, backupCount=3)
fh.setFormatter(fmt)
log.handlers.clear()
log.addHandler(sh)
log.addHandler(fh)


@dataclass
class FVGZone:
    direction: str  # bullish | bearish
    low: float
    high: float
    mid: float
    index: int
    age_bars: int
    width: float
    filled: bool = False


@dataclass
class Signal:
    signal: str
    confidence: float
    entry_price: float
    stop_loss: float
    take_profit: float
    risk_reward_ratio: float
    atr: float
    rsi: float
    ema_fast: float
    ema_slow: float
    reasons: list
    metadata: dict = field(default_factory=dict)


def detect_fvg_zones(highs, lows, closes=None, lookback=80):
    """Detect simple 3-candle Fair Value Gaps.

    Bullish FVG: high[i-1] < low[i+1], zone = [high[i-1], low[i+1]].
    Bearish FVG: low[i-1] > high[i+1], zone = [high[i+1], low[i-1]].
    """
    n = min(len(highs), len(lows))
    if n < 3:
        return []
    start = max(1, n - int(lookback))
    zones = []
    for i in range(start, n - 1):
        prev_high = float(highs[i - 1])
        prev_low = float(lows[i - 1])
        next_high = float(highs[i + 1])
        next_low = float(lows[i + 1])
        age = (n - 1) - i

        if prev_high < next_low:
            low = prev_high
            high = next_low
            zones.append(FVGZone(
                direction="bullish",
                low=round(low, 5),
                high=round(high, 5),
                mid=round((low + high) / 2.0, 5),
                index=i,
                age_bars=age,
                width=round(high - low, 5),
                filled=False,
            ))

        if prev_low > next_high:
            low = next_high
            high = prev_low
            zones.append(FVGZone(
                direction="bearish",
                low=round(low, 5),
                high=round(high, 5),
                mid=round((low + high) / 2.0, 5),
                index=i,
                age_bars=age,
                width=round(high - low, 5),
                filled=False,
            ))
    return zones


def nearest_active_fvg(price, zones, direction=None, max_age_bars=80):
    candidates = []
    for z in zones:
        if z.filled:
            continue
        if direction and z.direction != direction:
            continue
        if z.age_bars > max_age_bars:
            continue
        candidates.append(z)
    if not candidates:
        return None, None
    price = float(price)
    best = min(candidates, key=lambda z: abs(price - z.mid))
    return best, round(abs(price - best.mid), 5)


def compute_fib_levels(swing_low, swing_high, ratios=None):
    ratios = ratios or PDF_FIB_RATIOS
    low = float(swing_low)
    high = float(swing_high)
    span = high - low
    return {float(r): round(low + span * float(r), 5) for r in ratios}


def nearest_fib_level(price, levels):
    if not levels:
        return {"ratio": 0.0, "level": 0.0, "distance": 0.0}
    price = float(price)
    ratio, level = min(levels.items(), key=lambda item: abs(price - float(item[1])))
    return {"ratio": float(ratio), "level": float(level), "distance": round(abs(price - float(level)), 5)}


def fib_payload_metadata(nearest=None):
    nearest = nearest or {"ratio": 0.0, "level": 0.0, "distance": 0.0}
    return {
        "fib_nearest_ratio": float(nearest.get("ratio") or 0.0),
        "fib_nearest_level": float(nearest.get("level") or 0.0),
        "fib_distance": float(nearest.get("distance") or 0.0),
    }


def fvg_payload_metadata(zone=None, distance=None):
    if zone is None:
        return {
            "strategy_version": "bridge_mt5_pro_v2.4_fvg_fib_rsi",
            "setup_type": "none",
            "fvg_direction": "none",
            "fvg_low": 0.0,
            "fvg_high": 0.0,
            "fvg_mid": 0.0,
            "fvg_age_bars": 0,
            "fvg_width": 0.0,
            "fvg_distance": 0.0,
            "fib_nearest_ratio": 0.0,
            "fib_nearest_level": 0.0,
            "fib_distance": 0.0,
            "rsi_divergence": "none",
            "score_breakdown": {},
        }
    return {
        "strategy_version": "bridge_mt5_pro_v2.4_fvg_fib_rsi",
        "setup_type": "fvg_fib_rsi",
        "fvg_direction": zone.direction,
        "fvg_low": zone.low,
        "fvg_high": zone.high,
        "fvg_mid": zone.mid,
        "fvg_age_bars": zone.age_bars,
        "fvg_width": zone.width,
        "fvg_distance": float(distance or 0.0),
        "fib_nearest_ratio": 0.0,
        "fib_nearest_level": 0.0,
        "fib_distance": 0.0,
        "rsi_divergence": "none",
        "score_breakdown": {},
    }


def ema(values, period):
    if len(values) < period:
        return []
    out = [sum(values[:period]) / period]
    k = 2.0 / (period + 1)
    for v in values[period:]:
        out.append((v - out[-1]) * k + out[-1])
    return out


def rsi(values, period=14):
    if len(values) < period + 1:
        return 50.0
    gains = []
    losses = []
    for i in range(1, len(values)):
        d = values[i] - values[i - 1]
        gains.append(max(0.0, d))
        losses.append(max(0.0, -d))
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))


def rolling_rsi_values(values, period=14):
    return [rsi(values[: i + 1], period) for i in range(len(values))]


def find_pivots(values, kind="low", left=2, right=2, lookback=80):
    vals = [float(v) for v in values]
    if len(vals) < left + right + 1:
        return []
    start = max(left, len(vals) - int(lookback))
    pivots = []
    for i in range(start, len(vals) - right):
        left_vals = vals[i - left : i]
        right_vals = vals[i + 1 : i + right + 1]
        if kind == "low":
            if all(vals[i] < x for x in left_vals) and all(vals[i] < x for x in right_vals):
                pivots.append(i)
        elif kind == "high":
            if all(vals[i] > x for x in left_vals) and all(vals[i] > x for x in right_vals):
                pivots.append(i)
        else:
            raise ValueError("kind must be 'low' or 'high'")
    return pivots


def detect_rsi_divergence(closes, rsi_values, left=1, right=1, lookback=80):
    if len(closes) != len(rsi_values) or len(closes) < left + right + 3:
        return "none"
    lows_idx = find_pivots(closes, kind="low", left=left, right=right, lookback=lookback)
    highs_idx = find_pivots(closes, kind="high", left=left, right=right, lookback=lookback)
    if len(lows_idx) >= 2:
        a, b = lows_idx[-2], lows_idx[-1]
        price_a, price_b = float(closes[a]), float(closes[b])
        rsi_a, rsi_b = float(rsi_values[a]), float(rsi_values[b])
        if price_b < price_a and rsi_b > rsi_a:
            return "regular_bullish"
        if price_b > price_a and rsi_b < rsi_a:
            return "hidden_bullish"
    if len(highs_idx) >= 2:
        a, b = highs_idx[-2], highs_idx[-1]
        price_a, price_b = float(closes[a]), float(closes[b])
        rsi_a, rsi_b = float(rsi_values[a]), float(rsi_values[b])
        if price_b > price_a and rsi_b < rsi_a:
            return "regular_bearish"
        if price_b < price_a and rsi_b > rsi_a:
            return "hidden_bearish"
    return "none"


def rsi_divergence_payload_metadata(divergence="none"):
    return {"rsi_divergence": str(divergence or "none")}


def atr(highs, lows, closes, period=14):
    if len(closes) < period + 1:
        return 0.0
    trs = []
    for i in range(1, len(closes)):
        tr = max(highs[i] - lows[i], abs(highs[i] - closes[i - 1]), abs(lows[i] - closes[i - 1]))
        trs.append(tr)
    return sum(trs[-period:]) / period


def calc_position_size(balance, risk_percent, entry, stop, symbol):
    if entry <= 0 or stop <= 0 or entry == stop:
        log.warning(f"calc_position_size: invalid entry/stop (entry={entry}, stop={stop}), returning 0.01")
        return 0.01
    info = mt5.symbol_info(symbol)
    if info is None:
        log.warning(f"calc_position_size: symbol_info(None) for {symbol}, returning 0.01")
        return 0.01
    tick_value = info.trade_tick_value or 0
    tick_size = info.trade_tick_size or 0
    min_lot = info.volume_min or 0.01
    max_lot = info.volume_max or 1.0
    step = info.volume_step or 0.01
    if tick_value <= 0 or tick_size <= 0:
        # Fallback for brokers/symbols that report 0 tick_value/tick_size (e.g. Exness XAUUSDm)
        # Use symbol point as tick_size and a reasonable tick_value estimate
        point = info.point or 0.01
        digits = info.digits or 2
        # For XAUUSDm-like symbols: 1 lot = 100 oz, 1 point move = $0.01 per oz ≈ $1 per lot
        # Conservative fallback: tick_value = point * 100, tick_size = point
        fallback_tick_size = point
        fallback_tick_value = point * 100.0
        log.warning(
            f"calc_position_size: tick_value={tick_value} tick_size={tick_size} for {symbol}, "
            f"using fallback tick_value={fallback_tick_value} tick_size={fallback_tick_size}"
        )
        tick_value = fallback_tick_value
        tick_size = fallback_tick_size
    risk_amount = balance * risk_percent / 100.0
    stop_dist = abs(entry - stop)
    loss_per_lot = (stop_dist / tick_size) * tick_value
    if loss_per_lot <= 0:
        log.warning(f"calc_position_size: loss_per_lot<=0, returning min_lot={min_lot}")
        return min_lot
    lots = risk_amount / loss_per_lot
    lots = max(min_lot, min(max_lot, lots))
    lots = math.floor(lots / step) * step
    result = round(max(min_lot, lots), 2)
    if result <= min_lot:
        log.warning(
            f"calc_position_size: result={result} at min_lot (balance={balance} risk={risk_percent}% "
            f"stop_dist={stop_dist:.2f} loss_per_lot={loss_per_lot:.2f})"
        )
    return result


def trend_bias_from_higher_tf(symbol):
    rates_h = mt5.copy_rates_from_pos(symbol, CONFIG["confirm_timeframe"], 0, 220)
    if rates_h is None or len(rates_h) < 80:
        return 0.0, "no_confirm_tf"
    closes_h = rates_h["close"].tolist()
    ef_h = ema(closes_h, CONFIG["ema_fast"])
    es_h = ema(closes_h, CONFIG["ema_slow"])
    if not ef_h or not es_h:
        return 0.0, "no_confirm_ema"
    if ef_h[-1] > es_h[-1]:
        return 0.25, "confirm_up"
    if ef_h[-1] < es_h[-1]:
        return -0.25, "confirm_down"
    return 0.0, "confirm_flat"


def generate_signal(rates, tick, current_hour_utc=None, apply_session_filter=False):
    closes = rates["close"].tolist()
    highs = rates["high"].tolist()
    lows = rates["low"].tolist()
    if len(closes) < 60:
        return Signal("hold", 0.0, 0, 0, 0, 0, 0, 0, 0, 0, ["insufficient_bars"])

    price = float(tick.ask)
    ef = ema(closes, CONFIG["ema_fast"])
    es = ema(closes, CONFIG["ema_slow"])
    rv = rsi(closes, CONFIG["rsi_period"])
    av = atr(highs, lows, closes, CONFIG["atr_period"])

    if not ef or not es or av <= 0:
        return Signal("hold", 0.0, price, 0, 0, 0, av, rv, ef[-1] if ef else 0, es[-1] if es else 0, ["indicator_fail"])

    trend_up = ef[-1] > es[-1]
    trend_down = ef[-1] < es[-1]

    buy_score = 0.0
    sell_score = 0.0
    out_penalty = 0.0
    bad_hour_penalty = 0.0
    reasons = []

    fvg_zones = detect_fvg_zones(highs, lows, closes, lookback=80)
    bullish_fvg, bullish_fvg_dist = nearest_active_fvg(price, fvg_zones, direction="bullish")
    bearish_fvg, bearish_fvg_dist = nearest_active_fvg(price, fvg_zones, direction="bearish")
    selected_fvg = None
    selected_fvg_dist = None

    if trend_up:
        buy_score += 1.2
        reasons.append("trend_up")
    elif trend_down:
        sell_score += 1.2
        reasons.append("trend_down")

    if 45 <= rv <= 65 and trend_up:
        buy_score += 0.8
        reasons.append("rsi_support_up")
    if 35 <= rv <= 55 and trend_down:
        sell_score += 0.8
        reasons.append("rsi_support_down")
    if rv >= 72:
        sell_score += 0.6
        reasons.append("rsi_overbought")
    if rv <= 28:
        buy_score += 0.6
        reasons.append("rsi_oversold")

    fvg_max_distance = max(av * 1.25, 0.5)
    if trend_up and bullish_fvg is not None and bullish_fvg_dist <= fvg_max_distance:
        selected_fvg = bullish_fvg
        selected_fvg_dist = bullish_fvg_dist
        buy_score += 0.7
        reasons.append("bullish_fvg_near_price")
    if trend_down and bearish_fvg is not None and bearish_fvg_dist <= fvg_max_distance:
        selected_fvg = bearish_fvg
        selected_fvg_dist = bearish_fvg_dist
        sell_score += 0.7
        reasons.append("bearish_fvg_near_price")
    if selected_fvg is None and fvg_zones:
        reasons.append("fvg_not_in_confluence")
    elif selected_fvg is None:
        reasons.append("no_fvg_zone")

    ema_price_gap = abs(price - ef[-1])
    ema_price_ratio = (ema_price_gap / av) if av > 0 else 0.0
    if ema_price_ratio > 0.15:
        if price > ef[-1]:
            buy_score += 0.5
        else:
            sell_score += 0.5

    vol_ok = av > 0.4
    if vol_ok:
        buy_score += 0.2 if trend_up else 0
        sell_score += 0.2 if trend_down else 0
    else:
        reasons.append("low_volatility")

    tf_bias, tf_reason = trend_bias_from_higher_tf(CONFIG["symbol"])
    reasons.append(tf_reason)
    if tf_bias > 0:
        buy_score += tf_bias
    elif tf_bias < 0:
        sell_score += abs(tf_bias)

    ema_gap = abs(ef[-1] - es[-1])
    chop_penalty = 0.0
    if av < CONFIG["min_atr_price"] or ema_gap < CONFIG["min_ema_gap_price"]:
        gap_ratio = (ema_gap / CONFIG["min_ema_gap_price"]) if CONFIG["min_ema_gap_price"] > 0 else 0.0
        atr_ratio = (av / CONFIG["min_atr_price"]) if CONFIG["min_atr_price"] > 0 else 0.0
        chop_penalty = max(0.0, 0.4 * (1.0 - gap_ratio) + 0.3 * (1.0 - atr_ratio))
        if chop_penalty > 0.0:
            reasons.append("chop_regime")
        buy_score = max(0.0, buy_score - chop_penalty)
        sell_score = max(0.0, sell_score - chop_penalty)

    if apply_session_filter and current_hour_utc is not None:
        allowed = set(CONFIG["session_hours_utc"])
        in_session = int(current_hour_utc) in allowed
        mode = str(CONFIG.get("session_filter_mode", "hard")).lower()
        out_penalty = 0.0
        if mode == "hard":
            if not in_session:
                reasons.append("out_of_session")
                return Signal("hold", 0.0, price, 0, 0, 0, av, rv, ef[-1], es[-1], reasons, fvg_payload_metadata())
            reasons.append("in_session")
        else:
            in_bonus = float(CONFIG.get("session_in_bonus", 0.0))
            out_penalty = float(CONFIG.get("session_out_penalty", 0.0))
            if in_session:
                reasons.append("in_session_soft")
                if buy_score >= sell_score:
                    buy_score += in_bonus
                else:
                    sell_score += in_bonus
            else:
                reasons.append("out_of_session_soft")
                if buy_score >= sell_score:
                    buy_score = max(0.0, buy_score - out_penalty)
                else:
                    sell_score = max(0.0, sell_score - out_penalty)

    if CONFIG.get("bad_hour_filter_enabled", True) and current_hour_utc is not None:
        buy_score, sell_score, bad_hour_penalty, bad_hour_reason = apply_session_hour_quality_penalty(
            buy_score, sell_score, current_hour_utc
        )
        if bad_hour_reason:
            reasons.append(bad_hour_reason)

    signal = "hold"
    strength = max(buy_score, sell_score)
    edge = abs(buy_score - sell_score)
    confidence = min(1.0, (strength / 3.1) * 0.7 + (edge / 2.0) * 0.3)
    metadata = fvg_payload_metadata(selected_fvg, selected_fvg_dist)
    swing_low = min(lows[-80:]) if len(lows) >= 1 else price
    swing_high = max(highs[-80:]) if len(highs) >= 1 else price
    nearest_fib = nearest_fib_level(price, compute_fib_levels(swing_low, swing_high))
    metadata.update(fib_payload_metadata(nearest_fib))
    rsi_div_closes = closes[-100:]
    rsi_div = detect_rsi_divergence(rsi_div_closes, rolling_rsi_values(rsi_div_closes, CONFIG["rsi_period"]), left=2, right=2, lookback=80)
    metadata.update(rsi_divergence_payload_metadata(rsi_div))
    rsi_div_bonus = 0.0
    if rsi_div in ("regular_bullish", "hidden_bullish"):
        rsi_div_bonus = 0.35
        buy_score += rsi_div_bonus
        reasons.append(f"rsi_divergence_{rsi_div}")
    elif rsi_div in ("regular_bearish", "hidden_bearish"):
        rsi_div_bonus = 0.35
        sell_score += rsi_div_bonus
        reasons.append(f"rsi_divergence_{rsi_div}")
    fib_bonus = 0.0
    if selected_fvg is not None and av > 0 and nearest_fib["distance"] <= max(av * 0.75, 0.5):
        fib_bonus = 0.25
        if selected_fvg.direction == "bullish":
            buy_score += fib_bonus
        elif selected_fvg.direction == "bearish":
            sell_score += fib_bonus
        reasons.append("fib_confluence")
    strength = max(buy_score, sell_score)
    edge = abs(buy_score - sell_score)
    confidence = min(1.0, (strength / 3.1) * 0.7 + (edge / 2.0) * 0.3)
    metadata["score_breakdown"] = {
        "buy_score": round(buy_score, 3),
        "sell_score": round(sell_score, 3),
        "edge": round(edge, 3),
        "fvg_bonus": 0.7 if selected_fvg is not None else 0.0,
        "fib_bonus": round(fib_bonus, 3),
        "rsi_divergence_bonus": round(rsi_div_bonus, 3),
        "chop_penalty": round(chop_penalty, 3),
        "session_out_penalty": round(out_penalty, 3),
        "bad_hour_penalty": round(bad_hour_penalty, 3),
    }

    sig_threshold = max(1.5, 1.9 - chop_penalty - out_penalty)
    if buy_score > sell_score and buy_score >= sig_threshold and edge >= 0.55:
        signal = "buy"
    elif sell_score > buy_score and sell_score >= sig_threshold and edge >= 0.55:
        signal = "sell"

    if signal == "hold":
        return Signal("hold", round(confidence, 3), price, 0, 0, 0, av, rv, ef[-1], es[-1], reasons + [f"buy={buy_score:.2f}", f"sell={sell_score:.2f}"], metadata)

    if signal == "buy":
        sl = price - av * CONFIG["atr_sl_mult"]
        tp = price + av * CONFIG["atr_tp_mult"]
    else:
        sl = price + av * CONFIG["atr_sl_mult"]
        tp = price - av * CONFIG["atr_tp_mult"]

    rr = abs(tp - price) / abs(price - sl) if abs(price - sl) > 0 else 0
    return Signal(signal, round(confidence, 3), round(price, 2), round(sl, 2), round(tp, 2), round(rr, 2), round(av, 2), round(rv, 1), round(ef[-1], 2), round(es[-1], 2), reasons, metadata)


def atomic_write(path, payload):
    """Atomic file write with Windows locking resilience.
    Uses tmp->rename pattern with retry + fallback to direct write
    when the target is locked by another process (e.g. MQL5 EA).
    Never raises — callers are not disrupted by file-lock contention.
    Returns True on success, False on failure."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".tmp")
    text = json.dumps(payload, ensure_ascii=True, separators=(",", ":"))
    # Keep the file ASCII-safe for MQL5 FILE_ANSI readers. Non-ASCII text is escaped.
    try:
        tmp.write_text(text, encoding="utf-8")
    except OSError:
        # Even the tmp write failed — log and bail without crashing caller
        log.warning(f"atomic_write tmp write failed for {path}")
        return False
    # Retry rename up to 5 times with exponential backoff (Windows file lock)
    for attempt in range(5):
        try:
            tmp.replace(p)
            return True  # success
        except OSError:
            if attempt < 4:
                time.sleep(0.05 * (2 ** attempt))  # 50ms, 100ms, 200ms, 400ms
    # Final fallback: direct overwrite (non-atomic but better than stale data)
    try:
        tmp.replace(p)
        return True
    except OSError:
        try:
            p.write_text(text, encoding="utf-8")
            return True
        except OSError:
            log.warning(f"atomic_write completely failed for {path} — signal file may be stale")
            pass  # best-effort; caller must not be disrupted
    # Clean up stale .tmp regardless of outcome
    try:
        tmp.unlink(missing_ok=True)
    except OSError:
        pass
    return False


def signal_fingerprint(payload):
    """Stable ID for EA de-duplication: same setup = same id, new price geometry/time = new id."""
    parts = [
        str(payload.get("mt5_symbol") or payload.get("symbol") or ""),
        str(payload.get("timeframe") or ""),
        str(payload.get("signal") or "hold"),
        f"{float(payload.get('entry_price') or 0):.2f}",
        f"{float(payload.get('stop_loss') or 0):.2f}",
        f"{float(payload.get('take_profit') or 0):.2f}",
        f"{float(payload.get('confidence') or 0):.3f}",
        str(payload.get("setup_type") or ""),
        str(payload.get("fvg_direction") or ""),
        f"{float(payload.get('fvg_mid') or 0):.2f}",
    ]
    return "|".join(parts)


def build_hold_payload(reason, sig, symbol, spread_points=0.0, spread_price=0.0):
    now = datetime.now(timezone.utc)
    metadata = dict(fvg_payload_metadata())
    metadata.update(dict(getattr(sig, "metadata", {}) or {}))
    payload = {
        "schema_version": "2.4",
        "contract": "atsawin_mt5_signal",
        "signal": "hold",
        "confidence": 0.0,
        "entry_price": float(getattr(sig, "entry_price", 0.0) or 0.0),
        "stop_loss": 0.0,
        "take_profit": 0.0,
        "risk_reward_ratio": 0.0,
        "position_size": 0.0,
        "atr": float(getattr(sig, "atr", 0.0) or 0.0),
        "rsi": float(getattr(sig, "rsi", 0.0) or 0.0),
        "ema_fast": float(getattr(sig, "ema_fast", 0.0) or 0.0),
        "ema_slow": float(getattr(sig, "ema_slow", 0.0) or 0.0),
        "reasons": [reason] + list(getattr(sig, "reasons", []) or []),
        "symbol": "XAUUSD",
        "mt5_symbol": symbol,
        "timeframe": CONFIG["timeframe_name"],
        "confirm_timeframe": CONFIG["confirm_timeframe_name"],
        "spread_points": round(float(spread_points or 0.0), 1),
        "spread_price": round(float(spread_price or 0.0), 3),
        "timestamp": now.isoformat(),
        "timestamp_epoch": int(now.timestamp()),
        "expires_at_epoch": int(now.timestamp()) + int(CONFIG["scan_interval"] * 2 + 30),
        "source": "bridge_mt5_pro_v2.4_fvg_fib_rsi",
    }
    payload.update(metadata)
    payload["setup_key"] = signal_fingerprint(payload)
    payload["signal_id"] = payload["setup_key"]
    return payload


def ensure_trade_log_header(path):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    if not p.exists() or p.stat().st_size == 0:
        p.write_text(
            "timestamp,bar_index,symbol,timeframe,side,entry,stop_loss,take_profit,rr,confidence,outcome,pnl_r,reason\n",
            encoding="utf-8",
        )


def append_trade_log(path, row):
    ensure_trade_log_header(path)
    line = (
        f"{row['timestamp']},{row['bar_index']},{row['symbol']},{row['timeframe']},{row['side']},"
        f"{row['entry']:.2f},{row['stop_loss']:.2f},{row['take_profit']:.2f},{row['rr']:.2f},"
        f"{row['confidence']:.3f},{row['outcome']},{row['pnl_r']:.2f},{row['reason']}\n"
    )
    with open(path, "a", encoding="utf-8") as f:
        f.write(line)


def build_bad_hour_penalty_map(trade_log_path=None, min_trades=None, max_penalty=None):
    """Build a soft penalty map for UTC hours that underperform in backtest."""
    path = Path(trade_log_path or CONFIG["trade_log_csv"])
    min_trades = int(min_trades if min_trades is not None else CONFIG.get("bad_hour_min_trades", 20))
    max_penalty = float(max_penalty if max_penalty is not None else CONFIG.get("bad_hour_max_penalty", 0.35))
    if not path.exists():
        return {}

    stats = {}
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            if r.get("outcome") not in ("win", "loss"):
                continue
            try:
                h = datetime.fromisoformat(r.get("timestamp", "")).hour
                pnl = float(r.get("pnl_r", 0.0))
            except Exception:
                continue
            s = stats.setdefault(h, {"trades": 0, "wins": 0, "losses": 0, "pnl_r": 0.0})
            s["trades"] += 1
            s["pnl_r"] += pnl
            if r.get("outcome") == "win":
                s["wins"] += 1
            else:
                s["losses"] += 1

    penalties = {}
    winrate_threshold = float(CONFIG.get("bad_hour_winrate_threshold", 45.0))
    pnl_threshold = float(CONFIG.get("bad_hour_pnl_threshold", 0.0))
    for h, s in stats.items():
        trades = s["trades"]
        if trades < min_trades:
            continue
        winrate = (s["wins"] / trades * 100.0) if trades else 0.0
        pnl_r = float(s["pnl_r"])
        # Penalize genuinely bad hours only: negative expectancy. A low winrate hour
        # can still be profitable with XAUUSD RR, so do not punish positive PnL.
        if pnl_r >= (pnl_threshold - 0.01):
            continue
        pnl_component = min(max_penalty, abs(min(0.0, pnl_r)) / max(float(trades), 1.0) * 0.6)
        winrate_component = ((winrate_threshold - winrate) / 100.0) * 0.8 if winrate < winrate_threshold else 0.0
        penalty = min(max_penalty, max(0.05, pnl_component + winrate_component))
        penalties[int(h)] = {
            "penalty": round(penalty, 3),
            "trades": trades,
            "wins": s["wins"],
            "losses": s["losses"],
            "winrate": round(winrate, 2),
            "pnl_r": round(pnl_r, 2),
        }
    return penalties


def apply_session_hour_quality_penalty(buy_score, sell_score, current_hour_utc, penalty_map=None):
    """Reduce the leading score in known bad hours; return updated scores + telemetry."""
    if current_hour_utc is None:
        return buy_score, sell_score, 0.0, ""
    penalties = penalty_map if penalty_map is not None else build_bad_hour_penalty_map()
    row = penalties.get(int(current_hour_utc)) if penalties else None
    if not row:
        return buy_score, sell_score, 0.0, ""
    penalty = float(row.get("penalty", 0.0) or 0.0)
    if buy_score >= sell_score:
        buy_score = max(0.0, buy_score - penalty)
    else:
        sell_score = max(0.0, sell_score - penalty)
    return round(buy_score, 3), round(sell_score, 3), round(penalty, 3), f"bad_hour_penalty_h{int(current_hour_utc)}"


def build_live_execution_comparison_report(backtest_summary, live_stats, runtime, configured_max_spread=None):
    bt_winrate = float(backtest_summary.get("winrate", 0.0) or 0.0)
    live_winrate = float(live_stats.get("winrate", 0.0) or 0.0)
    configured_max_spread = float(configured_max_spread if configured_max_spread is not None else CONFIG.get("max_spread_points", 450))
    spread = float(runtime.get("spread_points", 0.0) or 0.0)
    actual_rr = float(runtime.get("actual_rr", 0.0) or 0.0)
    magic_positions = int(runtime.get("magic_positions", 0) or 0)
    symbol_positions = int(runtime.get("symbol_positions", 0) or 0)
    reason = str(runtime.get("reason", "") or "")
    decision = str(runtime.get("decision", "") or "")
    diagnostics = {
        "spread_real": {"value_points": spread, "configured_max_points": configured_max_spread, "status": "bad" if spread > configured_max_spread else "ok"},
        "slippage": {"status": "unknown", "note": "Need EA execution log with requested entry vs actual fill for exact slippage."},
        "late_entry": {"status": "warning" if actual_rr and actual_rr < 1.0 else "ok", "note": "actual_rr below bridge RR suggests late entry/price drift."},
        "actual_rr": {"value": round(actual_rr, 3), "status": "bad" if actual_rr and actual_rr < 1.0 else "ok"},
        "max_position_stacking": {"magic_positions": magic_positions, "symbol_positions": symbol_positions, "decision": decision, "reason": reason, "status": "bad" if reason in ("hard_magic_cap", "symbol_position_cap") or magic_positions >= 3 else "ok"},
    }
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "backtest": backtest_summary,
        "live": live_stats,
        "runtime": runtime,
        "winrate_gap_pct": round(live_winrate - bt_winrate, 2),
        "diagnostics": diagnostics,
    }


def get_live_history_stats(days=30, magic=20260601):
    """Summarize closed XAUUSDm EA history from MT5 deals."""
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=int(days))
    deals = mt5.history_deals_get(start, end)
    if deals is None:
        return {"days": days, "magic": magic, "trades": 0, "wins": 0, "losses": 0, "winrate": 0.0, "net_profit": 0.0, "error": str(mt5.last_error())}
    rows = []
    for d in deals:
        if getattr(d, "symbol", "") != CONFIG["symbol"]:
            continue
        if int(getattr(d, "magic", 0) or 0) != int(magic):
            continue
        profit = float(getattr(d, "profit", 0.0) or 0.0) + float(getattr(d, "swap", 0.0) or 0.0) + float(getattr(d, "commission", 0.0) or 0.0)
        if abs(profit) < 1e-9:
            continue
        rows.append(profit)
    wins = sum(1 for p in rows if p > 0)
    losses = sum(1 for p in rows if p < 0)
    trades = wins + losses
    return {
        "days": days,
        "magic": magic,
        "trades": trades,
        "wins": wins,
        "losses": losses,
        "winrate": round((wins / trades * 100.0), 2) if trades else 0.0,
        "net_profit": round(sum(rows), 2),
    }


def read_json_file(path, default=None):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:
        return default if default is not None else {}


def run_live_execution_compare(days=30):
    backtest_summary = read_json_file(CONFIG["trade_summary_json"], default={})
    runtime_path = Path(CONFIG["signal_dir"]) / "ea_runtime_status.json"
    runtime = read_json_file(runtime_path, default={})
    live_stats = get_live_history_stats(days=days)
    report = build_live_execution_comparison_report(backtest_summary, live_stats, runtime, CONFIG["max_spread_points"])
    atomic_write(CONFIG["live_execution_compare_json"], report)

    diag = report["diagnostics"]
    lines = [
        "Atsawin Live vs Backtest Execution Compare",
        f"timestamp: {report['timestamp']}",
        f"backtest: trades={backtest_summary.get('trades', 0)} winrate={backtest_summary.get('winrate', 0)}% pnl_r={backtest_summary.get('pnl_r', 0)}",
        f"live({days}d, magic={live_stats.get('magic')}): trades={live_stats.get('trades')} wins={live_stats.get('wins')} losses={live_stats.get('losses')} winrate={live_stats.get('winrate')}% net={live_stats.get('net_profit')}",
        f"winrate_gap_pct: {report['winrate_gap_pct']}",
        "",
        "Diagnostics:",
        f"- spread_real: {diag['spread_real']['status']} value={diag['spread_real']['value_points']} max={diag['spread_real']['configured_max_points']}",
        f"- slippage: {diag['slippage']['status']} {diag['slippage']['note']}",
        f"- late_entry: {diag['late_entry']['status']} {diag['late_entry']['note']}",
        f"- actual_rr: {diag['actual_rr']['status']} value={diag['actual_rr']['value']}",
        f"- max_position_stacking: {diag['max_position_stacking']['status']} magic_positions={diag['max_position_stacking']['magic_positions']} symbol_positions={diag['max_position_stacking']['symbol_positions']} reason={diag['max_position_stacking']['reason']}",
    ]
    Path(CONFIG["live_execution_compare_txt"]).write_text("\n".join(lines) + "\n", encoding="utf-8")
    log.info(f"Live execution compare JSON: {CONFIG['live_execution_compare_json']}")
    log.info(f"Live execution compare TXT : {CONFIG['live_execution_compare_txt']}")
    return report


def validate_payload(payload):
    required = ["signal", "confidence", "stop_loss", "take_profit", "timestamp"]
    for k in required:
        if k not in payload:
            return False, f"missing_{k}"
    if payload["signal"] not in ("buy", "sell", "hold"):
        return False, "invalid_signal"
    if not (0.0 <= float(payload["confidence"]) <= 1.0):
        return False, "invalid_confidence"
    if payload["signal"] in ("buy", "sell"):
        if float(payload["stop_loss"]) <= 0 or float(payload["take_profit"]) <= 0:
            return False, "invalid_sl_tp"
        if float(payload.get("position_size", 0)) <= 0:
            return False, "invalid_position_size"
        entry = float(payload.get("entry_price", 0))
        sl = float(payload["stop_loss"])
        tp = float(payload["take_profit"])
        if payload["signal"] == "buy":
            if sl >= tp:
                return False, "invalid_buy_geometry"
            if entry > 0 and not (sl < entry < tp):
                return False, "invalid_buy_entry_position"
        if payload["signal"] == "sell":
            if sl <= tp:
                return False, "invalid_sell_geometry"
            if entry > 0 and not (tp < entry < sl):
                return False, "invalid_sell_entry_position"
    return True, "ok"


def scan_once():
    symbol = CONFIG["symbol"]
    # Retry up to 3 times for transient MT5 data failures before giving up.
    # This prevents a single momentary disconnect from returning None
    # and incrementing the error counter in the main loop.
    tick = None
    rates = None
    for _retry in range(3):
        tick = mt5.symbol_info_tick(symbol)
        rates = mt5.copy_rates_from_pos(symbol, CONFIG["timeframe"], 0, 300)
        if tick is not None and rates is not None and len(rates) >= 60:
            break
        log.warning(f"No market data (retry {_retry + 1}/3)")
        time.sleep(2 * (_retry + 1))
    if tick is None or rates is None or len(rates) < 60:
        log.warning("No market data after 3 retries")
        return None

    sym_info = mt5.symbol_info(symbol)
    if sym_info is None:
        log.warning("symbol_info returned None, skipping scan")
        return None
    point = sym_info.point or 0.01
    spread_points = (tick.ask - tick.bid) / point
    spread_price = tick.ask - tick.bid
    now_utc_hour = datetime.now(timezone.utc).hour
    sig = generate_signal(rates, tick, current_hour_utc=now_utc_hour, apply_session_filter=True)

    if spread_points > CONFIG["max_spread_points"] or spread_price > CONFIG["max_spread_price"]:
        sig = Signal("hold", 0.0, sig.entry_price, 0, 0, 0, sig.atr, sig.rsi, sig.ema_fast, sig.ema_slow, sig.reasons + ["spread_too_high"])

    if sig.signal != "hold" and sig.confidence < CONFIG["min_confidence"]:
        sig = Signal("hold", 0.0, sig.entry_price, 0, 0, 0, sig.atr, sig.rsi, sig.ema_fast, sig.ema_slow, sig.reasons + ["confidence_below_threshold"])

    account = mt5.account_info()
    balance = float(account.balance) if account else 10000.0
    pos_size = 0.0
    if sig.signal != "hold":
        pos_size = calc_position_size(balance, CONFIG["risk_percent"], sig.entry_price, sig.stop_loss, symbol)

    now = datetime.now(timezone.utc)
    metadata = dict(fvg_payload_metadata())
    metadata.update(dict(getattr(sig, "metadata", {}) or {}))
    payload = {
        "schema_version": "2.4",
        "contract": "atsawin_mt5_signal",
        "signal": sig.signal,
        "confidence": sig.confidence,
        "entry_price": sig.entry_price,
        "stop_loss": sig.stop_loss,
        "take_profit": sig.take_profit,
        "risk_reward_ratio": sig.risk_reward_ratio,
        "position_size": pos_size,
        "atr": sig.atr,
        "rsi": sig.rsi,
        "ema_fast": sig.ema_fast,
        "ema_slow": sig.ema_slow,
        "reasons": sig.reasons,
        "symbol": "XAUUSD",
        "mt5_symbol": symbol,
        "timeframe": CONFIG["timeframe_name"],
        "confirm_timeframe": CONFIG["confirm_timeframe_name"],
        "spread_points": round(spread_points, 1),
        "spread_price": round(spread_price, 3),
        "timestamp": now.isoformat(),
        "timestamp_epoch": int(now.timestamp()),
        "expires_at_epoch": int(now.timestamp()) + int(CONFIG["scan_interval"] * 2 + 30),
        "source": "bridge_mt5_pro_v2.4_fvg_fib_rsi",
    }
    payload.update(metadata)
    payload["setup_key"] = signal_fingerprint(payload)
    payload["signal_id"] = payload["setup_key"]

    ok, reason = validate_payload(payload)
    if not ok:
        log.error(f"payload_validation_failed: {reason}")
        payload = build_hold_payload(f"validation_failed:{reason}", sig, symbol, spread_points, spread_price)

    signal_path = os.path.join(CONFIG["signal_dir"], CONFIG["signal_file"])
    status_path = os.path.join(CONFIG["signal_dir"], CONFIG["status_file"])
    sig_ok = atomic_write(signal_path, payload)
    if not sig_ok:
        log.error(f"atomic_write FAILED for {signal_path} — latest_signal.json not updated this scan")
    status_ok = atomic_write(status_path, {
        "last_scan": payload["timestamp"],
        "source": payload.get("source"),
        "schema_version": payload.get("schema_version"),
        "contract": payload.get("contract"),
        "signal_id": payload.get("signal_id"),
        "setup_key": payload.get("setup_key"),
        "symbol": payload.get("symbol"),
        "mt5_symbol": payload.get("mt5_symbol"),
        "timeframe": payload.get("timeframe"),
        "confirm_timeframe": payload.get("confirm_timeframe"),
        "signal": payload["signal"],
        "confidence": payload["confidence"],
        "entry_price": payload.get("entry_price"),
        "stop_loss": payload.get("stop_loss"),
        "take_profit": payload.get("take_profit"),
        "spread_points": payload["spread_points"],
        "spread_price": payload.get("spread_price"),
        "risk_reward_ratio": payload.get("risk_reward_ratio"),
        "position_size": payload["position_size"],
        "atr": payload.get("atr"),
        "rsi": payload.get("rsi"),
        "ema_fast": payload.get("ema_fast"),
        "ema_slow": payload.get("ema_slow"),
        "timestamp": payload.get("timestamp"),
        "timestamp_epoch": payload.get("timestamp_epoch"),
        "expires_at_epoch": payload.get("expires_at_epoch"),
        "strategy_version": payload.get("strategy_version"),
        "setup_type": payload.get("setup_type"),
        "fvg_direction": payload.get("fvg_direction"),
        "fvg_low": payload.get("fvg_low"),
        "fvg_high": payload.get("fvg_high"),
        "fvg_mid": payload.get("fvg_mid"),
        "fvg_age_bars": payload.get("fvg_age_bars"),
        "fvg_width": payload.get("fvg_width"),
        "fvg_distance": payload.get("fvg_distance"),
        "fib_nearest_ratio": payload.get("fib_nearest_ratio"),
        "fib_nearest_level": payload.get("fib_nearest_level"),
        "fib_distance": payload.get("fib_distance"),
        "rsi_divergence": payload.get("rsi_divergence"),
        "score_breakdown": payload.get("score_breakdown"),
        "reasons": payload.get("reasons", []),
    })

    log.info(f"{symbol} {payload['signal'].upper()} conf={payload['confidence']:.2f} spread={payload['spread_points']:.1f} lot={payload['position_size']} rr={payload['risk_reward_ratio']} id={payload.get('signal_id','')[:32]}")
    return payload


def evaluate_trade(rates, entry_idx, sig, max_hold):
    """Hold trade up to max_hold future bars; return (outcome, reason, close_price).
    outcome is 'win' | 'loss' | 'expired'. Compensates for lookahead bias by
    checking SL/TP hit ordering using midpoint proximity for same-bar hits."""
    sl = sig.stop_loss
    tp = sig.take_profit
    hold_limit = min(entry_idx + 1 + max_hold, len(rates) - 1)
    for j in range(entry_idx + 1, hold_limit + 1):
        h = float(rates[j]["high"])
        l = float(rates[j]["low"])
        if sig.signal == "buy":
            hit_sl = l <= sl
            hit_tp = h >= tp
            if hit_sl and hit_tp:
                mid = (h + l) / 2.0
                if abs(mid - sl) <= abs(mid - tp):
                    return "loss", "sl_hit", sl
                else:
                    return "win", "tp_hit", tp
            elif hit_sl:
                return "loss", "sl_hit", sl
            elif hit_tp:
                return "win", "tp_hit", tp
        else:
            hit_sl = h >= sl
            hit_tp = l <= tp
            if hit_sl and hit_tp:
                mid = (h + l) / 2.0
                if abs(mid - sl) <= abs(mid - tp):
                    return "loss", "sl_hit", sl
                else:
                    return "win", "tp_hit", tp
            elif hit_sl:
                return "loss", "sl_hit", sl
            elif hit_tp:
                return "win", "tp_hit", tp
    close_price = float(rates[hold_limit]["close"])
    return "expired", "max_hold_reached", close_price


def run_backtest(bars=1500):
    symbol = CONFIG["symbol"]
    rates = mt5.copy_rates_from_pos(symbol, CONFIG["timeframe"], 0, bars)
    if rates is None or len(rates) < 300:
        log.error("Not enough bars for backtest")
        return

    trade_log_path = CONFIG["trade_log_csv"]
    summary_path = CONFIG["trade_summary_json"]
    Path(trade_log_path).write_text("", encoding="utf-8")
    ensure_trade_log_header(trade_log_path)

    wins = 0
    losses = 0
    holds = 0
    pnl_r = 0.0

    max_hold = CONFIG.get("max_hold_bars", 48)
    tail_room = max_hold + 2
    start_idx = max(60, min(250, len(rates) // 3))
    for i in range(start_idx, len(rates) - tail_room):
        window = rates[:i]
        close_now = float(rates[i]["close"])
        tick = type("Tick", (), {"ask": close_now, "bid": close_now})
        bar_hour = datetime.fromtimestamp(int(rates[i]["time"]), tz=timezone.utc).hour
        sig = generate_signal(window, tick, current_hour_utc=bar_hour, apply_session_filter=True)
        if sig.signal == "hold" or sig.confidence < CONFIG["min_confidence"]:
            holds += 1
            continue

        ts = datetime.fromtimestamp(int(rates[i]["time"]), tz=timezone.utc).isoformat()

        max_hold = CONFIG.get("max_hold_bars", 48)
        outcome, reason, close_price = evaluate_trade(rates, i, sig, max_hold)

        trade_pnl_r = 0.0
        if outcome == "win":
            wins += 1
            pnl_r += sig.risk_reward_ratio
            trade_pnl_r = sig.risk_reward_ratio
        elif outcome == "loss":
            losses += 1
            pnl_r -= 1.0
            trade_pnl_r = -1.0
        elif outcome == "expired":
            holds += 1
            if sig.entry_price != 0 and sig.stop_loss != 0:
                risk_dist = abs(sig.entry_price - sig.stop_loss)
                if risk_dist > 0:
                    if sig.signal == "buy":
                        trade_pnl_r = round((close_price - sig.entry_price) / risk_dist, 2)
                    else:
                        trade_pnl_r = round((sig.entry_price - close_price) / risk_dist, 2)
                    pnl_r += trade_pnl_r
        else:
            holds += 1

        append_trade_log(trade_log_path, {
            "timestamp": ts,
            "bar_index": i,
            "symbol": symbol,
            "timeframe": CONFIG["timeframe_name"],
            "side": sig.signal,
            "entry": sig.entry_price,
            "stop_loss": sig.stop_loss,
            "take_profit": sig.take_profit,
            "rr": sig.risk_reward_ratio,
            "confidence": sig.confidence,
            "outcome": outcome,
            "pnl_r": trade_pnl_r,
            "reason": reason,
        })

    trades = wins + losses
    winrate = (wins / trades * 100.0) if trades else 0.0
    summary = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "symbol": symbol,
        "timeframe": CONFIG["timeframe_name"],
        "bars": bars,
        "trades": trades,
        "wins": wins,
        "losses": losses,
        "skipped": holds,
        "winrate": round(winrate, 2),
        "pnl_r": round(pnl_r, 2),
        "trade_log_csv": trade_log_path,
    }
    atomic_write(summary_path, summary)
    log.info(f"Backtest trades={trades} wins={wins} losses={losses} winrate={winrate:.1f}% pnl_r={pnl_r:.2f} skipped={holds}")
    log.info(f"Backtest trade log: {trade_log_path}")
    log.info(f"Backtest summary : {summary_path}")


def analyze_trade_log():
    trade_log_path = CONFIG["trade_log_csv"]
    if not Path(trade_log_path).exists():
        log.warning(f"trade log not found: {trade_log_path}")
        return

    rows = []
    with open(trade_log_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)

    win_rows = [r for r in rows if r.get("outcome") == "win"]
    loss_rows = [r for r in rows if r.get("outcome") == "loss"]
    exec_rows = win_rows + loss_rows

    def safe_hour(ts):
        try:
            return datetime.fromisoformat(ts).hour
        except Exception:
            return None

    by_hour = {}
    for h in range(24):
        bucket = [r for r in exec_rows if safe_hour(r.get("timestamp", "")) == h]
        w = sum(1 for r in bucket if r.get("outcome") == "win")
        l = sum(1 for r in bucket if r.get("outcome") == "loss")
        t = w + l
        by_hour[str(h)] = {"trades": t, "wins": w, "losses": l, "winrate": round((w / t * 100.0), 2) if t else 0.0}

    by_side = {}
    for side in ("buy", "sell"):
        bucket = [r for r in exec_rows if r.get("side") == side]
        w = sum(1 for r in bucket if r.get("outcome") == "win")
        l = sum(1 for r in bucket if r.get("outcome") == "loss")
        t = w + l
        by_side[side] = {"trades": t, "wins": w, "losses": l, "winrate": round((w / t * 100.0), 2) if t else 0.0}

    buckets = {
        "0.35-0.50": lambda c: 0.35 <= c < 0.50,
        "0.50-0.70": lambda c: 0.50 <= c < 0.70,
        "0.70-1.00": lambda c: 0.70 <= c <= 1.00,
    }
    by_confidence = {}
    for name, fn in buckets.items():
        bucket = []
        for r in exec_rows:
            try:
                c = float(r.get("confidence", 0))
            except Exception:
                c = 0.0
            if fn(c):
                bucket.append(r)
        w = sum(1 for r in bucket if r.get("outcome") == "win")
        l = sum(1 for r in bucket if r.get("outcome") == "loss")
        t = w + l
        by_confidence[name] = {"trades": t, "wins": w, "losses": l, "winrate": round((w / t * 100.0), 2) if t else 0.0}

    loss_reasons = {}
    for r in loss_rows:
        reason = r.get("reason", "unknown")
        loss_reasons[reason] = loss_reasons.get(reason, 0) + 1

    analysis = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source_csv": trade_log_path,
        "total_rows": len(rows),
        "executed_trades": len(exec_rows),
        "wins": len(win_rows),
        "losses": len(loss_rows),
        "overall_winrate": round((len(win_rows) / len(exec_rows) * 100.0), 2) if exec_rows else 0.0,
        "by_hour": by_hour,
        "by_side": by_side,
        "by_confidence": by_confidence,
        "loss_reasons": loss_reasons,
    }

    atomic_write(CONFIG["trade_analysis_json"], analysis)

    lines = [
        "Atsawin Backtest Trade Analysis",
        f"timestamp: {analysis['timestamp']}",
        f"executed_trades: {analysis['executed_trades']} wins: {analysis['wins']} losses: {analysis['losses']} winrate: {analysis['overall_winrate']}%",
        "",
        "By side:",
    ]
    for k, v in by_side.items():
        lines.append(f"- {k}: trades={v['trades']} wins={v['wins']} losses={v['losses']} winrate={v['winrate']}%")

    lines.append("")
    lines.append("By confidence bucket:")
    for k, v in by_confidence.items():
        lines.append(f"- {k}: trades={v['trades']} wins={v['wins']} losses={v['losses']} winrate={v['winrate']}%")

    lines.append("")
    lines.append("Loss reasons:")
    if loss_reasons:
        for k, v in sorted(loss_reasons.items(), key=lambda x: x[1], reverse=True):
            lines.append(f"- {k}: {v}")
    else:
        lines.append("- none")

    lines.append("")
    lines.append("Top active hours (executed trades):")
    active_hours = sorted(by_hour.items(), key=lambda x: x[1]["trades"], reverse=True)[:5]
    for h, v in active_hours:
        lines.append(f"- hour {h}: trades={v['trades']} winrate={v['winrate']}%")

    Path(CONFIG["trade_analysis_txt"]).write_text("\n".join(lines) + "\n", encoding="utf-8")
    log.info(f"Trade analysis JSON: {CONFIG['trade_analysis_json']}")
    log.info(f"Trade analysis TXT : {CONFIG['trade_analysis_txt']}")


def backtest_metrics(rates):
    wins = 0
    losses = 0
    holds = 0
    pnl_r = 0.0

    start_idx = max(60, min(250, len(rates) // 3))
    max_hold = CONFIG.get("max_hold_bars", 48)
    tail_room = max_hold + 2
    for i in range(start_idx, len(rates) - tail_room):
        window = rates[:i]
        close_now = float(rates[i]["close"])
        tick = type("Tick", (), {"ask": close_now, "bid": close_now})
        bar_hour = datetime.fromtimestamp(int(rates[i]["time"]), tz=timezone.utc).hour
        sig = generate_signal(window, tick, current_hour_utc=bar_hour, apply_session_filter=True)
        if sig.signal == "hold" or sig.confidence < CONFIG["min_confidence"]:
            holds += 1
            continue

        max_hold = CONFIG.get("max_hold_bars", 48)
        outcome, reason, close_price = evaluate_trade(rates, i, sig, max_hold)

        if outcome == "win":
            wins += 1
            pnl_r += sig.risk_reward_ratio
        elif outcome == "loss":
            losses += 1
            pnl_r -= 1.0
        elif outcome == "expired":
            holds += 1
            if sig.entry_price != 0 and sig.stop_loss != 0:
                risk_dist = abs(sig.entry_price - sig.stop_loss)
                if risk_dist > 0:
                    if sig.signal == "buy":
                        pnl_r += (close_price - sig.entry_price) / risk_dist
                    else:
                        pnl_r += (sig.entry_price - close_price) / risk_dist
        else:
            holds += 1

    trades = wins + losses
    winrate = (wins / trades * 100.0) if trades else 0.0
    return {
        "trades": trades,
        "wins": wins,
        "losses": losses,
        "skipped": holds,
        "winrate": round(winrate, 2),
        "pnl_r": round(pnl_r, 2),
    }


def autotune_parameters(bars=1000):
    symbol = CONFIG["symbol"]
    rates = mt5.copy_rates_from_pos(symbol, CONFIG["timeframe"], 0, bars)
    if rates is None or len(rates) < 300:
        log.error("Not enough bars for autotune")
        return None

    base = {
        "ema_fast": CONFIG["ema_fast"],
        "ema_slow": CONFIG["ema_slow"],
        "atr_sl_mult": CONFIG["atr_sl_mult"],
        "atr_tp_mult": CONFIG["atr_tp_mult"],
        "min_confidence": CONFIG["min_confidence"],
    }

    grid = {
        "ema_fast": [12, 20, 30],
        "ema_slow": [40, 50],
        "atr_sl_mult": [1.6, 1.8, 2.0],
        "atr_tp_mult": [2.8, 3.0, 3.4],
        "min_confidence": [0.35, 0.45, 0.55],
    }

    results = []
    for ef in grid["ema_fast"]:
        for es in grid["ema_slow"]:
            if ef >= es:
                continue
            for slm in grid["atr_sl_mult"]:
                for tpm in grid["atr_tp_mult"]:
                    if tpm <= slm:
                        continue
                    for mc in grid["min_confidence"]:
                        CONFIG["ema_fast"] = ef
                        CONFIG["ema_slow"] = es
                        CONFIG["atr_sl_mult"] = slm
                        CONFIG["atr_tp_mult"] = tpm
                        CONFIG["min_confidence"] = mc
                        m = backtest_metrics(rates)
                        row = {
                            "ema_fast": ef,
                            "ema_slow": es,
                            "atr_sl_mult": slm,
                            "atr_tp_mult": tpm,
                            "min_confidence": mc,
                            **m,
                        }
                        results.append(row)

    if not results:
        log.error("autotune found no candidates")
        return None

    filtered = [r for r in results if r["trades"] >= 20]
    candidates = filtered if filtered else results
    best = sorted(candidates, key=lambda r: (r["pnl_r"], r["winrate"], r["trades"]), reverse=True)[0]

    CONFIG["ema_fast"] = best["ema_fast"]
    CONFIG["ema_slow"] = best["ema_slow"]
    CONFIG["atr_sl_mult"] = best["atr_sl_mult"]
    CONFIG["atr_tp_mult"] = best["atr_tp_mult"]
    CONFIG["min_confidence"] = best["min_confidence"]

    output = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "symbol": symbol,
        "timeframe": CONFIG["timeframe_name"],
        "bars": bars,
        "baseline": base,
        "best": best,
        "candidates_tested": len(results),
        "min_trades_filter": 20,
        "top5": sorted(candidates, key=lambda r: (r["pnl_r"], r["winrate"], r["trades"]), reverse=True)[:5],
    }

    atomic_write(CONFIG["autotune_json"], output)
    txt_lines = [
        "Atsawin Autotune Result",
        f"timestamp: {output['timestamp']}",
        f"tested: {output['candidates_tested']} candidates",
        f"best: ema_fast={best['ema_fast']} ema_slow={best['ema_slow']} atr_sl_mult={best['atr_sl_mult']} atr_tp_mult={best['atr_tp_mult']} min_conf={best['min_confidence']}",
        f"metrics: trades={best['trades']} wins={best['wins']} losses={best['losses']} winrate={best['winrate']}% pnl_r={best['pnl_r']}",
        "",
        "Top 5:",
    ]
    for i, r in enumerate(output["top5"], start=1):
        txt_lines.append(
            f"{i}) ef={r['ema_fast']} es={r['ema_slow']} slm={r['atr_sl_mult']} tpm={r['atr_tp_mult']} mc={r['min_confidence']} -> pnl_r={r['pnl_r']} winrate={r['winrate']} trades={r['trades']}"
        )
    Path(CONFIG["autotune_txt"]).write_text("\n".join(txt_lines) + "\n", encoding="utf-8")

    log.info(f"Autotune best -> pnl_r={best['pnl_r']} winrate={best['winrate']} trades={best['trades']}")
    log.info(f"Autotune JSON: {CONFIG['autotune_json']}")
    log.info(f"Autotune TXT : {CONFIG['autotune_txt']}")
    return output


def optimize_session_hours_from_trade_log(min_trades_per_hour=10, max_hours=12, min_hours=4, min_total_trades=50):
    # Cooldown guard: prevent runaway re-execution (e.g. cron calling every 2 min).
    # Reads the last-run timestamp from the result JSON and skips if too recent.
    cooldown_sec = int(CONFIG.get("session_opt_cooldown_sec", 3600))
    _sess_json = CONFIG["session_opt_json"]
    if cooldown_sec > 0 and Path(_sess_json).exists():
        try:
            _prev = json.loads(Path(_sess_json).read_text(encoding="utf-8"))
            _prev_ts = datetime.fromisoformat(_prev["timestamp"])
            _elapsed = (datetime.now(timezone.utc) - _prev_ts.replace(tzinfo=timezone.utc)).total_seconds()
            if _elapsed < cooldown_sec:
                log.info(f"Session opt COOLDOWN -> {_elapsed:.0f}s elapsed, {cooldown_sec}s required. Skipping.")
                return None
        except Exception:
            pass  # If we can't read the file, proceed normally

    path = CONFIG["trade_log_csv"]
    if not Path(path).exists():
        log.warning(f"session optimize: trade log not found {path} — skipping optimization")
        result = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "old_hours": list(CONFIG["session_hours_utc"]),
            "new_hours": list(CONFIG["session_hours_utc"]),
            "min_trades_per_hour": min_trades_per_hour,
            "max_hours": max_hours,
            "min_hours": min_hours,
            "evaluated_hours": [],
            "selection_mode": "skipped_no_trade_log",
            "rejection_reason": f"trade_log_not_found_{path}",
        }
        atomic_write(CONFIG["session_opt_json"], result)
        log.info(f"Session opt SKIPPED -> keeping {CONFIG['session_hours_utc']} (no trade log)")
        log.info(f"Session opt JSON: {CONFIG['session_opt_json']}")
        return result

    rows = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            if r.get("outcome") not in ("win", "loss"):
                continue
            rows.append(r)

    if not rows:
        log.error("session optimize failed: no executed trades in log")
        return None

    # Statistical significance guard: require minimum total trades across all hours
    if len(rows) < min_total_trades:
        log.warning(f"session optimize: only {len(rows)} total trades in log, "
                     f"below minimum {min_total_trades}. Keeping old hours {CONFIG['session_hours_utc']}.")
        result = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "old_hours": list(CONFIG["session_hours_utc"]),
            "new_hours": list(CONFIG["session_hours_utc"]),
            "min_trades_per_hour": min_trades_per_hour,
            "max_hours": max_hours,
            "min_hours": min_hours,
            "evaluated_hours": [],
            "selection_mode": "rejected_insufficient_total_trades",
            "rejection_reason": f"total_trades={len(rows)}_below_{min_total_trades}",
        }
        atomic_write(CONFIG["session_opt_json"], result)
        log.info(f"Session opt REJECTED -> keeping {CONFIG['session_hours_utc']} (insufficient total trades)")
        log.info(f"Session opt JSON: {CONFIG['session_opt_json']}")
        return result

    stats = {}
    for r in rows:
        try:
            h = datetime.fromisoformat(r["timestamp"]).hour
            pnl = float(r.get("pnl_r", 0.0))
        except Exception:
            continue
        if h not in stats:
            stats[h] = {"trades": 0, "wins": 0, "losses": 0, "pnl_r": 0.0}
        stats[h]["trades"] += 1
        stats[h]["pnl_r"] += pnl
        if r.get("outcome") == "win":
            stats[h]["wins"] += 1
        else:
            stats[h]["losses"] += 1

    ranked = []
    for h, s in stats.items():
        trades = s["trades"]
        winrate = (s["wins"] / trades * 100.0) if trades else 0.0
        score = (s["pnl_r"] * 10.0) + (winrate / 100.0) + min(trades, 8) * 0.05
        ranked.append({
            "hour": h,
            "trades": trades,
            "wins": s["wins"],
            "losses": s["losses"],
            "winrate": round(winrate, 2),
            "pnl_r": round(s["pnl_r"], 2),
            "score": round(score, 4),
        })

    ranked.sort(key=lambda x: x["score"], reverse=True)
    strict = [r for r in ranked if r["trades"] >= min_trades_per_hour and (r["pnl_r"] > 0 or r["winrate"] >= 45.0)]

    if len(strict) >= min_hours:
        selected = strict[:max_hours]
        selection_mode = "strict"
    elif strict:
        # strict produced some results but fewer than min_hours: pad with top-scored hours
        strict_set = {r["hour"] for r in strict}
        fallback = [r for r in ranked if r["hour"] not in strict_set]
        selected = strict + fallback[:max(0, min_hours - len(strict))]
        selected = selected[:max_hours]
        selection_mode = "strict_padded"
    else:
        # strict produced nothing: use top-scored hours by rank
        selected = ranked[:max(min_hours, 1)]
        selected = selected[:max_hours]
        selection_mode = "fallback_top_score"

    selected_hours = sorted(int(r["hour"]) for r in selected)

    if not selected_hours:
        log.error("session optimize failed: empty selected hours")
        return None

    # Safety floor: never shrink session window below configured minimum hours
    min_allowed_hours = int(CONFIG.get("session_opt_min_hours", 5))
    if len(selected_hours) < min_allowed_hours:
        log.warning(f"session optimize produced only {len(selected_hours)} hours ({selected_hours}), "
                     f"below floor of {min_allowed_hours}. Keeping old hours {CONFIG['session_hours_utc']}.")
        result = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "old_hours": list(CONFIG["session_hours_utc"]),
            "new_hours": list(CONFIG["session_hours_utc"]),
            "min_trades_per_hour": min_trades_per_hour,
            "max_hours": max_hours,
            "min_hours": min_hours,
            "evaluated_hours": ranked,
            "selection_mode": f"{selection_mode}_rejected_below_floor",
            "rejection_reason": f"only_{len(selected_hours)}h_selected_need_{min_allowed_hours}h",
        }
        atomic_write(CONFIG["session_opt_json"], result)
        log.info(f"Session opt REJECTED -> keeping {CONFIG['session_hours_utc']} (too few hours)")
        log.info(f"Session opt JSON: {CONFIG['session_opt_json']}")
        return result

    # Safety check: only commit if new session window has positive or acceptable total PnL
    total_pnl_r = round(sum(float(r.get("pnl_r", 0)) for r in selected), 2)
    min_pnl_r = float(CONFIG.get("session_opt_min_pnl_r", -2.0))
    if total_pnl_r < min_pnl_r:
        log.warning(f"session optimize total PnL ({total_pnl_r}) below threshold ({min_pnl_r}). "
                     f"Keeping old hours {CONFIG['session_hours_utc']}.")
        result = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "old_hours": list(CONFIG["session_hours_utc"]),
            "new_hours": list(CONFIG["session_hours_utc"]),
            "min_trades_per_hour": min_trades_per_hour,
            "max_hours": max_hours,
            "min_hours": min_hours,
            "evaluated_hours": ranked,
            "selection_mode": f"{selection_mode}_rejected_low_pnl",
            "rejection_reason": f"total_pnl_r={total_pnl_r}_below_{min_pnl_r}",
        }
        atomic_write(CONFIG["session_opt_json"], result)
        log.info(f"Session opt REJECTED -> keeping {CONFIG['session_hours_utc']} (PnL too low)")
        log.info(f"Session opt JSON: {CONFIG['session_opt_json']}")
        return result

    old_hours = list(CONFIG["session_hours_utc"])
    CONFIG["session_hours_utc"] = selected_hours

    result = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "old_hours": old_hours,
        "new_hours": selected_hours,
        "min_trades_per_hour": min_trades_per_hour,
        "max_hours": max_hours,
        "min_hours": min_hours,
        "evaluated_hours": ranked,
        "selection_mode": selection_mode,
    }
    atomic_write(CONFIG["session_opt_json"], result)

    lines = [
        "Atsawin Session Optimization",
        f"timestamp: {result['timestamp']}",
        f"old_hours: {old_hours}",
        f"new_hours: {selected_hours}",
        f"selection_mode: {result['selection_mode']}",
        "",
        "Ranked hours:",
    ]
    for r in ranked:
        lines.append(
            f"- h{r['hour']:02d}: trades={r['trades']} wins={r['wins']} losses={r['losses']} winrate={r['winrate']}% pnl_r={r['pnl_r']} score={r['score']}"
        )
    Path(CONFIG["session_opt_txt"]).write_text("\n".join(lines) + "\n", encoding="utf-8")
    log.info(f"Session optimized -> {selected_hours}")
    log.info(f"Session opt JSON: {CONFIG['session_opt_json']}")
    log.info(f"Session opt TXT : {CONFIG['session_opt_txt']}")
    return result


def find_best_params_on_rates(rates):
    grid = {
        "ema_fast": [12, 20, 30],
        "ema_slow": [40, 50],
        "atr_sl_mult": [1.6, 1.8, 2.0],
        "atr_tp_mult": [2.8, 3.0, 3.4],
        "min_confidence": [0.35, 0.45, 0.55],
    }
    results = []
    for ef in grid["ema_fast"]:
        for es in grid["ema_slow"]:
            if ef >= es:
                continue
            for slm in grid["atr_sl_mult"]:
                for tpm in grid["atr_tp_mult"]:
                    if tpm <= slm:
                        continue
                    for mc in grid["min_confidence"]:
                        CONFIG["ema_fast"] = ef
                        CONFIG["ema_slow"] = es
                        CONFIG["atr_sl_mult"] = slm
                        CONFIG["atr_tp_mult"] = tpm
                        CONFIG["min_confidence"] = mc
                        m = backtest_metrics(rates)
                        results.append({"ema_fast": ef, "ema_slow": es, "atr_sl_mult": slm, "atr_tp_mult": tpm, "min_confidence": mc, **m})
    if not results:
        return None
    candidates = [r for r in results if r["trades"] >= 12] or results
    return sorted(candidates, key=lambda r: (r["pnl_r"], r["winrate"], r["trades"]), reverse=True)[0]


def run_walkforward(total_bars=1300, train_bars=550, test_bars=300, step=300):
    symbol = CONFIG["symbol"]
    rates = mt5.copy_rates_from_pos(symbol, CONFIG["timeframe"], 0, total_bars)
    if rates is None or len(rates) < (train_bars + test_bars + 50):
        log.error("Not enough bars for walk-forward")
        return None

    baseline = {
        "ema_fast": CONFIG["ema_fast"],
        "ema_slow": CONFIG["ema_slow"],
        "atr_sl_mult": CONFIG["atr_sl_mult"],
        "atr_tp_mult": CONFIG["atr_tp_mult"],
        "min_confidence": CONFIG["min_confidence"],
    }

    segments = []
    start = 0
    while start + train_bars + test_bars <= len(rates):
        train = rates[start:start + train_bars]
        test = rates[start + train_bars:start + train_bars + test_bars]
        best = find_best_params_on_rates(train)
        if best is None:
            break
        CONFIG["ema_fast"] = best["ema_fast"]
        CONFIG["ema_slow"] = best["ema_slow"]
        CONFIG["atr_sl_mult"] = best["atr_sl_mult"]
        CONFIG["atr_tp_mult"] = best["atr_tp_mult"]
        CONFIG["min_confidence"] = best["min_confidence"]
        test_metrics = backtest_metrics(test)
        segments.append({
            "start": start,
            "train_bars": train_bars,
            "test_bars": test_bars,
            "best": best,
            "test": test_metrics,
        })
        start += step

    if not segments:
        log.error("walk-forward produced no segments")
        return None

    total_trades = sum(s["test"]["trades"] for s in segments)
    total_wins = sum(s["test"]["wins"] for s in segments)
    total_losses = sum(s["test"]["losses"] for s in segments)
    total_pnl_r = round(sum(s["test"]["pnl_r"] for s in segments), 2)
    wf_winrate = round((total_wins / total_trades * 100.0), 2) if total_trades else 0.0

    result = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "symbol": symbol,
        "timeframe": CONFIG["timeframe_name"],
        "total_bars": int(len(rates)),
        "segments": segments,
        "summary": {
            "segments": len(segments),
            "trades": total_trades,
            "wins": total_wins,
            "losses": total_losses,
            "winrate": wf_winrate,
            "pnl_r": total_pnl_r,
        },
        "baseline": baseline,
    }

    atomic_write(CONFIG["walkforward_json"], result)
    lines = [
        "Atsawin Walk-Forward Result",
        f"timestamp: {result['timestamp']}",
        f"segments={len(segments)} trades={total_trades} wins={total_wins} losses={total_losses} winrate={wf_winrate}% pnl_r={total_pnl_r}",
        "",
    ]
    for idx, seg in enumerate(segments, start=1):
        b = seg["best"]
        t = seg["test"]
        lines.append(
            f"seg{idx}: best(ef={b['ema_fast']} es={b['ema_slow']} slm={b['atr_sl_mult']} tpm={b['atr_tp_mult']} mc={b['min_confidence']}) -> test(trades={t['trades']} winrate={t['winrate']} pnl_r={t['pnl_r']})"
        )
    Path(CONFIG["walkforward_txt"]).write_text("\n".join(lines) + "\n", encoding="utf-8")
    log.info(f"Walk-forward summary -> trades={total_trades} winrate={wf_winrate}% pnl_r={total_pnl_r}")
    log.info(f"Walk-forward JSON: {CONFIG['walkforward_json']}")
    log.info(f"Walk-forward TXT : {CONFIG['walkforward_txt']}")
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--health", action="store_true")
    ap.add_argument("--backtest", action="store_true")
    ap.add_argument("--analyze", action="store_true")
    ap.add_argument("--autotune", action="store_true")
    ap.add_argument("--walkforward", action="store_true")
    ap.add_argument("--optimize-session", action="store_true")
    ap.add_argument("--compare-live-execution", action="store_true")
    ap.add_argument("--compare-days", type=int, default=30)
    args = ap.parse_args()

    # Acquire lock for any mode that writes shared files (trade log, session opt, autotune, etc.)
    # to prevent parallel cron invocations from corrupting each other's output.
    _lock_path = CONFIG.get("lock_file", "")
    _lock_acquired = False
    if not any([args.health, args.analyze]):
        if _lock_path:
            if not _acquire_lock(_lock_path, log):
                sys.exit(0)
            _lock_acquired = True

    if not mt5.initialize(login=CONFIG["mt5_login"], server=CONFIG["mt5_server"]):
        log.error(f"MT5 init failed: {mt5.last_error()}")
        if _lock_acquired:
            _release_lock(_lock_path)
        sys.exit(1)

    if args.health:
        acc = mt5.account_info()
        tick = mt5.symbol_info_tick(CONFIG["symbol"])
        log.info(f"account_ok={acc is not None} symbol_tick_ok={tick is not None}")
        mt5.shutdown()
        return

    if args.optimize_session:
        _sess_min_trades = int(CONFIG.get("session_opt_min_trades_per_hour", 10))
        _sess_min_total = int(CONFIG.get("session_opt_min_total_trades", 50))
        run_backtest()
        analyze_trade_log()
        optimize_session_hours_from_trade_log(
            min_trades_per_hour=_sess_min_trades,
            min_total_trades=_sess_min_total,
        )
        run_backtest()
        analyze_trade_log()
        mt5.shutdown()
        return

    if args.compare_live_execution:
        run_live_execution_compare(days=args.compare_days)
        mt5.shutdown()
        return

    if args.walkforward:
        run_walkforward()
        mt5.shutdown()
        if _lock_acquired:
            _release_lock(_lock_path)
        return

    if args.autotune:
        tuned = autotune_parameters()
        if tuned is not None:
            run_backtest()
            analyze_trade_log()
        mt5.shutdown()
        if _lock_acquired:
            _release_lock(_lock_path)
        return

    if args.backtest:
        run_backtest()
        if args.analyze:
            analyze_trade_log()
        mt5.shutdown()
        if _lock_acquired:
            _release_lock(_lock_path)
        return

    if args.analyze:
        analyze_trade_log()
        mt5.shutdown()
        if _lock_acquired:
            _release_lock(_lock_path)
        return

    # Safety: clamp session hours to a minimum window so a previous aggressive
    # --optimize-session run cannot starve the live bridge of tradable hours.
    _session_floor = int(CONFIG.get("session_opt_min_hours", 5))
    if len(CONFIG.get("session_hours_utc", [])) < _session_floor:
        log.warning(f"session_hours_utc has only {len(CONFIG['session_hours_utc'])} hours "
                     f"({CONFIG['session_hours_utc']}), below floor {_session_floor}. "
                     f"Resetting to default [0,1,5,10,13,14].")
        CONFIG["session_hours_utc"] = [0, 1, 5, 10, 13, 14]

    def _reconnect_mt5():
        """Attempt to re-initialize MT5 connection. Returns True on success."""
        log.warning("Attempting MT5 reconnection...")
        try:
            mt5.shutdown()
        except Exception:
            pass
        for attempt in range(3):
            try:
                if mt5.initialize(login=CONFIG["mt5_login"], server=CONFIG["mt5_server"]):
                    log.info(f"MT5 reconnection successful (attempt {attempt + 1})")
                    return True
                else:
                    err = mt5.last_error()
                    log.warning(f"MT5 reconnection attempt {attempt + 1}/3 failed: {err}")
            except Exception as exc:
                log.warning(f"MT5 reconnection attempt {attempt + 1}/3 exception: {exc}")
            time.sleep(5 * (attempt + 1))
        log.error("MT5 reconnection failed after 3 attempts")
        return False

    try:
        scan_once()
        if not args.once:
            max_consecutive_errors = 10
            error_count = 0
            while True:
                time.sleep(CONFIG["scan_interval"])
                try:
                    result = scan_once()
                    if result is None:
                        # No market data — count as a consecutive failure
                        error_count += 1
                        log.warning(f"scan_once returned None (no market data) ({error_count}/{max_consecutive_errors})")
                        if error_count >= max_consecutive_errors:
                            log.error("Too many consecutive no-market-data cycles, attempting MT5 reconnection")
                            if _reconnect_mt5():
                                error_count = 0
                                continue
                            else:
                                log.error("MT5 reconnection failed, shutting down bridge")
                                break
                        time.sleep(min(30, CONFIG["scan_interval"]))
                        continue
                    error_count = 0
                except Exception as exc:
                    error_count += 1
                    log.error(f"scan_once error ({error_count}/{max_consecutive_errors}): {exc}")
                    if error_count >= max_consecutive_errors:
                        log.error("Too many consecutive errors, attempting MT5 reconnection")
                        if _reconnect_mt5():
                            error_count = 0
                            continue
                        else:
                            log.error("MT5 reconnection failed, shutting down bridge")
                            break
                    time.sleep(min(30, CONFIG["scan_interval"]))
    finally:
        if _lock_acquired:
            _release_lock(_lock_path)

    mt5.shutdown()


if __name__ == "__main__":
    main()
