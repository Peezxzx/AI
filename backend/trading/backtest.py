"""
Backtesting Framework - Strategy testing on historical data
"""
import asyncio
import uuid
import math
from datetime import datetime
from .models import (
    BacktestResult, BacktestSummary, Trade, PositionDirection,
    Signal,
)
from .market_data import get_klines
from .analysis import calculate_sma, calculate_ema, calculate_rsi, calculate_macd

# In-memory store for backtest runs
_backtest_runs: dict[str, BacktestResult] = {}


async def run_backtest(
    strategy: str,
    symbol: str,
    timeframe: str = "1h",
    start_date: str | None = None,
    end_date: str | None = None,
    initial_capital: float = 10000.0,
    position_size: float = 0.1,
    stop_loss: float | None = None,
    take_profit: float | None = None,
    strategy_params: dict | None = None,
) -> BacktestResult:
    """Run a backtest for a strategy."""
    backtest_id = str(uuid.uuid4())[:12]
    result = BacktestResult(
        backtest_id=backtest_id,
        status="started",
        strategy=strategy,
        symbol=symbol,
        timeframe=timeframe,
    )
    _backtest_runs[backtest_id] = result

    # Execute backtest asynchronously
    asyncio.create_task(_execute_backtest(
        backtest_id, strategy, symbol, timeframe,
        initial_capital, position_size, stop_loss, take_profit,
        strategy_params or {},
    ))

    return result


async def _execute_backtest(
    backtest_id: str,
    strategy: str,
    symbol: str,
    timeframe: str,
    initial_capital: float,
    position_size: float,
    stop_loss: float | None,
    take_profit: float | None,
    strategy_params: dict,
):
    """Execute backtest with the given strategy."""
    result = _backtest_runs[backtest_id]
    result.status = "running"
    start_time = datetime.utcnow()

    try:
        # Fetch historical data
        candles = await get_klines(symbol, timeframe, limit=1000)
        if not candles or len(candles) < 50:
            result.status = "failed"
            return

        closes = [c.close for c in candles]

        # Run strategy
        if strategy == "sma_crossover":
            trades = _strategy_sma_crossover(
                candles, closes, initial_capital, position_size,
                stop_loss, take_profit, strategy_params,
            )
        elif strategy == "rsi_mean_reversion":
            trades = _strategy_rsi_mean_reversion(
                candles, closes, initial_capital, position_size,
                stop_loss, take_profit, strategy_params,
            )
        elif strategy == "macd_momentum":
            trades = _strategy_macd_momentum(
                candles, closes, initial_capital, position_size,
                stop_loss, take_profit, strategy_params,
            )
        else:
            # Default: SMA crossover
            trades = _strategy_sma_crossover(
                candles, closes, initial_capital, position_size,
                stop_loss, take_profit, strategy_params,
            )

        # Calculate summary
        result.trades = trades
        result.summary = _calculate_summary(trades, initial_capital)
        result.equity_curve = _build_equity_curve(trades, initial_capital, candles)
        result.status = "completed"

    except Exception as e:
        result.status = "failed"

    result.duration_seconds = (datetime.utcnow() - start_time).total_seconds()


def _strategy_sma_crossover(
    candles, closes, capital, position_size_pct,
    stop_loss, take_profit, params,
) -> list[Trade]:
    """SMA Crossover strategy: buy when fast SMA crosses above slow SMA."""
    fast_period = params.get("fast_period", 10)
    slow_period = params.get("slow_period", 30)

    fast_sma = calculate_sma(closes, fast_period)
    slow_sma = calculate_sma(closes, slow_period)

    if not fast_sma or not slow_sma:
        return []

    # Align
    offset = slow_period - fast_period
    aligned_fast = fast_sma[offset:]

    trades = []
    position = None
    cash = capital

    for i in range(1, min(len(aligned_fast), len(slow_sma))):
        candle_idx = slow_period - 1 + i
        if candle_idx >= len(candles):
            break

        # Golden cross
        if aligned_fast[i] > slow_sma[i] and aligned_fast[i - 1] <= slow_sma[i - 1]:
            if position is None:
                # Open long
                price = candles[candle_idx].close
                qty = (cash * position_size_pct) / price
                if qty > 0:
                    position = Trade(
                        entry_time=candles[candle_idx].timestamp,
                        direction=PositionDirection.LONG,
                        entry_price=price,
                        quantity=qty,
                        stop_loss=price * (1 - stop_loss) if stop_loss else None,
                        take_profit=price * (1 + take_profit) if take_profit else None,
                    )
                    cash -= qty * price

        # Death cross
        elif aligned_fast[i] < slow_sma[i] and aligned_fast[i - 1] >= slow_sma[i - 1]:
            if position is not None:
                # Close long
                price = candles[candle_idx].close
                position.exit_time = candles[candle_idx].timestamp
                position.exit_price = price
                pnl = (price - position.entry_price) * position.quantity
                position.pnl = pnl
                position.pnl_percent = (price / position.entry_price - 1) * 100
                trades.append(position)
                cash += position.quantity * price
                position = None

        # Check stop loss / take profit
        if position is not None:
            price = candles[candle_idx].close
            if position.stop_loss and price <= position.stop_loss:
                position.exit_time = candles[candle_idx].timestamp
                position.exit_price = price
                pnl = (price - position.entry_price) * position.quantity
                position.pnl = pnl
                position.pnl_percent = (price / position.entry_price - 1) * 100
                trades.append(position)
                cash += position.quantity * price
                position = None
            elif position.take_profit and price >= position.take_profit:
                position.exit_time = candles[candle_idx].timestamp
                position.exit_price = price
                pnl = (price - position.entry_price) * position.quantity
                position.pnl = pnl
                position.pnl_percent = (price / position.entry_price - 1) * 100
                trades.append(position)
                cash += position.quantity * price
                position = None

    # Close any open position at the end
    if position is not None:
        price = candles[-1].close
        position.exit_time = candles[-1].timestamp
        position.exit_price = price
        pnl = (price - position.entry_price) * position.quantity
        position.pnl = pnl
        position.pnl_percent = (price / position.entry_price - 1) * 100
        trades.append(position)

    return trades


def _strategy_rsi_mean_reversion(
    candles, closes, capital, position_size_pct,
    stop_loss, take_profit, params,
) -> list[Trade]:
    """RSI Mean Reversion: buy when RSI < oversold, sell when RSI > overbought."""
    period = params.get("rsi_period", 14)
    oversold = params.get("oversold", 30)
    overbought = params.get("overbought", 70)

    rsi_values = calculate_rsi(closes, period)
    if not rsi_values:
        return []

    trades = []
    position = None
    cash = capital
    offset = len(closes) - len(rsi_values)

    for i in range(1, len(rsi_values)):
        candle_idx = offset + i
        if candle_idx >= len(candles):
            break

        # RSI oversold -> buy
        if rsi_values[i] < oversold and rsi_values[i - 1] >= oversold:
            if position is None:
                price = candles[candle_idx].close
                qty = (cash * position_size_pct) / price
                if qty > 0:
                    position = Trade(
                        entry_time=candles[candle_idx].timestamp,
                        direction=PositionDirection.LONG,
                        entry_price=price,
                        quantity=qty,
                        stop_loss=price * (1 - stop_loss) if stop_loss else None,
                        take_profit=price * (1 + take_profit) if take_profit else None,
                    )
                    cash -= qty * price

        # RSI overbought -> sell
        elif rsi_values[i] > overbought and rsi_values[i - 1] <= overbought:
            if position is not None:
                price = candles[candle_idx].close
                position.exit_time = candles[candle_idx].timestamp
                position.exit_price = price
                pnl = (price - position.entry_price) * position.quantity
                position.pnl = pnl
                position.pnl_percent = (price / position.entry_price - 1) * 100
                trades.append(position)
                cash += position.quantity * price
                position = None

        # Check stop loss / take profit
        if position is not None:
            price = candles[candle_idx].close
            if position.stop_loss and price <= position.stop_loss:
                position.exit_time = candles[candle_idx].timestamp
                position.exit_price = price
                pnl = (price - position.entry_price) * position.quantity
                position.pnl = pnl
                position.pnl_percent = (price / position.entry_price - 1) * 100
                trades.append(position)
                cash += position.quantity * price
                position = None
            elif position.take_profit and price >= position.take_profit:
                position.exit_time = candles[candle_idx].timestamp
                position.exit_price = price
                pnl = (price - position.entry_price) * position.quantity
                position.pnl = pnl
                position.pnl_percent = (price / position.entry_price - 1) * 100
                trades.append(position)
                cash += position.quantity * price
                position = None

    if position is not None:
        price = candles[-1].close
        position.exit_time = candles[-1].timestamp
        position.exit_price = price
        pnl = (price - position.entry_price) * position.quantity
        position.pnl = pnl
        position.pnl_percent = (price / position.entry_price - 1) * 100
        trades.append(position)

    return trades


def _strategy_macd_momentum(
    candles, closes, capital, position_size_pct,
    stop_loss, take_profit, params,
) -> list[Trade]:
    """MACD Momentum: buy when MACD crosses above signal, sell when below."""
    macd_line, signal_line, histogram = calculate_macd(closes)
    if not macd_line or not signal_line:
        return []

    trades = []
    position = None
    cash = capital
    offset = len(macd_line) - len(signal_line)

    for i in range(1, len(signal_line)):
        macd_idx = i + offset
        candle_idx = len(closes) - len(macd_line) + macd_idx
        if candle_idx >= len(candles) or candle_idx < 0:
            continue

        # Bullish crossover
        if histogram[i] > 0 and (i == 0 or histogram[i - 1] <= 0):
            if position is None:
                price = candles[candle_idx].close
                qty = (cash * position_size_pct) / price
                if qty > 0:
                    position = Trade(
                        entry_time=candles[candle_idx].timestamp,
                        direction=PositionDirection.LONG,
                        entry_price=price,
                        quantity=qty,
                        stop_loss=price * (1 - stop_loss) if stop_loss else None,
                        take_profit=price * (1 + take_profit) if take_profit else None,
                    )
                    cash -= qty * price

        # Bearish crossover
        elif histogram[i] < 0 and (i == 0 or histogram[i - 1] >= 0):
            if position is not None:
                price = candles[candle_idx].close
                position.exit_time = candles[candle_idx].timestamp
                position.exit_price = price
                pnl = (price - position.entry_price) * position.quantity
                position.pnl = pnl
                position.pnl_percent = (price / position.entry_price - 1) * 100
                trades.append(position)
                cash += position.quantity * price
                position = None

        # Check stop loss / take profit
        if position is not None:
            price = candles[candle_idx].close
            if position.stop_loss and price <= position.stop_loss:
                position.exit_time = candles[candle_idx].timestamp
                position.exit_price = price
                pnl = (price - position.entry_price) * position.quantity
                position.pnl = pnl
                position.pnl_percent = (price / position.entry_price - 1) * 100
                trades.append(position)
                cash += position.quantity * price
                position = None
            elif position.take_profit and price >= position.take_profit:
                position.exit_time = candles[candle_idx].timestamp
                position.exit_price = price
                pnl = (price - position.entry_price) * position.quantity
                position.pnl = pnl
                position.pnl_percent = (price / position.entry_price - 1) * 100
                trades.append(position)
                cash += position.quantity * price
                position = None

    if position is not None:
        price = candles[-1].close
        position.exit_time = candles[-1].timestamp
        position.exit_price = price
        pnl = (price - position.entry_price) * position.quantity
        position.pnl = pnl
        position.pnl_percent = (price / position.entry_price - 1) * 100
        trades.append(position)

    return trades


def _calculate_summary(trades: list[Trade], initial_capital: float) -> BacktestSummary:
    """Calculate backtest summary statistics."""
    summary = BacktestSummary()

    if not trades:
        return summary

    summary.total_trades = len(trades)
    summary.winning_trades = sum(1 for t in trades if t.pnl > 0)
    summary.losing_trades = sum(1 for t in trades if t.pnl <= 0)

    wins = [t.pnl for t in trades if t.pnl > 0]
    losses = [t.pnl for t in trades if t.pnl <= 0]

    summary.average_win = sum(wins) / len(wins) if wins else 0.0
    summary.average_loss = sum(losses) / len(losses) if losses else 0.0

    total_pnl = sum(t.pnl for t in trades)
    summary.total_return = total_pnl
    summary.total_return_percent = (total_pnl / initial_capital) * 100

    summary.win_rate = summary.winning_trades / summary.total_trades if summary.total_trades > 0 else 0.0

    # Profit factor
    gross_profit = sum(wins) if wins else 0.0
    gross_loss = abs(sum(losses)) if losses else 1.0
    summary.profit_factor = gross_profit / gross_loss if gross_loss > 0 else float("inf")

    # Max drawdown
    equity = initial_capital
    peak = equity
    max_dd = 0.0
    for t in trades:
        equity += t.pnl
        peak = max(peak, equity)
        dd = peak - equity
        max_dd = max(max_dd, dd)

    summary.max_drawdown = max_dd
    summary.max_drawdown_percent = (max_dd / initial_capital) * 100 if initial_capital > 0 else 0.0

    # Sharpe ratio (simplified)
    returns = [t.pnl_percent for t in trades]
    if len(returns) > 1:
        avg_return = sum(returns) / len(returns)
        variance = sum((r - avg_return) ** 2 for r in returns) / (len(returns) - 1)
        std = math.sqrt(variance) if variance > 0 else 1.0
        summary.sharpe_ratio = (avg_return / std) * math.sqrt(252) if std > 0 else 0.0

    return summary


def _build_equity_curve(trades: list[Trade], initial_capital: float, candles) -> list[dict]:
    """Build equity curve from trades."""
    equity = initial_capital
    curve = []

    for t in trades:
        equity += t.pnl
        curve.append({
            "timestamp": t.exit_time.isoformat() if t.exit_time else None,
            "value": round(equity, 2),
        })

    return curve


def get_backtest_result(backtest_id: str) -> BacktestResult | None:
    """Get backtest result."""
    return _backtest_runs.get(backtest_id)


def list_backtests() -> list[BacktestResult]:
    """List all backtest runs."""
    return list(_backtest_runs.values())
