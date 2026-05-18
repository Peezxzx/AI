"""
Trading AI Infrastructure - Data Models
"""
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
from datetime import datetime


class Signal(str, Enum):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EXTREME = "extreme"


class OrderSide(str, Enum):
    BUY = "buy"
    SELL = "sell"


class OrderType(str, Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"


class PositionDirection(str, Enum):
    LONG = "long"
    SHORT = "short"


@dataclass
class Candle:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass
class Ticker:
    symbol: str
    last_price: float
    bid: float
    ask: float
    high_24h: float
    low_24h: float
    volume_24h: float
    change_24h: float
    change_percent_24h: float
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class OrderBook:
    symbol: str
    bids: list[dict] = field(default_factory=list)  # [{"price": float, "quantity": float}]
    asks: list[dict] = field(default_factory=list)
    spread: float = 0.0
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class IndicatorValue:
    timestamp: datetime
    value: float


@dataclass
class MACDValue:
    timestamp: datetime
    macd: float
    signal: float
    histogram: float


@dataclass
class BollingerValue:
    timestamp: datetime
    upper: float
    middle: float
    lower: float


@dataclass
class IndicatorResult:
    symbol: str
    timeframe: str
    sma: list[IndicatorValue] = field(default_factory=list)
    ema: list[IndicatorValue] = field(default_factory=list)
    rsi: list[IndicatorValue] = field(default_factory=list)
    macd: list[MACDValue] = field(default_factory=list)
    bollinger: list[BollingerValue] = field(default_factory=list)
    atr: list[IndicatorValue] = field(default_factory=list)
    stochastic: list[IndicatorValue] = field(default_factory=list)
    calculated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class TradingSignal:
    symbol: str
    timeframe: str
    signal: Signal = Signal.HOLD
    confidence: float = 0.0
    indicators_summary: dict = field(default_factory=dict)
    generated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Trade:
    entry_time: datetime
    exit_time: Optional[datetime] = None
    direction: PositionDirection = PositionDirection.LONG
    entry_price: float = 0.0
    exit_price: float = 0.0
    quantity: float = 0.0
    pnl: float = 0.0
    pnl_percent: float = 0.0
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None


@dataclass
class BacktestSummary:
    total_return: float = 0.0
    total_return_percent: float = 0.0
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0
    max_drawdown_percent: float = 0.0
    win_rate: float = 0.0
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    average_win: float = 0.0
    average_loss: float = 0.0
    profit_factor: float = 0.0


@dataclass
class BacktestResult:
    backtest_id: str = ""
    status: str = "started"
    strategy: str = ""
    symbol: str = ""
    timeframe: str = ""
    summary: BacktestSummary = field(default_factory=BacktestSummary)
    equity_curve: list[dict] = field(default_factory=list)
    trades: list[Trade] = field(default_factory=list)
    duration_seconds: float = 0.0


@dataclass
class RiskAssessment:
    symbol: str
    position_size: float
    risk_level: RiskLevel = RiskLevel.MEDIUM
    risk_score: float = 0.5
    metrics: dict = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)


@dataclass
class RiskLimits:
    max_position_size: float = 10000.0
    max_daily_loss: float = 500.0
    max_drawdown: float = 0.2
    max_leverage: float = 1.0
    max_open_positions: int = 5


@dataclass
class Position:
    symbol: str
    quantity: float
    average_entry: float
    current_price: float
    pnl: float
    pnl_percent: float
    value: float
    direction: PositionDirection = PositionDirection.LONG
    opened_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Portfolio:
    total_value: float = 0.0
    cash: float = 0.0
    invested: float = 0.0
    pnl_today: float = 0.0
    pnl_total: float = 0.0
    positions: list[Position] = field(default_factory=list)
    updated_at: datetime = field(default_factory=datetime.utcnow)
