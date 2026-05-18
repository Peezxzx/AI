"""
Auto Executor - Paper trading execution engine.

Simulates trade execution with realistic fills, tracks performance,
and manages open positions. No real money involved.
"""
import asyncio
import json
import uuid
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional
from enum import Enum

from .models import Signal, PositionDirection, Trade
from .market_data import get_current_price, get_klines
from .signal_generator import generate_signal, SignalRecommendation
from .risk import calculate_position_size, calculate_stop_loss, calculate_take_profit
from .analysis import calculate_atr


class OrderStatus(str, Enum):
    PENDING = "pending"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"


@dataclass
class PaperOrder:
    """A paper trading order."""
    order_id: str
    symbol: str
    side: str  # "buy" | "sell"
    quantity: float
    entry_price: float
    stop_loss: float
    take_profit: float
    status: OrderStatus = OrderStatus.PENDING
    filled_price: float = 0.0
    pnl: float = 0.0
    pnl_percent: float = 0.0
    created_at: str = ""
    filled_at: str = ""
    closed_at: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ExecutorState:
    """State of the auto executor."""
    running: bool = False
    capital: float = 10000.0
    initial_capital: float = 10000.0
    risk_percent: float = 2.0
    max_open_positions: int = 3
    max_daily_trades: int = 10
    min_confidence: float = 0.5
    min_risk_reward: float = 1.5
    watchlist: list[str] = field(default_factory=lambda: [
        "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT"
    ])
    timeframe: str = "1h"
    strategies: list[str] = field(default_factory=lambda: [
        "sma_crossover", "rsi_mean_reversion", "macd_momentum",
        "bollinger_breakout", "stochastic_rsi", "atr_trend",
    ])
    open_orders: list[dict] = field(default_factory=list)
    closed_orders: list[dict] = field(default_factory=list)
    daily_trades: int = 0
    daily_pnl: float = 0.0
    total_pnl: float = 0.0
    win_count: int = 0
    loss_count: int = 0
    last_scan: str = ""
    last_signal: str = ""


# State file
STATE_FILE = Path("/tmp/atsawin_executor_state.json")

# Global state
_state = ExecutorState()


def _save_state():
    """Persist state to disk."""
    try:
        STATE_FILE.write_text(json.dumps(asdict(_state), indent=2, default=str))
    except Exception:
        pass


def _load_state():
    """Load state from disk."""
    global _state
    if STATE_FILE.exists():
        try:
            data = json.loads(STATE_FILE.read_text())
            _state = ExecutorState(**{k: v for k, v in data.items() if k in ExecutorState.__dataclass_fields__})
        except Exception:
            pass


def get_state() -> ExecutorState:
    """Get current executor state."""
    return _state


def update_state(**kwargs) -> ExecutorState:
    """Update executor state."""
    global _state
    for key, value in kwargs.items():
        if hasattr(_state, key):
            setattr(_state, key, value)
    _save_state()
    return _state


def reset_state(capital: float = 10000.0) -> ExecutorState:
    """Reset executor state."""
    global _state
    _state = ExecutorState(capital=capital, initial_capital=capital)
    _save_state()
    return _state


async def execute_signal(
    recommendation: SignalRecommendation,
    capital: float | None = None,
    risk_percent: float | None = None,
) -> PaperOrder | None:
    """Execute a signal recommendation as a paper trade."""
    state = get_state()

    # Validate
    if recommendation.signal == "hold":
        return None

    if recommendation.confidence < state.min_confidence:
        return None

    if recommendation.risk_reward_ratio < state.min_risk_reward:
        return None

    if len(state.open_orders) >= state.max_open_positions:
        return None

    if state.daily_trades >= state.max_daily_trades:
        return None

    cap = capital or state.capital
    rp = risk_percent or state.risk_percent

    # Calculate position size
    risk_amount = cap * (rp / 100)
    risk_per_unit = abs(recommendation.entry_price - recommendation.stop_loss)
    if risk_per_unit <= 0:
        return None

    quantity = risk_amount / risk_per_unit

    # Create order
    order = PaperOrder(
        order_id=str(uuid.uuid4())[:12],
        symbol=recommendation.symbol,
        side=recommendation.signal,
        quantity=round(quantity, 6),
        entry_price=recommendation.entry_price,
        stop_loss=recommendation.stop_loss,
        take_profit=recommendation.take_profit,
        status=OrderStatus.PENDING,
        created_at=datetime.utcnow().isoformat(),
    )

    # Simulate fill (paper trading - fill at entry price)
    try:
        current_price = await get_current_price(recommendation.symbol)
        # Simulate slippage (0.05%)
        slippage = current_price * 0.0005
        if recommendation.signal == "buy":
            order.filled_price = current_price + slippage
        else:
            order.filled_price = current_price - slippage
    except Exception:
        order.filled_price = recommendation.entry_price

    order.status = OrderStatus.FILLED
    order.filled_at = datetime.utcnow().isoformat()

    # Update state
    state.open_orders.append(order.to_dict())
    state.daily_trades += 1
    state.last_signal = f"{recommendation.signal.upper()} {recommendation.symbol} @ {order.filled_price:.6f}"
    _save_state()

    return order


async def check_open_positions():
    """Check and update open positions (check SL/TP hits)."""
    state = get_state()
    closed = []

    for order_dict in state.open_orders[:]:
        try:
            current_price = await get_current_price(order_dict["symbol"])
            side = order_dict["side"]
            entry = order_dict["filled_price"]
            sl = order_dict["stop_loss"]
            tp = order_dict["take_profit"]
            qty = order_dict["quantity"]

            hit_sl = False
            hit_tp = False

            if side == "buy":
                if current_price <= sl:
                    hit_sl = True
                    exit_price = sl
                elif current_price >= tp:
                    hit_tp = True
                    exit_price = tp
                else:
                    exit_price = current_price
            else:  # sell/short
                if current_price >= sl:
                    hit_sl = True
                    exit_price = sl
                elif current_price <= tp:
                    hit_tp = True
                    exit_price = tp
                else:
                    exit_price = current_price

            # Update unrealized PnL
            if side == "buy":
                order_dict["pnl"] = (exit_price - entry) * qty
                order_dict["pnl_percent"] = ((exit_price / entry) - 1) * 100
            else:
                order_dict["pnl"] = (entry - exit_price) * qty
                order_dict["pnl_percent"] = ((entry / exit_price) - 1) * 100

            # Check if SL or TP hit
            if hit_sl or hit_tp:
                order_dict["status"] = OrderStatus.FILLED.value
                order_dict["closed_at"] = datetime.utcnow().isoformat()

                pnl = order_dict["pnl"]
                state.total_pnl += pnl
                state.daily_pnl += pnl
                state.capital += pnl

                if pnl > 0:
                    state.win_count += 1
                else:
                    state.loss_count += 1

                state.closed_orders.append(order_dict)
                state.open_orders.remove(order_dict)
                closed.append(order_dict)

        except Exception:
            continue

    if closed:
        _save_state()

    return closed


async def close_position(order_id: str) -> dict | None:
    """Manually close a position."""
    state = get_state()

    for order_dict in state.open_orders:
        if order_dict["order_id"] == order_id:
            try:
                current_price = await get_current_price(order_dict["symbol"])
            except Exception:
                current_price = order_dict["filled_price"]

            side = order_dict["side"]
            entry = order_dict["filled_price"]
            qty = order_dict["quantity"]

            if side == "buy":
                pnl = (current_price - entry) * qty
                pnl_pct = ((current_price / entry) - 1) * 100
            else:
                pnl = (entry - current_price) * qty
                pnl_pct = ((entry / current_price) - 1) * 100

            order_dict["pnl"] = round(pnl, 2)
            order_dict["pnl_percent"] = round(pnl_pct, 2)
            order_dict["status"] = OrderStatus.FILLED.value
            order_dict["closed_at"] = datetime.utcnow().isoformat()

            state.total_pnl += pnl
            state.daily_pnl += pnl
            state.capital += pnl

            if pnl > 0:
                state.win_count += 1
            else:
                state.loss_count += 1

            state.closed_orders.append(order_dict)
            state.open_orders.remove(order_dict)
            _save_state()

            return order_dict

    return None


async def run_scan_cycle() -> list[PaperOrder]:
    """Run one scan cycle: scan watchlist and execute signals."""
    state = get_state()
    executed = []

    state.last_scan = datetime.utcnow().isoformat()

    # Check existing positions first
    await check_open_positions()

    # Scan each symbol
    for symbol in state.watchlist:
        if len(state.open_orders) >= state.max_open_positions:
            break

        try:
            rec = await generate_signal(
                symbol=symbol,
                timeframe=state.timeframe,
                capital=state.capital,
                risk_percent=state.risk_percent,
                strategies=state.strategies,
            )

            if rec.signal != "hold" and rec.confidence >= state.min_confidence:
                if rec.risk_reward_ratio >= state.min_risk_reward:
                    order = await execute_signal(rec)
                    if order:
                        executed.append(order)
        except Exception:
            continue

    _save_state()
    return executed


def get_performance_stats() -> dict:
    """Get performance statistics."""
    state = get_state()
    total_trades = state.win_count + state.loss_count

    return {
        "capital": round(state.capital, 2),
        "initial_capital": round(state.initial_capital, 2),
        "total_pnl": round(state.total_pnl, 2),
        "total_pnl_percent": round((state.capital / state.initial_capital - 1) * 100, 2),
        "daily_pnl": round(state.daily_pnl, 2),
        "daily_trades": state.daily_trades,
        "open_positions": len(state.open_orders),
        "total_trades": total_trades,
        "win_count": state.win_count,
        "loss_count": state.loss_count,
        "win_rate": round(state.win_count / total_trades, 3) if total_trades > 0 else 0.0,
        "running": state.running,
        "last_scan": state.last_scan,
        "last_signal": state.last_signal,
    }


def get_open_positions() -> list[dict]:
    """Get all open positions."""
    return get_state().open_orders


def get_trade_history(limit: int = 50) -> list[dict]:
    """Get closed trade history."""
    state = get_state()
    return state.closed_orders[-limit:]


# Load state on import
_load_state()
