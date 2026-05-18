"""
Market Data Provider - Fetches data from Binance public API
No API key required for public endpoints.
"""
import asyncio
import json
from datetime import datetime
from pathlib import Path
from .models import Candle, Ticker, OrderBook

# Cache directory
CACHE_DIR = Path("/tmp/atsawin_trading_cache")
CACHE_DIR.mkdir(exist_ok=True)

# Binance public API base
BINANCE_API = "https://api.binance.com/api/v3"

# Timeframe mapping
TIMEFRAME_MAP = {
    "1m": "1m",
    "5m": "5m",
    "15m": "15m",
    "1h": "1h",
    "4h": "4h",
    "1d": "1d",
}


async def _http_get(url: str) -> dict | list:
    """Make an async HTTP GET request using curl."""
    proc = await asyncio.create_subprocess_exec(
        "curl", "-s", "--max-time", "15", url,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=20)
    if proc.returncode != 0:
        raise ConnectionError(f"HTTP request failed: {stderr.decode()}")
    return json.loads(stdout.decode("utf-8"))


def _cache_path(symbol: str, timeframe: str, suffix: str = "klines") -> Path:
    """Get cache file path."""
    safe = f"{symbol}_{timeframe}_{suffix}".replace("/", "_")
    return CACHE_DIR / f"{safe}.json"


def _load_cache(path: Path, max_age_seconds: int = 60) -> dict | list | None:
    """Load cached data if not expired."""
    if not path.exists():
        return None
    age = datetime.utcnow().timestamp() - path.stat().st_mtime
    if age > max_age_seconds:
        return None
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return None


def _save_cache(path: Path, data):
    """Save data to cache."""
    try:
        path.write_text(json.dumps(data))
    except OSError:
        pass


async def get_klines(
    symbol: str,
    timeframe: str = "1h",
    limit: int = 100,
    use_cache: bool = True,
) -> list[Candle]:
    """Fetch kline/candlestick data from Binance."""
    tf = TIMEFRAME_MAP.get(timeframe, timeframe)
    cache = _cache_path(symbol, tf, "klines")

    if use_cache:
        cached = _load_cache(cache, max_age_seconds=60)
        if cached:
            return _parse_klines(cached[:limit])

    url = f"{BINANCE_API}/klines?symbol={symbol.upper()}&interval={tf}&limit={limit}"
    data = await _http_get(url)
    _save_cache(cache, data)
    return _parse_klines(data)


def _parse_klines(raw: list) -> list[Candle]:
    """Parse Binance kline response into Candle objects."""
    candles = []
    for k in raw:
        # Binance kline format:
        # [open_time, open, high, low, close, volume, close_time, ...]
        candles.append(Candle(
            timestamp=datetime.utcfromtimestamp(k[0] / 1000),
            open=float(k[1]),
            high=float(k[2]),
            low=float(k[3]),
            close=float(k[4]),
            volume=float(k[5]),
        ))
    return candles


async def get_ticker(symbol: str) -> Ticker:
    """Fetch 24h ticker data from Binance."""
    cache = _cache_path(symbol, "ticker")
    cached = _load_cache(cache, max_age_seconds=30)
    if cached:
        return _parse_ticker(cached)

    url = f"{BINANCE_API}/ticker/24hr?symbol={symbol.upper()}"
    data = await _http_get(url)
    _save_cache(cache, data)
    return _parse_ticker(data)


def _parse_ticker(data: dict) -> Ticker:
    """Parse Binance ticker response."""
    return Ticker(
        symbol=data["symbol"],
        last_price=float(data["lastPrice"]),
        bid=float(data["bidPrice"]),
        ask=float(data["askPrice"]),
        high_24h=float(data["highPrice"]),
        low_24h=float(data["lowPrice"]),
        volume_24h=float(data["volume"]),
        change_24h=float(data["priceChange"]),
        change_percent_24h=float(data["priceChangePercent"]),
        timestamp=datetime.utcnow(),
    )


async def get_order_book(symbol: str, depth: int = 20) -> OrderBook:
    """Fetch order book from Binance."""
    url = f"{BINANCE_API}/depth?symbol={symbol.upper()}&limit={depth}"
    data = await _http_get(url)

    bids = [{"price": float(p), "quantity": float(q)} for p, q in data.get("bids", [])]
    asks = [{"price": float(p), "quantity": float(q)} for p, q in data.get("asks", [])]

    spread = 0.0
    if bids and asks:
        spread = asks[0]["price"] - bids[0]["price"]

    return OrderBook(
        symbol=symbol.upper(),
        bids=bids,
        asks=asks,
        spread=spread,
        timestamp=datetime.utcnow(),
    )


async def get_available_symbols() -> list[str]:
    """Fetch available trading symbols from Binance."""
    cache = _cache_dir = CACHE_DIR / "symbols.json"
    cached = _load_cache(cache, max_age_seconds=3600)
    if cached:
        return cached

    url = f"{BINANCE_API}/exchangeInfo"
    data = await _http_get(url)
    symbols = [
        s["symbol"] for s in data.get("symbols", [])
        if s.get("status") == "TRADING" and s.get("quoteAsset") == "USDT"
    ]
    symbols.sort()
    _save_cache(cache, symbols)
    return symbols


async def get_current_price(symbol: str) -> float:
    """Get current price for a symbol."""
    url = f"{BINANCE_API}/ticker/price?symbol={symbol.upper()}"
    data = await _http_get(url)
    return float(data["price"])
