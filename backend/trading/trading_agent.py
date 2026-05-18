"""
Trading Agent - Main orchestrator for the Enhanced Trading Agent (EA).

Coordinates strategy engine, signal generator, and auto executor.
Can run in manual mode (signal only) or auto mode (paper trading).
"""
import asyncio
import json
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

from .strategy_engine import AggregatedSignal, StrategyType, run_all_strategies
from .signal_generator import (
    SignalRecommendation, WatchlistConfig,
    generate_signal, scan_watchlist, get_signal_history,
)
from .auto_executor import (
    ExecutorState, PaperOrder, OrderStatus,
    get_state, update_state, reset_state,
    execute_signal, check_open_positions, close_position,
    run_scan_cycle, get_performance_stats,
    get_open_positions, get_trade_history,
)
from .risk import assess_risk, get_risk_limits, set_risk_limits
from .portfolio import get_portfolio, add_position, close_position as close_portfolio_position


@dataclass
class AgentConfig:
    """Configuration for the trading agent."""
    mode: str = "manual"  # "manual" | "auto" | "paper"
    symbols: list[str] = field(default_factory=lambda: [
        "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT"
    ])
    timeframe: str = "1h"
    capital: float = 10000.0
    risk_percent: float = 2.0
    max_open_positions: int = 3
    min_confidence: float = 0.5
    min_risk_reward: float = 1.5
    scan_interval_seconds: int = 300  # 5 minutes
    strategies: list[str] = field(default_factory=lambda: [
        "sma_crossover", "rsi_mean_reversion", "macd_momentum",
        "bollinger_breakout", "stochastic_rsi", "atr_trend",
    ])


class TradingAgent:
    """
    Enhanced Trading Agent (EA) - Main orchestrator.

    Usage:
        agent = TradingAgent(AgentConfig(mode="paper"))
        await agent.start()

        # Or manual mode:
        agent = TradingAgent()
        signal = await agent.analyze("BTCUSDT")
        await agent.execute(signal)
    """

    def __init__(self, config: AgentConfig | None = None):
        self.config = config or AgentConfig()
        self._running = False
        self._scan_count = 0

    @property
    def is_running(self) -> bool:
        return self._running

    async def analyze(
        self,
        symbol: str,
        timeframe: str | None = None,
    ) -> SignalRecommendation:
        """Analyze a symbol and generate a signal recommendation."""
        tf = timeframe or self.config.timeframe
        return await generate_signal(
            symbol=symbol,
            timeframe=tf,
            capital=self.config.capital,
            risk_percent=self.config.risk_percent,
            strategies=self.config.strategies,
        )

    async def scan(
        self,
        symbols: list[str] | None = None,
        min_confidence: float | None = None,
    ) -> list[SignalRecommendation]:
        """Scan multiple symbols for trading opportunities."""
        config = WatchlistConfig(
            symbols=symbols or self.config.symbols,
            timeframes=[self.config.timeframe],
            min_confidence=min_confidence or self.config.min_confidence,
            strategies=self.config.strategies,
        )
        return await scan_watchlist(
            config=config,
            capital=self.config.capital,
            risk_percent=self.config.risk_percent,
        )

    async def execute(
        self,
        recommendation: SignalRecommendation,
    ) -> PaperOrder | None:
        """Execute a signal recommendation."""
        state = get_state()
        if len(state.open_positions) >= self.config.max_open_positions:
            return None
        return await execute_signal(
            recommendation,
            capital=self.config.capital,
            risk_percent=self.config.risk_percent,
        )

    async def start(self):
        """Start the trading agent in auto mode."""
        if self._running:
            return

        self._running = True
        update_state(
            running=True,
            capital=self.config.capital,
            initial_capital=self.config.capital,
            risk_percent=self.config.risk_percent,
            max_open_positions=self.config.max_open_positions,
            min_confidence=self.config.min_confidence,
            min_risk_reward=self.config.min_risk_reward,
            watchlist=self.config.symbols,
            timeframe=self.config.timeframe,
            strategies=self.config.strategies,
        )

        while self._running:
            try:
                await run_scan_cycle()
                self._scan_count += 1
            except Exception:
                pass

            await asyncio.sleep(self.config.scan_interval_seconds)

    def stop(self):
        """Stop the trading agent."""
        self._running = False
        update_state(running=False)

    def status(self) -> dict:
        """Get agent status."""
        perf = get_performance_stats()
        return {
            "running": self._running,
            "mode": self.config.mode,
            "scan_count": self._scan_count,
            "config": {
                "symbols": self.config.symbols,
                "timeframe": self.config.timeframe,
                "capital": self.config.capital,
                "risk_percent": self.config.risk_percent,
                "max_open_positions": self.config.max_open_positions,
                "min_confidence": self.config.min_confidence,
                "min_risk_reward": self.config.min_risk_reward,
                "scan_interval_seconds": self.config.scan_interval_seconds,
                "strategies": self.config.strategies,
            },
            "performance": perf,
        }


# Singleton agent instance
_agent: TradingAgent | None = None


def get_agent(config: AgentConfig | None = None) -> TradingAgent:
    """Get or create the singleton trading agent."""
    global _agent
    if _agent is None:
        _agent = TradingAgent(config)
    return _agent


def reset_agent(config: AgentConfig | None = None) -> TradingAgent:
    """Reset the singleton trading agent."""
    global _agent
    _agent = TradingAgent(config)
    return _agent
