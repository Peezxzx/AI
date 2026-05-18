# TRADING AI INFRASTRUCTURE CONTRACTS

## Interface Definitions for Trading System

---

## 1. Market Data Contract

### Get Market Data
```
GET /trading/market/data?symbol={symbol}&timeframe={tf}&limit={n}
Response:
{
    "symbol": string,
    "timeframe": "1m" | "5m" | "15m" | "1h" | "4h" | "1d",
    "data": [
        {
            "timestamp": ISO8601 timestamp,
            "open": float,
            "high": float,
            "low": float,
            "close": float,
            "volume": float
        }
    ],
    "source": string,
    "cached": boolean
}
```

### Get Order Book
```
GET /trading/market/orderbook?symbol={symbol}&depth={n}
Response:
{
    "symbol": string,
    "bids": [{"price": float, "quantity": float}],
    "asks": [{"price": float, "quantity": float}],
    "spread": float,
    "timestamp": ISO8601 timestamp
}
```

### Get Ticker
```
GET /trading/market/ticker?symbol={symbol}
Response:
{
    "symbol": string,
    "last_price": float,
    "bid": float,
    "ask": float,
    "high_24h": float,
    "low_24h": float,
    "volume_24h": float,
    "change_24h": float,
    "change_percent_24h": float,
    "timestamp": ISO8601 timestamp
}
```

---

## 2. Technical Analysis Contract

### Get Indicators
```
POST /trading/analysis/indicators
Request:
{
    "symbol": string,
    "timeframe": string,
    "indicators": ["sma" | "ema" | "rsi" | "macd" | "bollinger" | "atr" | "stochastic"],
    "period": int (default: 14),
    "limit": int (default: 100)
}
Response:
{
    "symbol": string,
    "timeframe": string,
    "indicators": {
        "sma": [{"timestamp": ISO8601, "value": float}],
        "rsi": [{"timestamp": ISO8601, "value": float}],
        "macd": [{"timestamp": ISO8601, "macd": float, "signal": float, "histogram": float}]
    },
    "calculated_at": ISO8601 timestamp
}
```

### Get Signal
```
GET /trading/analysis/signal?symbol={symbol}&timeframe={tf}
Response:
{
    "symbol": string,
    "timeframe": string,
    "signal": "buy" | "sell" | "hold",
    "confidence": float (0.0 - 1.0),
    "indicators_summary": {
        "rsi": {"value": float, "signal": string},
        "macd": {"value": float, "signal": string},
        "sma_cross": {"value": string, "signal": string}
    },
    "generated_at": ISO8601 timestamp
}
```

---

## 3. Backtesting Contract

### Run Backtest
```
POST /trading/backtest/run
Request:
{
    "strategy": string,
    "symbol": string,
    "timeframe": string,
    "start_date": ISO8601 timestamp,
    "end_date": ISO8601 timestamp,
    "initial_capital": float,
    "position_size": float (percentage, 0.0 - 1.0),
    "stop_loss": float (optional),
    "take_profit": float (optional),
    "strategy_params": object
}
Response:
{
    "backtest_id": string,
    "status": "started",
    "estimated_duration_seconds": int
}
```

### Get Backtest Results
```
GET /trading/backtest/results/{backtest_id}
Response:
{
    "backtest_id": string,
    "status": "running" | "completed" | "failed",
    "summary": {
        "total_return": float,
        "total_return_percent": float,
        "sharpe_ratio": float,
        "max_drawdown": float,
        "max_drawdown_percent": float,
        "win_rate": float,
        "total_trades": int,
        "winning_trades": int,
        "losing_trades": int,
        "average_win": float,
        "average_loss": float,
        "profit_factor": float
    },
    "equity_curve": [{"timestamp": ISO8601, "value": float}],
    "trades": [
        {
            "entry_time": ISO8601 timestamp,
            "exit_time": ISO8601 timestamp,
            "direction": "long" | "short",
            "entry_price": float,
            "exit_price": float,
            "quantity": float,
            "pnl": float,
            "pnl_percent": float
        }
    ],
    "duration_seconds": float
}
```

---

## 4. Risk Management Contract

### Get Risk Assessment
```
GET /trading/risk/assessment?symbol={symbol}&position_size={size}
Response:
{
    "symbol": string,
    "position_size": float,
    "risk_level": "low" | "medium" | "high" | "extreme",
    "risk_score": float (0.0 - 1.0),
    "metrics": {
        "volatility_30d": float,
        "var_95": float,
        "max_position_size": float,
        "recommended_leverage": float
    },
    "warnings": string[]
}
```

### Set Risk Limits
```
POST /trading/risk/limits
Request:
{
    "max_position_size": float,
    "max_daily_loss": float,
    "max_drawdown": float,
    "max_leverage": float,
    "max_open_positions": int
}
Response:
{
    "limits_set": boolean,
    "active_limits": object
}
```

---

## 5. Portfolio Contract

### Get Portfolio
```
GET /trading/portfolio
Response:
{
    "total_value": float,
    "cash": float,
    "invested": float,
    "pnl_today": float,
    "pnl_total": float,
    "positions": [
        {
            "symbol": string,
            "quantity": float,
            "average_entry": float,
            "current_price": float,
            "pnl": float,
            "pnl_percent": float,
            "value": float
        }
    ],
    "updated_at": ISO8601 timestamp
}
```

---

## Error Codes

| Code | Meaning |
|------|---------|
| 6001 | Market data unavailable |
| 6002 | Invalid symbol |
| 6003 | Backtest failed |
| 6004 | Risk limit exceeded |
| 6005 | Insufficient capital |
| 6006 | Strategy not found |
| 6007 | Order rejected |
| 6008 | Exchange API error |
| 6009 | Rate limit exceeded |
| 6010 | Data feed disconnected |
