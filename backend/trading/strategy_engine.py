"""
Strategy Engine - Multi-strategy trading engine with signal aggregation.

Supports multiple strategies running simultaneously, aggregates their signals
into a composite recommendation with confidence scoring.
"""
import asyncio
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime
from enum import Enum

from .models import Signal, Candle
from .market_data import get_klines
from .analysis import (
    calculate_sma, calculate_ema, calculate_rsi,
    calculate_macd, calculate_bollinger, calculate_atr,
    calculate_stochastic,
)


class StrategyType(str, Enum):
    SMA_CROSSOVER = "sma_crossover"
    RSI_MEAN_REVERSION = "rsi_mean_reversion"
    MACD_MOMENTUM = "macd_momentum"
    BOLLINGER_BREAKOUT = "bollinger_breakout"
    STOCHASTIC_RSI = "stochastic_rsi"
    MULTI_TIMEFRAME = "multi_timeframe"
    ATR_TREND = "atr_trend"


@dataclass
class StrategySignal:
    """Signal from a single strategy."""
    strategy: StrategyType
    signal: Signal
    confidence: float  # 0.0 - 1.0
    weight: float = 1.0  # Strategy weight for aggregation
    details: dict = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class AggregatedSignal:
    """Composite signal from all strategies."""
    symbol: str
    timeframe: str
    signal: Signal
    confidence: float
    strategy_signals: list[StrategySignal] = field(default_factory=list)
    buy_score: float = 0.0
    sell_score: float = 0.0
    hold_score: float = 0.0
    total_weight: float = 0.0
    timestamp: datetime = field(default_factory=datetime.utcnow)

    @property
    def consensus(self) -> str:
        """How many strategies agree."""
        if not self.strategy_signals:
            return "none"
        buy_count = sum(1 for s in self.strategy_signals if s.signal == Signal.BUY)
        sell_count = sum(1 for s in self.strategy_signals if s.signal == Signal.SELL)
        hold_count = sum(1 for s in self.strategy_signals if s.signal == Signal.HOLD)
        total = len(self.strategy_signals)
        if buy_count > total * 0.6:
            return "strong_buy"
        elif sell_count > total * 0.6:
            return "strong_sell"
        elif buy_count > sell_count:
            return "weak_buy"
        elif sell_count > buy_count:
            return "weak_sell"
        else:
            return "mixed"


# ─── Individual Strategy Functions ───────────────────────────

async def strategy_sma_crossover(
    symbol: str,
    timeframe: str,
    candles: list[Candle],
    params: dict | None = None,
) -> StrategySignal:
    """SMA Crossover: fast/slow SMA cross with trend confirmation."""
    p = params or {}
    fast_period = p.get("fast_period", 10)
    slow_period = p.get("slow_period", 30)

    closes = [c.close for c in candles]
    if len(closes) < slow_period + 5:
        return StrategySignal(
            strategy=StrategyType.SMA_CROSSOVER,
            signal=Signal.HOLD,
            confidence=0.0,
            details={"error": "Not enough data"},
        )

    fast_sma = calculate_sma(closes, fast_period)
    slow_sma = calculate_sma(closes, slow_period)

    if not fast_sma or not slow_sma:
        return StrategySignal(
            strategy=StrategyType.SMA_CROSSOVER,
            signal=Signal.HOLD,
            confidence=0.0,
            details={"error": "SMA calculation failed"},
        )

    # Align
    offset = slow_period - fast_period
    aligned_fast = fast_sma[offset:]

    # Current and previous positions
    curr_diff = aligned_fast[-1] - slow_sma[-1]
    prev_diff = aligned_fast[-2] - slow_sma[-2]

    details = {
        "fast_sma": round(aligned_fast[-1], 6),
        "slow_sma": round(slow_sma[-1], 6),
        "diff": round(curr_diff, 6),
    }

    # Golden cross (fast crosses above slow)
    if curr_diff > 0 and prev_diff <= 0:
        return StrategySignal(
            strategy=StrategyType.SMA_CROSSOVER,
            signal=Signal.BUY,
            confidence=0.7,
            details={**details, "cross": "golden"},
        )
    # Death cross (fast crosses below slow)
    elif curr_diff < 0 and prev_diff >= 0:
        return StrategySignal(
            strategy=StrategyType.SMA_CROSSOVER,
            signal=Signal.SELL,
            confidence=0.7,
            details={**details, "cross": "death"},
        )
    # Trend continuation
    elif curr_diff > 0:
        return StrategySignal(
            strategy=StrategyType.SMA_CROSSOVER,
            signal=Signal.BUY,
            confidence=0.4,
            details={**details, "trend": "bullish"},
        )
    else:
        return StrategySignal(
            strategy=StrategyType.SMA_CROSSOVER,
            signal=Signal.SELL,
            confidence=0.4,
            details={**details, "trend": "bearish"},
        )


async def strategy_rsi_mean_reversion(
    symbol: str,
    timeframe: str,
    candles: list[Candle],
    params: dict | None = None,
) -> StrategySignal:
    """RSI Mean Reversion: buy oversold, sell overbought."""
    p = params or {}
    period = p.get("period", 14)
    oversold = p.get("oversold", 30)
    overbought = p.get("overbought", 70)

    closes = [c.close for c in candles]
    rsi_values = calculate_rsi(closes, period)

    if not rsi_values:
        return StrategySignal(
            strategy=StrategyType.RSI_MEAN_REVERSION,
            signal=Signal.HOLD,
            confidence=0.0,
            details={"error": "RSI calculation failed"},
        )

    last_rsi = rsi_values[-1]
    prev_rsi = rsi_values[-2] if len(rsi_values) > 1 else last_rsi

    details = {
        "rsi": round(last_rsi, 2),
        "prev_rsi": round(prev_rsi, 2),
        "oversold_threshold": oversold,
        "overbought_threshold": overbought,
    }

    # Oversold bounce
    if last_rsi < oversold and prev_rsi >= oversold:
        return StrategySignal(
            strategy=StrategyType.RSI_MEAN_REVERSION,
            signal=Signal.BUY,
            confidence=0.75,
            details={**details, "condition": "oversold_bounce"},
        )
    # Overbought reversal
    elif last_rsi > overbought and prev_rsi <= overbought:
        return StrategySignal(
            strategy=StrategyType.RSI_MEAN_REVERSION,
            signal=Signal.SELL,
            confidence=0.75,
            details={**details, "condition": "overbought_reversal"},
        )
    # Still oversold
    elif last_rsi < oversold:
        return StrategySignal(
            strategy=StrategyType.RSI_MEAN_REVERSION,
            signal=Signal.BUY,
            confidence=0.5,
            details={**details, "condition": "oversold"},
        )
    # Still overbought
    elif last_rsi > overbought:
        return StrategySignal(
            strategy=StrategyType.RSI_MEAN_REVERSION,
            signal=Signal.SELL,
            confidence=0.5,
            details={**details, "condition": "overbought"},
        )
    else:
        return StrategySignal(
            strategy=StrategyType.RSI_MEAN_REVERSION,
            signal=Signal.HOLD,
            confidence=0.3,
            details={**details, "condition": "neutral"},
        )


async def strategy_macd_momentum(
    symbol: str,
    timeframe: str,
    candles: list[Candle],
    params: dict | None = None,
) -> StrategySignal:
    """MACD Momentum: histogram crossover with momentum confirmation."""
    p = params or {}
    fast = p.get("fast", 12)
    slow = p.get("slow", 26)
    signal_period = p.get("signal_period", 9)

    closes = [c.close for c in candles]
    macd_line, signal_line, histogram = calculate_macd(closes, fast, slow, signal_period)

    if not macd_line or not signal_line or not histogram:
        return StrategySignal(
            strategy=StrategyType.MACD_MOMENTUM,
            signal=Signal.HOLD,
            confidence=0.0,
            details={"error": "MACD calculation failed"},
        )

    curr_hist = histogram[-1]
    prev_hist = histogram[-2] if len(histogram) > 1 else curr_hist

    details = {
        "macd": round(macd_line[-1], 6),
        "signal": round(signal_line[-1], 6),
        "histogram": round(curr_hist, 6),
    }

    # Bullish crossover
    if curr_hist > 0 and prev_hist <= 0:
        return StrategySignal(
            strategy=StrategyType.MACD_MOMENTUM,
            signal=Signal.BUY,
            confidence=0.7,
            details={**details, "cross": "bullish"},
        )
    # Bearish crossover
    elif curr_hist < 0 and prev_hist >= 0:
        return StrategySignal(
            strategy=StrategyType.MACD_MOMENTUM,
            signal=Signal.SELL,
            confidence=0.7,
            details={**details, "cross": "bearish"},
        )
    # Positive momentum
    elif curr_hist > 0:
        return StrategySignal(
            strategy=StrategyType.MACD_MOMENTUM,
            signal=Signal.BUY,
            confidence=0.4,
            details={**details, "momentum": "positive"},
        )
    else:
        return StrategySignal(
            strategy=StrategyType.MACD_MOMENTUM,
            signal=Signal.SELL,
            confidence=0.4,
            details={**details, "momentum": "negative"},
        )


async def strategy_bollinger_breakout(
    symbol: str,
    timeframe: str,
    candles: list[Candle],
    params: dict | None = None,
) -> StrategySignal:
    """Bollinger Bands: mean reversion at bands, breakout detection."""
    p = params or {}
    period = p.get("period", 20)
    std_dev = p.get("std_dev", 2.0)

    closes = [c.close for c in candles]
    upper, middle, lower = calculate_bollinger(closes, period, std_dev)

    if not upper or not middle or not lower:
        return StrategySignal(
            strategy=StrategyType.BOLLINGER_BREAKOUT,
            signal=Signal.HOLD,
            confidence=0.0,
            details={"error": "Bollinger calculation failed"},
        )

    last_price = closes[-1]
    last_upper = upper[-1]
    last_lower = lower[-1]
    last_middle = middle[-1]

    # Bandwidth for squeeze detection
    bandwidth = (last_upper - last_lower) / last_middle if last_middle > 0 else 0

    details = {
        "upper": round(last_upper, 6),
        "middle": round(last_middle, 6),
        "lower": round(last_lower, 6),
        "price": round(last_price, 6),
        "bandwidth": round(bandwidth, 6),
    }

    # Price below lower band -> buy (mean reversion)
    if last_price < last_lower:
        return StrategySignal(
            strategy=StrategyType.BOLLINGER_BREAKOUT,
            signal=Signal.BUY,
            confidence=0.65,
            details={**details, "condition": "below_lower_band"},
        )
    # Price above upper band -> sell (mean reversion)
    elif last_price > last_upper:
        return StrategySignal(
            strategy=StrategyType.BOLLINGER_BREAKOUT,
            signal=Signal.SELL,
            confidence=0.65,
            details={**details, "condition": "above_upper_band"},
        )
    # Squeeze (low volatility) -> prepare for breakout
    elif bandwidth < 0.05:
        return StrategySignal(
            strategy=StrategyType.BOLLINGER_BREAKOUT,
            signal=Signal.HOLD,
            confidence=0.4,
            details={**details, "condition": "squeeze"},
        )
    else:
        return StrategySignal(
            strategy=StrategyType.BOLLINGER_BREAKOUT,
            signal=Signal.HOLD,
            confidence=0.3,
            details={**details, "condition": "within_bands"},
        )


async def strategy_stochastic_rsi(
    symbol: str,
    timeframe: str,
    candles: list[Candle],
    params: dict | None = None,
) -> StrategySignal:
    """Stochastic RSI: combines Stochastic and RSI for stronger signals."""
    p = params or {}
    stoch_period = p.get("stoch_period", 14)
    rsi_period = p.get("rsi_period", 14)

    closes = [c.close for c in candles]

    # Stochastic
    stoch_values = calculate_stochastic(candles, stoch_period)
    # RSI
    rsi_values = calculate_rsi(closes, rsi_period)

    if not stoch_values or not rsi_values:
        return StrategySignal(
            strategy=StrategyType.STOCHASTIC_RSI,
            signal=Signal.HOLD,
            confidence=0.0,
            details={"error": "Calculation failed"},
        )

    last_stoch = stoch_values[-1]
    prev_stoch = stoch_values[-2] if len(stoch_values) > 1 else last_stoch
    last_rsi = rsi_values[-1]

    details = {
        "stochastic": round(last_stoch, 2),
        "rsi": round(last_rsi, 2),
    }

    # Both oversold
    if last_stoch < 20 and last_rsi < 30:
        return StrategySignal(
            strategy=StrategyType.STOCHASTIC_RSI,
            signal=Signal.BUY,
            confidence=0.8,
            details={**details, "condition": "double_oversold"},
        )
    # Both overbought
    elif last_stoch > 80 and last_rsi > 70:
        return StrategySignal(
            strategy=StrategyType.STOCHASTIC_RSI,
            signal=Signal.SELL,
            confidence=0.8,
            details={**details, "condition": "double_overbought"},
        )
    # Stochastic oversold crossover
    elif last_stoch < 20 and prev_stoch < 20:
        return StrategySignal(
            strategy=StrategyType.STOCHASTIC_RSI,
            signal=Signal.BUY,
            confidence=0.55,
            details={**details, "condition": "stoch_oversold"},
        )
    # Stochastic overbought crossover
    elif last_stoch > 80 and prev_stoch > 80:
        return StrategySignal(
            strategy=StrategyType.STOCHASTIC_RSI,
            signal=Signal.SELL,
            confidence=0.55,
            details={**details, "condition": "stoch_overbought"},
        )
    else:
        return StrategySignal(
            strategy=StrategyType.STOCHASTIC_RSI,
            signal=Signal.HOLD,
            confidence=0.3,
            details={**details, "condition": "neutral"},
        )


async def strategy_atr_trend(
    symbol: str,
    timeframe: str,
    candles: list[Candle],
    params: dict | None = None,
) -> StrategySignal:
    """ATR Trend: uses ATR for volatility-adjusted trend following."""
    p = params or {}
    atr_period = p.get("atr_period", 14)
    ema_period = p.get("ema_period", 20)

    closes = [c.close for c in candles]
    atr_values = calculate_atr(candles, atr_period)
    ema_values = calculate_ema(closes, ema_period)

    if not atr_values or not ema_values:
        return StrategySignal(
            strategy=StrategyType.ATR_TREND,
            signal=Signal.HOLD,
            confidence=0.0,
            details={"error": "Calculation failed"},
        )

    last_price = closes[-1]
    last_atr = atr_values[-1]
    last_ema = ema_values[-1]

    # ATR as percentage of price
    atr_pct = (last_atr / last_price * 100) if last_price > 0 else 0

    details = {
        "atr": round(last_atr, 6),
        "atr_percent": round(atr_pct, 3),
        "ema": round(last_ema, 6),
        "price": round(last_price, 6),
    }

    # Price above EMA with low ATR -> strong uptrend
    if last_price > last_ema and atr_pct < 2.0:
        return StrategySignal(
            strategy=StrategyType.ATR_TREND,
            signal=Signal.BUY,
            confidence=0.6,
            details={**details, "condition": "strong_uptrend"},
        )
    # Price below EMA with low ATR -> strong downtrend
    elif last_price < last_ema and atr_pct < 2.0:
        return StrategySignal(
            strategy=StrategyType.ATR_TREND,
            signal=Signal.SELL,
            confidence=0.6,
            details={**details, "condition": "strong_downtrend"},
        )
    # High ATR -> volatile, be cautious
    elif atr_pct > 5.0:
        return StrategySignal(
            strategy=StrategyType.ATR_TREND,
            signal=Signal.HOLD,
            confidence=0.5,
            details={**details, "condition": "high_volatility"},
        )
    else:
        return StrategySignal(
            strategy=StrategyType.ATR_TREND,
            signal=Signal.HOLD,
            confidence=0.3,
            details={**details, "condition": "normal"},
        )


# ─── Strategy Registry ───────────────────────────────────────

STRATEGY_FUNCTIONS = {
    StrategyType.SMA_CROSSOVER: strategy_sma_crossover,
    StrategyType.RSI_MEAN_REVERSION: strategy_rsi_mean_reversion,
    StrategyType.MACD_MOMENTUM: strategy_macd_momentum,
    StrategyType.BOLLINGER_BREAKOUT: strategy_bollinger_breakout,
    StrategyType.STOCHASTIC_RSI: strategy_stochastic_rsi,
    StrategyType.ATR_TREND: strategy_atr_trend,
}

# Default weights for each strategy
DEFAULT_WEIGHTS = {
    StrategyType.SMA_CROSSOVER: 1.0,
    StrategyType.RSI_MEAN_REVERSION: 1.2,
    StrategyType.MACD_MOMENTUM: 1.0,
    StrategyType.BOLLINGER_BREAKOUT: 0.8,
    StrategyType.STOCHASTIC_RSI: 1.1,
    StrategyType.ATR_TREND: 0.9,
}


async def run_all_strategies(
    symbol: str,
    timeframe: str = "1h",
    strategies: list[StrategyType] | None = None,
    strategy_params: dict | None = None,
    limit: int = 200,
) -> AggregatedSignal:
    """Run all strategies and aggregate signals."""
    if strategies is None:
        strategies = list(STRATEGY_FUNCTIONS.keys())

    # Fetch data once for all strategies
    candles = await get_klines(symbol, timeframe, limit)
    if not candles or len(candles) < 30:
        return AggregatedSignal(
            symbol=symbol,
            timeframe=timeframe,
            signal=Signal.HOLD,
            confidence=0.0,
        )

    # Run all strategies concurrently
    tasks = []
    for stype in strategies:
        func = STRATEGY_FUNCTIONS.get(stype)
        if func:
            params = (strategy_params or {}).get(stype.value, {})
            tasks.append(func(symbol, timeframe, candles, params))

    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Collect valid signals
    strategy_signals = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            continue
        if result and result.confidence > 0:
            result.weight = DEFAULT_WEIGHTS.get(strategies[i], 1.0)
            strategy_signals.append(result)

    # Aggregate
    return _aggregate_signals(symbol, timeframe, strategy_signals)


def _aggregate_signals(
    symbol: str,
    timeframe: str,
    signals: list[StrategySignal],
) -> AggregatedSignal:
    """Aggregate multiple strategy signals into one composite signal."""
    agg = AggregatedSignal(symbol=symbol, timeframe=timeframe)

    if not signals:
        agg.signal = Signal.HOLD
        agg.confidence = 0.0
        return agg

    agg.strategy_signals = signals

    total_weight = sum(s.weight for s in signals)
    buy_score = 0.0
    sell_score = 0.0
    hold_score = 0.0

    for s in signals:
        weighted_conf = s.confidence * s.weight
        if s.signal == Signal.BUY:
            buy_score += weighted_conf
        elif s.signal == Signal.SELL:
            sell_score += weighted_conf
        else:
            hold_score += weighted_conf

    agg.buy_score = buy_score
    agg.sell_score = sell_score
    agg.hold_score = hold_score
    agg.total_weight = total_weight

    if total_weight == 0:
        agg.signal = Signal.HOLD
        agg.confidence = 0.0
        return agg

    # Determine composite signal
    buy_ratio = buy_score / total_weight
    sell_ratio = sell_score / total_weight
    hold_ratio = hold_score / total_weight

    if buy_ratio > sell_ratio and buy_ratio > hold_ratio:
        agg.signal = Signal.BUY
        agg.confidence = min(1.0, buy_ratio)
    elif sell_ratio > buy_ratio and sell_ratio > hold_ratio:
        agg.signal = Signal.SELL
        agg.confidence = min(1.0, sell_ratio)
    else:
        agg.signal = Signal.HOLD
        agg.confidence = min(1.0, hold_ratio)

    return agg
