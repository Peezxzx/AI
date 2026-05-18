"""
Risk Management - Position sizing, risk assessment, limits
"""
import math
from .models import RiskAssessment, RiskLevel, RiskLimits
from .market_data import get_klines, get_ticker
from .analysis import calculate_atr, calculate_rsi

# Default risk limits
_default_limits = RiskLimits()


def get_risk_limits() -> RiskLimits:
    """Get current risk limits."""
    return _default_limits


def set_risk_limits(
    max_position_size: float | None = None,
    max_daily_loss: float | None = None,
    max_drawdown: float | None = None,
    max_leverage: float | None = None,
    max_open_positions: int | None = None,
) -> RiskLimits:
    """Set risk limits."""
    global _default_limits
    if max_position_size is not None:
        _default_limits.max_position_size = max_position_size
    if max_daily_loss is not None:
        _default_limits.max_daily_loss = max_daily_loss
    if max_drawdown is not None:
        _default_limits.max_drawdown = max_drawdown
    if max_leverage is not None:
        _default_limits.max_leverage = max_leverage
    if max_open_positions is not None:
        _default_limits.max_open_positions = max_open_positions
    return _default_limits


async def assess_risk(symbol: str, position_size: float) -> RiskAssessment:
    """Assess risk for a potential position."""
    assessment = RiskAssessment(symbol=symbol, position_size=position_size)
    warnings = []

    # Fetch data
    candles = await get_klines(symbol, "1d", limit=30)
    ticker = await get_ticker(symbol)

    if not candles or not ticker:
        assessment.risk_level = RiskLevel.HIGH
        assessment.risk_score = 0.8
        warnings.append("Unable to fetch market data for risk assessment")
        assessment.warnings = warnings
        return assessment

    closes = [c.close for c in candles]

    # Volatility (30-day annualized)
    returns = [(closes[i] / closes[i - 1]) - 1 for i in range(1, len(closes))]
    if returns:
        avg_return = sum(returns) / len(returns)
        variance = sum((r - avg_return) ** 2 for r in returns) / len(returns)
        daily_vol = math.sqrt(variance)
        annual_vol = daily_vol * math.sqrt(365)
        assessment.metrics["volatility_30d"] = round(annual_vol * 100, 2)
    else:
        annual_vol = 0.0
        assessment.metrics["volatility_30d"] = 0.0

    # VaR (95%) - Value at Risk
    if returns:
        sorted_returns = sorted(returns)
        var_index = int(len(sorted_returns) * 0.05)
        var_95 = abs(sorted_returns[var_index]) * position_size
        assessment.metrics["var_95"] = round(var_95, 2)
    else:
        assessment.metrics["var_95"] = 0.0

    # ATR-based position sizing
    atr_values = calculate_atr(candles, period=14)
    if atr_values:
        current_atr = atr_values[-1]
        assessment.metrics["atr_14"] = round(current_atr, 6)

        # Recommended position size based on 2% risk rule
        risk_per_unit = current_atr * 2
        if risk_per_unit > 0:
            max_risk_amount = position_size * 0.02
            recommended_size = max_risk_amount / risk_per_unit * ticker.last_price
            assessment.metrics["max_position_size"] = round(recommended_size, 2)
        else:
            assessment.metrics["max_position_size"] = position_size
    else:
        assessment.metrics["atr_14"] = 0.0
        assessment.metrics["max_position_size"] = position_size

    # Recommended leverage
    if annual_vol > 0:
        rec_leverage = min(5.0, max(1.0, 0.5 / annual_vol))
        assessment.metrics["recommended_leverage"] = round(rec_leverage, 1)
    else:
        assessment.metrics["recommended_leverage"] = 1.0

    # RSI check
    rsi_values = calculate_rsi(closes, 14)
    if rsi_values:
        last_rsi = rsi_values[-1]
        assessment.metrics["rsi_14"] = round(last_rsi, 2)
        if last_rsi > 80:
            warnings.append("RSI indicates extremely overbought conditions")
        elif last_rsi < 20:
            warnings.append("RSI indicates extremely oversold conditions")

    # Calculate risk score (0-1)
    risk_score = 0.0

    # Volatility contribution (0-0.4)
    vol_score = min(0.4, annual_vol * 2)
    risk_score += vol_score

    # VaR contribution (0-0.3)
    var_ratio = assessment.metrics["var_95"] / position_size if position_size > 0 else 0
    var_score = min(0.3, var_ratio * 10)
    risk_score += var_score

    # Position size vs limit (0-0.3)
    size_ratio = position_size / _default_limits.max_position_size if _default_limits.max_position_size > 0 else 0
    size_score = min(0.3, size_ratio * 0.3)
    risk_score += size_score

    assessment.risk_score = round(min(1.0, risk_score), 3)

    # Determine risk level
    if assessment.risk_score < 0.25:
        assessment.risk_level = RiskLevel.LOW
    elif assessment.risk_score < 0.5:
        assessment.risk_level = RiskLevel.MEDIUM
    elif assessment.risk_score < 0.75:
        assessment.risk_level = RiskLevel.HIGH
    else:
        assessment.risk_level = RiskLevel.EXTREME

    # Additional warnings
    if position_size > _default_limits.max_position_size:
        warnings.append(f"Position size ({position_size}) exceeds max ({_default_limits.max_position_size})")

    if annual_vol > 1.0:
        warnings.append("Extreme volatility detected (>100% annualized)")

    if ticker.change_percent_24h > 10:
        warnings.append(f"Large 24h price increase: +{ticker.change_percent_24h}%")
    elif ticker.change_percent_24h < -10:
        warnings.append(f"Large 24h price decrease: {ticker.change_percent_24h}%")

    assessment.warnings = warnings
    return assessment


def calculate_position_size(
    capital: float,
    risk_percent: float,
    entry_price: float,
    stop_loss_price: float,
) -> float:
    """Calculate position size based on risk parameters."""
    if entry_price <= 0 or stop_loss_price <= 0:
        return 0.0

    risk_amount = capital * (risk_percent / 100)
    risk_per_unit = abs(entry_price - stop_loss_price)

    if risk_per_unit <= 0:
        return 0.0

    return risk_amount / risk_per_unit


def calculate_stop_loss(
    entry_price: float,
    direction: str,
    atr_value: float,
    multiplier: float = 2.0,
) -> float:
    """Calculate stop loss price based on ATR."""
    if direction == "long":
        return entry_price - (atr_value * multiplier)
    else:
        return entry_price + (atr_value * multiplier)


def calculate_take_profit(
    entry_price: float,
    direction: str,
    atr_value: float,
    multiplier: float = 3.0,
) -> float:
    """Calculate take profit price based on ATR."""
    if direction == "long":
        return entry_price + (atr_value * multiplier)
    else:
        return entry_price - (atr_value * multiplier)
