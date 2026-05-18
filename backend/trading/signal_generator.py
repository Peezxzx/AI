"""
Signal Generator - Real-time signal generation with confidence scoring.

Generates trading signals by running the strategy engine, applying filters,
and producing actionable recommendations with entry/exit levels.
"""
import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field, asdict

from .models import Signal
from .strategy_engine import (
    run_all_strategies, AggregatedSignal, StrategyType,
)
from .risk import assess_risk, calculate_stop_loss, calculate_take_profit
from .market_data import get_klines, get_current_price
from .analysis import calculate_atr


# Signal history storage
SIGNAL_LOG_DIR = Path("/tmp/atsawin_signals")
SIGNAL_LOG_DIR.mkdir(exist_ok=True)


@dataclass
class SignalRecommendation:
    """Complete trading recommendation with entry/exit levels."""
    symbol: str
    timeframe: str
    signal: str  # "buy" | "sell" | "hold"
    confidence: float
    consensus: str
    entry_price: float
    stop_loss: float
    take_profit: float
    risk_reward_ratio: float
    position_size: float
    risk_level: str
    strategy_signals: list[dict]
    indicators_summary: dict
    warnings: list[str]
    generated_at: str

    def to_dict(self) -> dict:
        return asdict(self)

    def summary_text(self) -> str:
        """Human-readable summary."""
        emoji = {"buy": "🟢", "sell": "🔴", "hold": "🟡"}.get(self.signal, "⚪")
        lines = [
            f"{emoji} {self.symbol} ({self.timeframe})",
            f"Signal: {self.signal.upper()} | Confidence: {self.confidence:.0%}",
            f"Consensus: {self.consensus}",
            f"",
            f"Entry: {self.entry_price:.6f}",
            f"Stop Loss: {self.stop_loss:.6f}",
            f"Take Profit: {self.take_profit:.6f}",
            f"R:R = {self.risk_reward_ratio:.2f}",
            f"Position Size: {self.position_size:.4f}",
            f"Risk: {self.risk_level}",
        ]
        if self.warnings:
            lines.append("")
            for w in self.warnings:
                lines.append(f"⚠️ {w}")
        return "\n".join(lines)


@dataclass
class WatchlistConfig:
    """Configuration for a watchlist of symbols."""
    symbols: list[str] = field(default_factory=lambda: [
        "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT"
    ])
    timeframes: list[str] = field(default_factory=lambda: ["1h", "4h"])
    min_confidence: float = 0.5
    strategies: list[str] = field(default_factory=lambda: [
        "sma_crossover", "rsi_mean_reversion", "macd_momentum",
        "bollinger_breakout", "stochastic_rsi", "atr_trend",
    ])


async def generate_signal(
    symbol: str,
    timeframe: str = "1h",
    capital: float = 10000.0,
    risk_percent: float = 2.0,
    strategies: list[str] | None = None,
) -> SignalRecommendation:
    """Generate a complete trading signal recommendation."""
    # Run strategy engine
    strategy_types = None
    if strategies:
        strategy_types = [StrategyType(s) for s in strategies if s in [e.value for e in StrategyType]]

    agg = await run_all_strategies(
        symbol=symbol,
        timeframe=timeframe,
        strategies=strategy_types,
    )

    # Get current price
    try:
        entry_price = await get_current_price(symbol)
    except Exception:
        entry_price = 0.0

    # Calculate ATR for stop loss / take profit
    candles = await get_klines(symbol, timeframe, limit=50)
    atr_value = 0.0
    if candles:
        atr_values = calculate_atr(candles, period=14)
        if atr_values:
            atr_value = atr_values[-1]

    # Calculate stop loss and take profit
    direction = agg.signal.value
    if direction == "buy":
        stop_loss = calculate_stop_loss(entry_price, "long", atr_value, 2.0)
        take_profit = calculate_take_profit(entry_price, "long", atr_value, 3.0)
    elif direction == "sell":
        stop_loss = calculate_stop_loss(entry_price, "short", atr_value, 2.0)
        take_profit = calculate_take_profit(entry_price, "short", atr_value, 3.0)
    else:
        stop_loss = entry_price * 0.95
        take_profit = entry_price * 1.05

    # Risk:Reward ratio
    risk = abs(entry_price - stop_loss)
    reward = abs(take_profit - entry_price)
    rr_ratio = reward / risk if risk > 0 else 0.0

    # Position size based on risk
    risk_amount = capital * (risk_percent / 100)
    position_size = risk_amount / risk if risk > 0 else 0.0

    # Risk assessment
    risk_level = "medium"
    warnings = []
    try:
        assessment = await assess_risk(symbol, capital)
        risk_level = assessment.risk_level.value
        warnings = assessment.warnings
    except Exception:
        pass

    # Build strategy signals summary
    strategy_signals = []
    for s in agg.strategy_signals:
        strategy_signals.append({
            "strategy": s.strategy.value,
            "signal": s.signal.value,
            "confidence": round(s.confidence, 3),
            "weight": s.weight,
            "details": s.details,
        })

    # Indicators summary from strategies
    indicators_summary = {}
    for s in agg.strategy_signals:
        if "rsi" in s.details:
            indicators_summary["rsi"] = s.details["rsi"]
        if "macd" in s.details:
            indicators_summary["macd"] = s.details["macd"]
        if "fast_sma" in s.details:
            indicators_summary["sma_cross"] = f"{s.details.get('fast_sma', 0)}/{s.details.get('slow_sma', 0)}"
        if "atr" in s.details:
            indicators_summary["atr"] = s.details["atr"]
        if "stochastic" in s.details:
            indicators_summary["stochastic"] = s.details["stochastic"]

    rec = SignalRecommendation(
        symbol=symbol,
        timeframe=timeframe,
        signal=agg.signal.value,
        confidence=round(agg.confidence, 3),
        consensus=agg.consensus,
        entry_price=round(entry_price, 6),
        stop_loss=round(stop_loss, 6),
        take_profit=round(take_profit, 6),
        risk_reward_ratio=round(rr_ratio, 2),
        position_size=round(position_size, 6),
        risk_level=risk_level,
        strategy_signals=strategy_signals,
        indicators_summary=indicators_summary,
        warnings=warnings,
        generated_at=datetime.utcnow().isoformat(),
    )

    # Log signal
    _log_signal(rec)

    return rec


async def scan_watchlist(
    config: WatchlistConfig | None = None,
    capital: float = 10000.0,
    risk_percent: float = 2.0,
) -> list[SignalRecommendation]:
    """Scan all symbols in watchlist for trading opportunities."""
    if config is None:
        config = WatchlistConfig()

    results = []

    for symbol in config.symbols:
        for timeframe in config.timeframes:
            try:
                rec = await generate_signal(
                    symbol=symbol,
                    timeframe=timeframe,
                    capital=capital,
                    risk_percent=risk_percent,
                    strategies=config.strategies,
                )
                if rec.confidence >= config.min_confidence and rec.signal != "hold":
                    results.append(rec)
            except Exception:
                continue

    # Sort by confidence descending
    results.sort(key=lambda r: r.confidence, reverse=True)
    return results


def _log_signal(rec: SignalRecommendation):
    """Log signal to file."""
    try:
        log_file = SIGNAL_LOG_DIR / f"{rec.symbol}_{rec.timeframe}.jsonl"
        with open(log_file, "a") as f:
            f.write(json.dumps(rec.to_dict()) + "\n")
    except Exception:
        pass


def get_signal_history(symbol: str, timeframe: str = "1h", limit: int = 20) -> list[dict]:
    """Get signal history for a symbol."""
    log_file = SIGNAL_LOG_DIR / f"{symbol}_{timeframe}.jsonl"
    if not log_file.exists():
        return []

    try:
        lines = log_file.read_text().strip().split("\n")
        history = []
        for line in lines[-limit:]:
            try:
                history.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return history
    except Exception:
        return []
