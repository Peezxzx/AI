"""
Trading API Router - REST endpoints for trading system
"""
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from .market_data import (
    get_klines, get_ticker, get_order_book,
    get_available_symbols, get_current_price,
)
from .analysis import get_indicators, get_signal
from .backtest import run_backtest, get_backtest_result, list_backtests
from .risk import (
    assess_risk, get_risk_limits, set_risk_limits,
    calculate_position_size, calculate_stop_loss, calculate_take_profit,
)
from .portfolio import get_portfolio, add_position, close_position, reset_portfolio
from .models import PositionDirection

# Enhanced Trading Agent imports
from .strategy_engine import run_all_strategies, AggregatedSignal, StrategyType
from .signal_generator import (
    generate_signal, scan_watchlist, get_signal_history,
    WatchlistConfig, SignalRecommendation,
)
from .auto_executor import (
    get_state, update_state, reset_state,
    execute_signal, check_open_positions, close_position as close_executor_position,
    run_scan_cycle, get_performance_stats,
    get_open_positions, get_trade_history,
)
from .trading_agent import TradingAgent, AgentConfig, get_agent, reset_agent

router = APIRouter(prefix="/trading", tags=["trading"])


# ─── Market Data ────────────────────────────────────────────

@router.get("/market/data")
async def market_data(
    symbol: str = Query(..., description="Trading pair symbol"),
    timeframe: str = Query(default="1h", description="Candle timeframe"),
    limit: int = Query(default=100, le=1000),
):
    """Get candlestick data."""
    try:
        candles = await get_klines(symbol, timeframe, limit)
        return {
            "symbol": symbol.upper(),
            "timeframe": timeframe,
            "data": [
                {
                    "timestamp": c.timestamp.isoformat(),
                    "open": c.open,
                    "high": c.high,
                    "low": c.low,
                    "close": c.close,
                    "volume": c.volume,
                }
                for c in candles
            ],
            "source": "binance",
            "cached": False,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Market data error: {str(e)}")


@router.get("/market/ticker")
async def market_ticker(symbol: str = Query(...)):
    """Get 24h ticker data."""
    try:
        t = await get_ticker(symbol)
        return {
            "symbol": t.symbol,
            "last_price": t.last_price,
            "bid": t.bid,
            "ask": t.ask,
            "high_24h": t.high_24h,
            "low_24h": t.low_24h,
            "volume_24h": t.volume_24h,
            "change_24h": t.change_24h,
            "change_percent_24h": t.change_percent_24h,
            "timestamp": t.timestamp.isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ticker error: {str(e)}")


@router.get("/market/orderbook")
async def market_orderbook(
    symbol: str = Query(...),
    depth: int = Query(default=20, le=100),
):
    """Get order book."""
    try:
        ob = await get_order_book(symbol, depth)
        return {
            "symbol": ob.symbol,
            "bids": ob.bids,
            "asks": ob.asks,
            "spread": ob.spread,
            "timestamp": ob.timestamp.isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Order book error: {str(e)}")


@router.get("/market/symbols")
async def market_symbols():
    """Get available trading symbols."""
    try:
        symbols = await get_available_symbols()
        return {"symbols": symbols, "count": len(symbols)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Symbols error: {str(e)}")


@router.get("/market/price")
async def market_price(symbol: str = Query(...)):
    """Get current price."""
    try:
        price = await get_current_price(symbol)
        return {"symbol": symbol.upper(), "price": price}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Price error: {str(e)}")


# ─── Technical Analysis ─────────────────────────────────────

@router.post("/analysis/indicators")
async def analysis_indicators(request: dict):
    """Calculate technical indicators."""
    try:
        result = await get_indicators(
            symbol=request["symbol"],
            timeframe=request.get("timeframe", "1h"),
            indicators=request.get("indicators", ["sma", "ema", "rsi", "macd", "bollinger"]),
            period=request.get("period", 14),
            limit=request.get("limit", 200),
        )

        response = {
            "symbol": result.symbol,
            "timeframe": result.timeframe,
            "indicators": {},
            "calculated_at": result.calculated_at.isoformat(),
        }

        if result.sma:
            response["indicators"]["sma"] = [
                {"timestamp": v.timestamp.isoformat(), "value": round(v.value, 6)}
                for v in result.sma
            ]
        if result.ema:
            response["indicators"]["ema"] = [
                {"timestamp": v.timestamp.isoformat(), "value": round(v.value, 6)}
                for v in result.ema
            ]
        if result.rsi:
            response["indicators"]["rsi"] = [
                {"timestamp": v.timestamp.isoformat(), "value": round(v.value, 2)}
                for v in result.rsi
            ]
        if result.macd:
            response["indicators"]["macd"] = [
                {
                    "timestamp": v.timestamp.isoformat(),
                    "macd": round(v.macd, 6),
                    "signal": round(v.signal, 6),
                    "histogram": round(v.histogram, 6),
                }
                for v in result.macd
            ]
        if result.bollinger:
            response["indicators"]["bollinger"] = [
                {
                    "timestamp": v.timestamp.isoformat(),
                    "upper": round(v.upper, 6),
                    "middle": round(v.middle, 6),
                    "lower": round(v.lower, 6),
                }
                for v in result.bollinger
            ]
        if result.atr:
            response["indicators"]["atr"] = [
                {"timestamp": v.timestamp.isoformat(), "value": round(v.value, 6)}
                for v in result.atr
            ]
        if result.stochastic:
            response["indicators"]["stochastic"] = [
                {"timestamp": v.timestamp.isoformat(), "value": round(v.value, 2)}
                for v in result.stochastic
            ]

        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis error: {str(e)}")


@router.get("/analysis/signal")
async def analysis_signal(
    symbol: str = Query(...),
    timeframe: str = Query(default="1h"),
):
    """Get trading signal."""
    try:
        signal = await get_signal(symbol, timeframe)
        return {
            "symbol": signal.symbol,
            "timeframe": signal.timeframe,
            "signal": signal.signal.value,
            "confidence": round(signal.confidence, 3),
            "indicators_summary": signal.indicators_summary,
            "generated_at": signal.generated_at.isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Signal error: {str(e)}")


# ─── Backtesting ───────────────────────────────────────────

@router.post("/backtest/run")
async def backtest_run(request: dict):
    """Run a backtest."""
    try:
        result = await run_backtest(
            strategy=request.get("strategy", "sma_crossover"),
            symbol=request["symbol"],
            timeframe=request.get("timeframe", "1h"),
            start_date=request.get("start_date"),
            end_date=request.get("end_date"),
            initial_capital=request.get("initial_capital", 10000),
            position_size=request.get("position_size", 0.1),
            stop_loss=request.get("stop_loss"),
            take_profit=request.get("take_profit"),
            strategy_params=request.get("strategy_params", {}),
        )
        return {
            "backtest_id": result.backtest_id,
            "status": result.status,
            "estimated_duration_seconds": 10,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Backtest error: {str(e)}")


@router.get("/backtest/results/{backtest_id}")
async def backtest_results(backtest_id: str):
    """Get backtest results."""
    result = get_backtest_result(backtest_id)
    if not result:
        raise HTTPException(status_code=404, detail="Backtest not found")

    return {
        "backtest_id": result.backtest_id,
        "status": result.status,
        "strategy": result.strategy,
        "symbol": result.symbol,
        "timeframe": result.timeframe,
        "summary": {
            "total_return": round(result.summary.total_return, 2),
            "total_return_percent": round(result.summary.total_return_percent, 2),
            "sharpe_ratio": round(result.summary.sharpe_ratio, 3),
            "max_drawdown": round(result.summary.max_drawdown, 2),
            "max_drawdown_percent": round(result.summary.max_drawdown_percent, 2),
            "win_rate": round(result.summary.win_rate, 3),
            "total_trades": result.summary.total_trades,
            "winning_trades": result.summary.winning_trades,
            "losing_trades": result.summary.losing_trades,
            "average_win": round(result.summary.average_win, 2),
            "average_loss": round(result.summary.average_loss, 2),
            "profit_factor": round(result.summary.profit_factor, 3),
        },
        "equity_curve": result.equity_curve,
        "trades": [
            {
                "entry_time": t.entry_time.isoformat() if t.entry_time else None,
                "exit_time": t.exit_time.isoformat() if t.exit_time else None,
                "direction": t.direction.value,
                "entry_price": t.entry_price,
                "exit_price": t.exit_price,
                "quantity": t.quantity,
                "pnl": round(t.pnl, 2),
                "pnl_percent": round(t.pnl_percent, 2),
            }
            for t in result.trades
        ],
        "duration_seconds": result.duration_seconds,
    }


@router.get("/backtest/list")
async def backtest_list():
    """List all backtest runs."""
    runs = list_backtests()
    return [
        {
            "backtest_id": r.backtest_id,
            "status": r.status,
            "strategy": r.strategy,
            "symbol": r.symbol,
        }
        for r in runs
    ]


# ─── Risk Management ───────────────────────────────────────

@router.get("/risk/assessment")
async def risk_assessment(
    symbol: str = Query(...),
    position_size: float = Query(...),
):
    """Get risk assessment for a position."""
    try:
        result = await assess_risk(symbol, position_size)
        return {
            "symbol": result.symbol,
            "position_size": result.position_size,
            "risk_level": result.risk_level.value,
            "risk_score": result.risk_score,
            "metrics": result.metrics,
            "warnings": result.warnings,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Risk assessment error: {str(e)}")


@router.get("/risk/limits")
async def risk_limits_get():
    """Get current risk limits."""
    limits = get_risk_limits()
    return {
        "max_position_size": limits.max_position_size,
        "max_daily_loss": limits.max_daily_loss,
        "max_drawdown": limits.max_drawdown,
        "max_leverage": limits.max_leverage,
        "max_open_positions": limits.max_open_positions,
    }


@router.post("/risk/limits")
async def risk_limits_post(request: dict):
    """Set risk limits."""
    limits = set_risk_limits(
        max_position_size=request.get("max_position_size"),
        max_daily_loss=request.get("max_daily_loss"),
        max_drawdown=request.get("max_drawdown"),
        max_leverage=request.get("max_leverage"),
        max_open_positions=request.get("max_open_positions"),
    )
    return {
        "limits_set": True,
        "active_limits": {
            "max_position_size": limits.max_position_size,
            "max_daily_loss": limits.max_daily_loss,
            "max_drawdown": limits.max_drawdown,
            "max_leverage": limits.max_leverage,
            "max_open_positions": limits.max_open_positions,
        },
    }


@router.post("/risk/position-size")
async def risk_position_size(request: dict):
    """Calculate position size based on risk parameters."""
    size = calculate_position_size(
        capital=request["capital"],
        risk_percent=request.get("risk_percent", 2.0),
        entry_price=request["entry_price"],
        stop_loss_price=request["stop_loss_price"],
    )
    return {"position_size": round(size, 6)}


@router.post("/risk/stop-loss")
async def risk_stop_loss(request: dict):
    """Calculate stop loss price."""
    price = calculate_stop_loss(
        entry_price=request["entry_price"],
        direction=request.get("direction", "long"),
        atr_value=request["atr_value"],
        multiplier=request.get("multiplier", 2.0),
    )
    return {"stop_loss_price": round(price, 6)}


@router.post("/risk/take-profit")
async def risk_take_profit(request: dict):
    """Calculate take profit price."""
    price = calculate_take_profit(
        entry_price=request["entry_price"],
        direction=request.get("direction", "long"),
        atr_value=request["atr_value"],
        multiplier=request.get("multiplier", 3.0),
    )
    return {"take_profit_price": round(price, 6)}


# ─── Portfolio ─────────────────────────────────────────────

@router.get("/portfolio")
async def portfolio_get():
    """Get current portfolio."""
    try:
        portfolio = await get_portfolio()
        return {
            "total_value": round(portfolio.total_value, 2),
            "cash": round(portfolio.cash, 2),
            "invested": round(portfolio.invested, 2),
            "pnl_today": round(portfolio.pnl_today, 2),
            "pnl_total": round(portfolio.pnl_total, 2),
            "positions": [
                {
                    "symbol": p.symbol,
                    "quantity": p.quantity,
                    "average_entry": p.average_entry,
                    "current_price": p.current_price,
                    "pnl": round(p.pnl, 2),
                    "pnl_percent": round(p.pnl_percent, 2),
                    "value": round(p.value, 2),
                    "direction": p.direction.value,
                }
                for p in portfolio.positions
            ],
            "updated_at": portfolio.updated_at.isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Portfolio error: {str(e)}")


@router.post("/portfolio/position")
async def portfolio_add_position(request: dict):
    """Add a position to the portfolio."""
    try:
        direction = PositionDirection(request.get("direction", "long"))
        position = await add_position(
            symbol=request["symbol"],
            quantity=request["quantity"],
            entry_price=request["entry_price"],
            direction=direction,
        )
        return {
            "symbol": position.symbol,
            "quantity": position.quantity,
            "average_entry": position.average_entry,
            "direction": position.direction.value,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Add position error: {str(e)}")


@router.delete("/portfolio/position/{symbol}")
async def portfolio_close_position(
    symbol: str,
    direction: str = Query(default="long"),
):
    """Close a position."""
    try:
        pnl = await close_position(symbol, PositionDirection(direction))
        return {"symbol": symbol, "pnl": round(pnl, 2), "closed": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Close position error: {str(e)}")


@router.post("/portfolio/reset")
async def portfolio_reset(initial_cash: float = 10000):
    """Reset portfolio."""
    portfolio = await reset_portfolio(initial_cash)
    return {"cash": portfolio.cash, "reset": True}


# ══════════════════════════════════════════════════════════════
# ENHANCED TRADING AGENT (EA) ENDPOINTS
# ══════════════════════════════════════════════════════════════

# ─── Strategy Engine ─────────────────────────────────────────

@router.post("/ea/strategies/analyze")
async def ea_strategies_analyze(request: dict):
    """Run multi-strategy analysis on a symbol."""
    try:
        result = await run_all_strategies(
            symbol=request["symbol"],
            timeframe=request.get("timeframe", "1h"),
            limit=request.get("limit", 200),
        )
        return {
            "symbol": result.symbol,
            "timeframe": result.timeframe,
            "signal": result.signal.value,
            "confidence": round(result.confidence, 3),
            "consensus": result.consensus,
            "buy_score": round(result.buy_score, 3),
            "sell_score": round(result.sell_score, 3),
            "hold_score": round(result.hold_score, 3),
            "strategies": [
                {
                    "strategy": s.strategy.value,
                    "signal": s.signal.value,
                    "confidence": round(s.confidence, 3),
                    "weight": s.weight,
                    "details": s.details,
                }
                for s in result.strategy_signals
            ],
            "timestamp": result.timestamp.isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Strategy analysis error: {str(e)}")


# ─── Signal Generator ────────────────────────────────────────

@router.get("/ea/signal")
async def ea_signal(
    symbol: str = Query(...),
    timeframe: str = Query(default="1h"),
    capital: float = Query(default=10000),
    risk_percent: float = Query(default=2.0),
):
    """Generate a complete trading signal with entry/exit levels."""
    try:
        rec = await generate_signal(
            symbol=symbol,
            timeframe=timeframe,
            capital=capital,
            risk_percent=risk_percent,
        )
        return rec.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Signal generation error: {str(e)}")


@router.post("/ea/scan")
async def ea_scan(request: dict):
    """Scan watchlist for trading opportunities."""
    try:
        config = WatchlistConfig(
            symbols=request.get("symbols", ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT"]),
            timeframes=request.get("timeframes", ["1h"]),
            min_confidence=request.get("min_confidence", 0.5),
            strategies=request.get("strategies"),
        )
        results = await scan_watchlist(
            config=config,
            capital=request.get("capital", 10000),
            risk_percent=request.get("risk_percent", 2.0),
        )
        return {
            "opportunities": [r.to_dict() for r in results],
            "count": len(results),
            "scanned_at": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scan error: {str(e)}")


@router.get("/ea/signal-history")
async def ea_signal_history(
    symbol: str = Query(...),
    timeframe: str = Query(default="1h"),
    limit: int = Query(default=20, le=100),
):
    """Get signal history for a symbol."""
    history = get_signal_history(symbol, timeframe, limit)
    return {"symbol": symbol, "timeframe": timeframe, "history": history}


# ─── Auto Executor (Paper Trading) ──────────────────────────

@router.get("/ea/executor/status")
async def ea_executor_status():
    """Get auto executor status."""
    state = get_state()
    return {
        "running": state.running,
        "capital": round(state.capital, 2),
        "initial_capital": state.initial_capital,
        "total_pnl": round(state.total_pnl, 2),
        "daily_pnl": round(state.daily_pnl, 2),
        "daily_trades": state.daily_trades,
        "open_positions": len(state.open_orders),
        "win_count": state.win_count,
        "loss_count": state.loss_count,
        "last_scan": state.last_scan,
        "last_signal": state.last_signal,
        "config": {
            "risk_percent": state.risk_percent,
            "max_open_positions": state.max_open_positions,
            "max_daily_trades": state.max_daily_trades,
            "min_confidence": state.min_confidence,
            "min_risk_reward": state.min_risk_reward,
            "watchlist": state.watchlist,
            "timeframe": state.timeframe,
            "strategies": state.strategies,
        },
    }


@router.post("/ea/executor/configure")
async def ea_executor_configure(request: dict):
    """Configure the auto executor."""
    state = update_state(
        risk_percent=request.get("risk_percent", 2.0),
        max_open_positions=request.get("max_open_positions", 3),
        max_daily_trades=request.get("max_daily_trades", 10),
        min_confidence=request.get("min_confidence", 0.5),
        min_risk_reward=request.get("min_risk_reward", 1.5),
        watchlist=request.get("watchlist", ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT"]),
        timeframe=request.get("timeframe", "1h"),
        strategies=request.get("strategies", [
            "sma_crossover", "rsi_mean_reversion", "macd_momentum",
            "bollinger_breakout", "stochastic_rsi", "atr_trend",
        ]),
    )
    return {"configured": True, "state": get_performance_stats()}


@router.post("/ea/executor/start")
async def ea_executor_start():
    """Start the auto executor (runs one scan cycle)."""
    try:
        executed = await run_scan_cycle()
        return {
            "executed": len(executed),
            "orders": [o.to_dict() for o in executed],
            "stats": get_performance_stats(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Executor start error: {str(e)}")


@router.post("/ea/executor/stop")
async def ea_executor_stop():
    """Stop the auto executor."""
    update_state(running=False)
    return {"stopped": True}


@router.post("/ea/executor/reset")
async def ea_executor_reset(initial_cash: float = 10000):
    """Reset the auto executor state."""
    state = reset_state(initial_cash)
    return {"reset": True, "capital": state.capital}


@router.get("/ea/executor/positions")
async def ea_executor_positions():
    """Get open positions."""
    positions = get_open_positions()
    return {"positions": positions, "count": len(positions)}


@router.get("/ea/executor/history")
async def ea_executor_history(limit: int = 50):
    """Get trade history."""
    history = get_trade_history(limit)
    return {"trades": history, "count": len(history)}


@router.post("/ea/executor/close/{order_id}")
async def ea_executor_close(order_id: str):
    """Close a position manually."""
    result = await close_executor_position(order_id)
    if not result:
        raise HTTPException(status_code=404, detail="Position not found")
    return {"closed": True, "pnl": result.get("pnl", 0)}


@router.get("/ea/executor/performance")
async def ea_executor_performance():
    """Get performance statistics."""
    return get_performance_stats()


# ─── Trading Agent (High-Level) ──────────────────────────────

@router.get("/ea/agent/status")
async def ea_agent_status():
    """Get trading agent status."""
    agent = get_agent()
    return agent.status()


@router.post("/ea/agent/analyze")
async def ea_agent_analyze(request: dict):
    """Analyze a symbol using the trading agent."""
    try:
        agent = get_agent()
        rec = await agent.analyze(
            symbol=request["symbol"],
            timeframe=request.get("timeframe", "1h"),
        )
        return rec.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis error: {str(e)}")


@router.post("/ea/agent/scan")
async def ea_agent_scan(request: dict):
    """Scan for opportunities using the trading agent."""
    try:
        agent = get_agent()
        results = await agent.scan(
            symbols=request.get("symbols"),
            min_confidence=request.get("min_confidence"),
        )
        return {
            "opportunities": [r.to_dict() for r in results],
            "count": len(results),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scan error: {str(e)}")
