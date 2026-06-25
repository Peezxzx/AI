"""
Technical Analysis Engine - Calculates indicators and generates signals
"""
import math
from datetime import datetime
from .models import (
    Candle, IndicatorResult, IndicatorValue, MACDValue,
    BollingerValue, TradingSignal, Signal,
)
from .market_data import get_klines


def calculate_sma(prices: list[float], period: int) -> list[float]:
    """Calculate Simple Moving Average."""
    if len(prices) < period:
        return []
    result = []
    for i in range(period - 1, len(prices)):
        avg = sum(prices[i - period + 1:i + 1]) / period
        result.append(avg)
    return result


def calculate_ema(prices: list[float], period: int) -> list[float]:
    """Calculate Exponential Moving Average."""
    if len(prices) < period:
        return []
    multiplier = 2.0 / (period + 1)
    ema = [sum(prices[:period]) / period]
    for price in prices[period:]:
        ema.append((price - ema[-1]) * multiplier + ema[-1])
    return ema


def calculate_rsi(prices: list[float], period: int = 14) -> list[float]:
    """Calculate Relative Strength Index."""
    if len(prices) < period + 1:
        return []

    gains = []
    losses = []
    for i in range(1, len(prices)):
        change = prices[i] - prices[i - 1]
        gains.append(max(0, change))
        losses.append(max(0, -change))

    if len(gains) < period:
        return []

    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    rsi_values = []
    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        if avg_loss == 0:
            rsi_values.append(100.0)
        else:
            rs = avg_gain / avg_loss
            rsi_values.append(100.0 - (100.0 / (1.0 + rs)))

    return rsi_values


def calculate_macd(
    prices: list[float],
    fast: int = 12,
    slow: int = 26,
    signal_period: int = 9,
) -> tuple[list[float], list[float], list[float]]:
    """Calculate MACD, Signal line, and Histogram."""
    if len(prices) < slow:
        return [], [], []

    ema_fast = calculate_ema(prices, fast)
    ema_slow = calculate_ema(prices, slow)

    # Align the EMAs
    offset = slow - fast
    macd_line = []
    for i in range(len(ema_slow)):
        macd_line.append(ema_fast[i + offset] - ema_slow[i])

    if len(macd_line) < signal_period:
        return macd_line, [], []

    signal_line = calculate_ema(macd_line, signal_period)
    signal_offset = len(macd_line) - len(signal_line)

    histogram = []
    for i in range(len(signal_line)):
        histogram.append(macd_line[i + signal_offset] - signal_line[i])

    return macd_line, signal_line, histogram


def calculate_bollinger(
    prices: list[float],
    period: int = 20,
    std_dev: float = 2.0,
) -> tuple[list[float], list[float], list[float]]:
    """Calculate Bollinger Bands (upper, middle, lower)."""
    if len(prices) < period:
        return [], [], []

    upper = []
    middle = []
    lower = []

    for i in range(period - 1, len(prices)):
        window = prices[i - period + 1:i + 1]
        avg = sum(window) / period
        variance = sum((p - avg) ** 2 for p in window) / period
        std = math.sqrt(variance)
        middle.append(avg)
        upper.append(avg + std_dev * std)
        lower.append(avg - std_dev * std)

    return upper, middle, lower


def calculate_atr(candles: list[Candle], period: int = 14) -> list[float]:
    """Calculate Average True Range."""
    if len(candles) < period + 1:
        return []

    true_ranges = []
    for i in range(1, len(candles)):
        tr = max(
            candles[i].high - candles[i].low,
            abs(candles[i].high - candles[i - 1].close),
            abs(candles[i].low - candles[i - 1].close),
        )
        true_ranges.append(tr)

    if len(true_ranges) < period:
        return []

    atr = [sum(true_ranges[:period]) / period]
    for i in range(period, len(true_ranges)):
        atr.append((atr[-1] * (period - 1) + true_ranges[i]) / period)

    return atr


def calculate_stochastic(
    candles: list[Candle],
    period: int = 14,
    smooth: int = 3,
) -> list[float]:
    """Calculate Stochastic Oscillator (%K)."""
    if len(candles) < period:
        return []

    k_values = []
    for i in range(period - 1, len(candles)):
        window = candles[i - period + 1:i + 1]
        high = max(c.high for c in window)
        low = min(c.low for c in window)
        if high == low:
            k_values.append(50.0)
        else:
            k_values.append((candles[i].close - low) / (high - low) * 100)

    if len(k_values) < smooth:
        return k_values

    # Smooth with SMA
    smoothed = []
    for i in range(smooth - 1, len(k_values)):
        smoothed.append(sum(k_values[i - smooth + 1:i + 1]) / smooth)

    return smoothed


async def get_indicators(
    symbol: str,
    timeframe: str = "1h",
    indicators: list[str] | None = None,
    period: int = 14,
    limit: int = 200,
) -> IndicatorResult:
    """Calculate technical indicators for a symbol."""
    if indicators is None:
        indicators = ["sma", "ema", "rsi", "macd", "bollinger", "atr"]

    candles = await get_klines(symbol, timeframe, limit)
    if not candles:
        return IndicatorResult(symbol=symbol, timeframe=timeframe)

    closes = [c.close for c in candles]
    result = IndicatorResult(symbol=symbol, timeframe=timeframe)

    if "sma" in indicators:
        sma_values = calculate_sma(closes, period)
        offset = len(closes) - len(sma_values)
        result.sma = [
            IndicatorValue(timestamp=candles[i + offset].timestamp, value=v)
            for i, v in enumerate(sma_values)
        ]

    if "ema" in indicators:
        ema_values = calculate_ema(closes, period)
        offset = len(closes) - len(ema_values)
        result.ema = [
            IndicatorValue(timestamp=candles[i + offset].timestamp, value=v)
            for i, v in enumerate(ema_values)
        ]

    if "rsi" in indicators:
        rsi_values = calculate_rsi(closes, period)
        offset = len(closes) - len(rsi_values)
        result.rsi = [
            IndicatorValue(timestamp=candles[i + offset].timestamp, value=v)
            for i, v in enumerate(rsi_values)
        ]

    if "macd" in indicators:
        macd_line, signal_line, histogram = calculate_macd(closes)
        if macd_line and signal_line:
            offset = len(macd_line) - len(signal_line)
            result.macd = [
                MACDValue(
                    timestamp=candles[len(closes) - len(macd_line) + i + offset].timestamp,
                    macd=macd_line[i + offset],
                    signal=signal_line[i],
                    histogram=histogram[i] if i < len(histogram) else 0.0,
                )
                for i in range(len(signal_line))
            ]

    if "bollinger" in indicators:
        upper, middle, lower = calculate_bollinger(closes, period)
        if upper:
            offset = len(closes) - len(upper)
            result.bollinger = [
                BollingerValue(
                    timestamp=candles[i + offset].timestamp,
                    upper=upper[i],
                    middle=middle[i],
                    lower=lower[i],
                )
                for i in range(len(upper))
            ]

    if "atr" in indicators:
        atr_values = calculate_atr(candles, period)
        if atr_values:
            offset = len(candles) - len(atr_values)
            result.atr = [
                IndicatorValue(timestamp=candles[i + offset].timestamp, value=v)
                for i, v in enumerate(atr_values)
            ]

    if "stochastic" in indicators:
        stoch_values = calculate_stochastic(candles, period)
        if stoch_values:
            offset = len(candles) - len(stoch_values)
            result.stochastic = [
                IndicatorValue(timestamp=candles[i + offset].timestamp, value=v)
                for i, v in enumerate(stoch_values)
            ]

    result.calculated_at = datetime.utcnow()
    return result


async def get_signal(
    symbol: str,
    timeframe: str = "1h",
) -> TradingSignal:
    """Generate a trading signal based on multiple indicators."""
    from .market_data import get_klines as _get_klines  # avoid circular import at module level

    indicators = await get_indicators(
        symbol, timeframe,
        indicators=["sma", "ema", "rsi", "macd"],
        limit=200,
    )

    signal = TradingSignal(symbol=symbol, timeframe=timeframe)
    buy_score = 0.0
    sell_score = 0.0
    total_weight = 0.0

    # RSI analysis — scaled by how far from neutral (50)
    if indicators.rsi:
        last_rsi = indicators.rsi[-1].value
        rsi_signal = "oversold" if last_rsi < 30 else "overbought" if last_rsi > 70 else "neutral"
        signal.indicators_summary["rsi"] = {
            "value": round(last_rsi, 2),
            "signal": rsi_signal,
        }
        total_weight += 1.0
        if last_rsi < 30:
            buy_score += min(1.0, (30 - last_rsi) / 30 + 0.5)
        elif last_rsi > 70:
            sell_score += min(1.0, (last_rsi - 70) / 30 + 0.5)

    # MACD analysis — use histogram magnitude for scoring
    if indicators.macd:
        last_macd = indicators.macd[-1]
        prev_macd = indicators.macd[-2] if len(indicators.macd) > 1 else last_macd
        macd_cross = "bullish" if last_macd.histogram > 0 and prev_macd.histogram <= 0 else \
                      "bearish" if last_macd.histogram < 0 and prev_macd.histogram >= 0 else \
                      "above_zero" if last_macd.histogram > 0 else \
                      "below_zero" if last_macd.histogram < 0 else "neutral"
        signal.indicators_summary["macd"] = {
            "value": round(last_macd.macd, 6),
            "signal": macd_cross,
        }
        total_weight += 1.0
        if macd_cross in ("bullish", "above_zero"):
            buy_score += 1.0 if macd_cross == "bullish" else 0.5
        elif macd_cross in ("bearish", "below_zero"):
            sell_score += 1.0 if macd_cross == "bearish" else 0.5

    # EMA crossover (fast vs slow) — computed from raw closes, NOT SMA-on-SMA
    closes_available = False
    closes = []
    try:
        candles = await _get_klines(symbol, timeframe, limit=100)
        if candles and len(candles) >= 26:
            closes = [c.close for c in candles]
            closes_available = True
    except Exception:
        pass

    if closes_available:
        ema_fast = calculate_ema(closes, 12)
        ema_slow = calculate_ema(closes, 26)
        if ema_fast and ema_slow:
            offset = len(ema_fast) - len(ema_slow)
            fast_aligned = ema_fast[offset:]
            cross = "golden_cross" if fast_aligned[-1] > ema_slow[-1] else "death_cross"
            signal.indicators_summary["sma_cross"] = {
                "value": f"{fast_aligned[-1]:.2f}/{ema_slow[-1]:.2f}",
                "signal": cross,
            }
            total_weight += 1.0
            if cross == "golden_cross":
                buy_score += 1.0
            else:
                sell_score += 1.0
    elif indicators.sma and len(indicators.sma) >= 2:
        # Fallback: SMA-on-SMA (less accurate, kept for backwards compat)
        sma_short = calculate_sma([v.value for v in indicators.sma], 5)
        sma_long = calculate_sma([v.value for v in indicators.sma], 20)
        if sma_short and sma_long:
            cross = "golden_cross" if sma_short[-1] > sma_long[-1] else "death_cross"
            signal.indicators_summary["sma_cross"] = {
                "value": f"{sma_short[-1]:.2f}/{sma_long[-1]:.2f}",
                "signal": cross,
            }
            total_weight += 1.0
            if cross == "golden_cross":
                buy_score += 1.0
            else:
                sell_score += 1.0

    # Determine signal with continuous confidence (0-1 range)
    if total_weight > 0:
        net_score = (buy_score - sell_score) / total_weight  # -1 to +1
        if net_score > 0.05:
            signal.signal = Signal.BUY
            signal.confidence = round(min(1.0, abs(net_score)), 3)
        elif net_score < -0.05:
            signal.signal = Signal.SELL
            signal.confidence = round(min(1.0, abs(net_score)), 3)
        else:
            signal.signal = Signal.HOLD
            signal.confidence = round(0.5 - abs(net_score), 3)

    signal.generated_at = datetime.utcnow()
    return signal
