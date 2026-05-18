"""
Portfolio Management - Track positions, PnL, portfolio value
"""
import json
from datetime import datetime
from pathlib import Path
from .models import Portfolio, Position, PositionDirection
from .market_data import get_ticker, get_current_price

# Portfolio data file
PORTFOLIO_FILE = Path("/tmp/atsawin_portfolio.json")


def _load_portfolio() -> Portfolio:
    """Load portfolio from disk."""
    if PORTFOLIO_FILE.exists():
        try:
            data = json.loads(PORTFOLIO_FILE.read_text())
            positions = []
            for p in data.get("positions", []):
                positions.append(Position(
                    symbol=p["symbol"],
                    quantity=p["quantity"],
                    average_entry=p["average_entry"],
                    current_price=p.get("current_price", 0),
                    pnl=p.get("pnl", 0),
                    pnl_percent=p.get("pnl_percent", 0),
                    value=p.get("value", 0),
                    direction=PositionDirection(p.get("direction", "long")),
                ))
            return Portfolio(
                total_value=data.get("total_value", 0),
                cash=data.get("cash", 10000),
                invested=data.get("invested", 0),
                pnl_today=data.get("pnl_today", 0),
                pnl_total=data.get("pnl_total", 0),
                positions=positions,
            )
        except (json.JSONDecodeError, KeyError):
            pass
    return Portfolio(cash=10000)


def _save_portfolio(portfolio: Portfolio):
    """Save portfolio to disk."""
    data = {
        "total_value": portfolio.total_value,
        "cash": portfolio.cash,
        "invested": portfolio.invested,
        "pnl_today": portfolio.pnl_today,
        "pnl_total": portfolio.pnl_total,
        "positions": [
            {
                "symbol": p.symbol,
                "quantity": p.quantity,
                "average_entry": p.average_entry,
                "current_price": p.current_price,
                "pnl": p.pnl,
                "pnl_percent": p.pnl_percent,
                "value": p.value,
                "direction": p.direction.value,
            }
            for p in portfolio.positions
        ],
        "updated_at": datetime.utcnow().isoformat(),
    }
    PORTFOLIO_FILE.write_text(json.dumps(data, indent=2))


async def get_portfolio() -> Portfolio:
    """Get current portfolio with live prices."""
    portfolio = _load_portfolio()

    total_invested = 0.0
    total_pnl = 0.0

    for position in portfolio.positions:
        try:
            ticker = await get_ticker(position.symbol)
            position.current_price = ticker.last_price
            position.value = position.quantity * position.current_price

            if position.direction == PositionDirection.LONG:
                position.pnl = (position.current_price - position.average_entry) * position.quantity
                position.pnl_percent = ((position.current_price / position.average_entry) - 1) * 100
            else:
                position.pnl = (position.average_entry - position.current_price) * position.quantity
                position.pnl_percent = ((position.average_entry / position.current_price) - 1) * 100

            total_invested += position.value
            total_pnl += position.pnl
        except Exception:
            pass

    portfolio.invested = total_invested
    portfolio.total_value = portfolio.cash + total_invested
    portfolio.pnl_total = total_pnl
    portfolio.updated_at = datetime.utcnow()

    _save_portfolio(portfolio)
    return portfolio


async def add_position(
    symbol: str,
    quantity: float,
    entry_price: float,
    direction: PositionDirection = PositionDirection.LONG,
) -> Position:
    """Add a new position to the portfolio."""
    portfolio = _load_portfolio()

    # Check if position already exists
    for p in portfolio.positions:
        if p.symbol == symbol and p.direction == direction:
            # Update existing position (average entry)
            total_qty = p.quantity + quantity
            total_cost = (p.quantity * p.average_entry) + (quantity * entry_price)
            p.average_entry = total_cost / total_qty
            p.quantity = total_qty
            _save_portfolio(portfolio)
            return p

    # New position
    position = Position(
        symbol=symbol,
        quantity=quantity,
        average_entry=entry_price,
        current_price=entry_price,
        pnl=0.0,
        pnl_percent=0.0,
        value=quantity * entry_price,
        direction=direction,
    )
    portfolio.positions.append(position)
    portfolio.cash -= quantity * entry_price
    _save_portfolio(portfolio)
    return position


async def close_position(symbol: str, direction: PositionDirection = PositionDirection.LONG) -> float:
    """Close a position and return PnL."""
    portfolio = _load_portfolio()

    for i, p in enumerate(portfolio.positions):
        if p.symbol == symbol and p.direction == direction:
            try:
                current_price = await get_current_price(symbol)
            except Exception:
                current_price = p.current_price

            if direction == PositionDirection.LONG:
                pnl = (current_price - p.average_entry) * p.quantity
            else:
                pnl = (p.average_entry - current_price) * p.quantity

            portfolio.cash += p.quantity * current_price
            portfolio.positions.pop(i)
            _save_portfolio(portfolio)
            return pnl

    return 0.0


async def reset_portfolio(initial_cash: float = 10000) -> Portfolio:
    """Reset portfolio to initial state."""
    portfolio = Portfolio(cash=initial_cash)
    _save_portfolio(portfolio)
    return portfolio
