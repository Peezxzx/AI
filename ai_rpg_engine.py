#!/usr/bin/env python3
"""
AI_RPG Trading Engine v2 — Python Edition
แกะ logic จาก AI_RPG.mq5 v4 + mt5_bridge.py มารวมกัน
รันบน Python ได้เลย ไม่ต้องมี MT5

โหมด:
  1. SIMULATION — backtest/paper trade ด้วยข้อมูลจำลอง
  2. BRIDGE — เชื่อมต่อกับ FastAPI backend สำหรับรับ signal
  3. HYBRID — ใช้ข้อมูลจริงจาก Binance + signal จาก backend

Usage:
  python ai_rpg_engine.py --mode simulation
  python ai_rpg_engine.py --mode bridge --api-url http://localhost:8000 --api-key YOUR_KEY
  python ai_rpg_engine.py --mode hybrid --api-url http://localhost:8000 --api-key YOUR_KEY
"""

import asyncio
import json
import logging
import argparse
import os
import sys
import time
from datetime import datetime, timezone
from dataclasses import dataclass, field, asdict
from typing import Optional
from pathlib import Path
from enum import Enum

# ══════════════════════════════════════════════════════════════
# CONFIG
# ══════════════════════════════════════════════════════════════

DEFAULT_CONFIG = {
    # --- Mode ---
    "mode": "simulation",          # simulation | bridge | hybrid
    "symbol": "BTCUSDT",
    "timeframe": "1h",             # 1m 5m 15m 1h 4h 1d

    # --- API ---
    "api_url": "http://185.84.160.106",
    "api_key": "mt5bridge2024",

    # --- Risk ---
    "risk_percent": 2.0,
    "max_lot": 1.0,
    "min_lot": 0.01,
    "max_spread_pct": 0.005,       # 0.5%
    "max_open_trades": 3,
    "min_confidence": 0.3,
    "signal_expiry_min": 60,
    "initial_balance": 10000.0,

    # --- Bridge ---
    "signal_file": "latest_signal.json",
    "status_file": "ea_status.json",
    "log_file": "ai_rpg_engine.log",
    "poll_interval": 10,           # seconds

    # --- Simulation ---
    "sim_speed": 1.0,              # 1.0 = realtime, 10.0 = 10x faster
    "sim_data_file": None,         # CSV file with OHLCV data (optional)
}


# ══════════════════════════════════════════════════════════════
# DATA STRUCTURES
# ══════════════════════════════════════════════════════════════

class TradeStatus(Enum):
    OPEN = "open"
    CLOSED = "closed"
    FAILED = "failed"

class SignalDirection(Enum):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"

@dataclass
class Candle:
    time: int
    open: float
    high: float
    low: float
    close: float
    volume: int

@dataclass
class Signal:
    direction: SignalDirection = SignalDirection.HOLD
    confidence: float = 0.0
    entry_price: float = 0.0
    stop_loss: float = 0.0
    take_profit: float = 0.0
    position_size: float = 0.0
    risk_reward_ratio: float = 0.0
    consensus: str = ""
    risk_level: str = "medium"
    timestamp: str = ""
    source: str = ""               # "api" | "file" | "simulation"
    valid: bool = False

@dataclass
class Trade:
    ticket: int = 0
    action: str = ""               # "buy" | "sell"
    lot: float = 0.0
    entry_price: float = 0.0
    sl: float = 0.0
    tp: float = 0.0
    close_price: float = 0.0
    pnl: float = 0.0
    status: TradeStatus = TradeStatus.FAILED
    open_time: str = ""
    close_time: str = ""
    source: str = ""

@dataclass
class Account:
    balance: float = 10000.0
    equity: float = 10000.0
    margin: float = 0.0
    free_margin: float = 10000.0
    profit: float = 0.0
    currency: str = "USD"

@dataclass
class EngineState:
    total_trades: int = 0
    total_pnl: float = 0.0
    daily_pnl: float = 0.0
    consecutive_errors: int = 0
    max_consecutive_errors: int = 5
    initialized: bool = False
    running: bool = False
    trades: list = field(default_factory=list)
    current_signal: Optional[Signal] = None
    account: Account = field(default_factory=Account)


# ══════════════════════════════════════════════════════════════
# LOGGING
# ══════════════════════════════════════════════════════════════

def setup_logging(log_file: str) -> logging.Logger:
    logger = logging.getLogger("AI_RPG")
    logger.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")

    logger.addHandler(logging.StreamHandler(sys.stdout))

    try:
        from logging.handlers import RotatingFileHandler
        logger.addHandler(RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=3))
    except:
        pass

    return logger


# ══════════════════════════════════════════════════════════════
# SIMULATION DATA GENERATOR
# ══════════════════════════════════════════════════════════════

class SimDataGenerator:
    """สร้างข้อมูล OHLCV จำลองสำหรับ backtest/simulation"""

    def __init__(self, symbol: str = "BTCUSDT", base_price: float = 100000.0):
        self.symbol = symbol
        self.base_price = base_price
        self.current_price = base_price
        self.tick_count = 0

    def generate_candles(self, count: int = 200) -> list:
        """สร้างแท่งเทียนจำลอง"""
        import random
        candles = []
        price = self.base_price

        for i in range(count):
            # Random walk with slight upward bias
            change = random.gauss(0.001, 0.005) * price
            open_p = price
            close_p = price + change
            high_p = max(open_p, close_p) + abs(random.gauss(0, 0.002) * price)
            low_p = min(open_p, close_p) - abs(random.gauss(0, 0.002) * price)
            volume = int(random.uniform(100, 10000))

            candles.append(Candle(
                time=int(time.time()) - (count - i) * 3600,
                open=round(open_p, 2),
                high=round(high_p, 2),
                low=round(low_p, 2),
                close=round(close_p, 2),
                volume=volume
            ))
            price = close_p

        self.current_price = price
        return candles

    def generate_signal(self) -> Signal:
        """สร้าง signal จำลอง"""
        import random
        rand = random.random()

        if rand < 0.3:
            direction = SignalDirection.BUY
            confidence = random.uniform(0.3, 0.9)
        elif rand < 0.6:
            direction = SignalDirection.SELL
            confidence = random.uniform(0.3, 0.9)
        else:
            direction = SignalDirection.HOLD
            confidence = random.uniform(0.1, 0.4)

        sl_pct = random.uniform(0.01, 0.03)
        tp_pct = random.uniform(0.02, 0.05)

        if direction == SignalDirection.BUY:
            sl = self.current_price * (1 - sl_pct)
            tp = self.current_price * (1 + tp_pct)
        elif direction == SignalDirection.SELL:
            sl = self.current_price * (1 + sl_pct)
            tp = self.current_price * (1 - tp_pct)
        else:
            sl = 0
            tp = 0

        return Signal(
            direction=direction,
            confidence=round(confidence, 3),
            entry_price=round(self.current_price, 2),
            stop_loss=round(sl, 2),
            take_profit=round(tp, 2),
            position_size=0.01,
            risk_reward_ratio=round(tp_pct / sl_pct, 2) if sl_pct > 0 else 0,
            consensus="strong_" + direction.value if confidence > 0.6 else "weak_" + direction.value,
            risk_level="low" if confidence > 0.7 else "medium" if confidence > 0.4 else "high",
            timestamp=datetime.now(timezone.utc).isoformat(),
            source="simulation",
            valid=(direction != SignalDirection.HOLD)
        )

    def tick(self):
        """อัพเดทราคา 1 tick"""
        import random
        self.current_price += random.gauss(0, 0.0001) * self.current_price
        self.tick_count += 1


# ══════════════════════════════════════════════════════════════
# BINANCE DATA PROVIDER (Real Data)
# ══════════════════════════════════════════════════════════════

class BinanceProvider:
    """ดึงข้อมูลจริงจาก Binance API"""

    BASE_URL = "https://api.binance.com"

    def __init__(self, symbol: str = "BTCUSDT", timeframe: str = "1h"):
        self.symbol = symbol
        self.timeframe = timeframe
        self.session = None

    async def init(self):
        try:
            import aiohttp
            self.session = aiohttp.ClientTimeout(total=30)
        except ImportError:
            pass

    async def get_candles(self, limit: int = 200) -> list:
        """ดึงข้อมูลแท่งเทียนจาก Binance"""
        try:
            import aiohttp
            url = f"{self.BASE_URL}/api/v3/klines"
            params = {"symbol": self.symbol, "interval": self.timeframe, "limit": limit}

            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=30)) as r:
                    if r.status == 200:
                        data = await r.json()
                        candles = []
                        for k in data:
                            candles.append(Candle(
                                time=int(k[0] / 1000),
                                open=float(k[1]),
                                high=float(k[2]),
                                low=float(k[3]),
                                close=float(k[4]),
                                volume=int(float(k[5]))
                            ))
                        return candles
        except Exception as e:
            logging.getLogger("AI_RPG").warning(f"Binance API error: {e}")
        return []

    async def get_price(self) -> float:
        """ดึงราคาปัจจุบัน"""
        try:
            import aiohttp
            url = f"{self.BASE_URL}/api/v3/ticker/price"
            params = {"symbol": self.symbol}
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as r:
                    if r.status == 200:
                        data = await r.json()
                        return float(data["price"])
        except:
            pass
        return 0.0


# ══════════════════════════════════════════════════════════════
# SIGNAL PROVIDERS
# ══════════════════════════════════════════════════════════════

class SignalProvider:
    """Base class สำหรับ signal providers"""

    async def get_signal(self) -> Signal:
        return Signal()


class APISignalProvider(SignalProvider):
    """รับ signal จาก FastAPI backend"""

    def __init__(self, api_url: str, api_key: str, symbol: str):
        self.api_url = api_url
        self.api_key = api_key
        self.symbol = symbol

    async def get_signal(self) -> Signal:
        try:
            import aiohttp
            url = f"{self.api_url}/api/mt5/signal?symbol={self.symbol}"
            headers = {"X-API-Key": self.api_key}

            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as r:
                    if r.status == 200:
                        data = await r.json()
                        if data.get("signal") and data["signal"] != "hold":
                            return Signal(
                                direction=SignalDirection(data["signal"]),
                                confidence=float(data.get("confidence", 0)),
                                entry_price=float(data.get("entry_price", 0)),
                                stop_loss=float(data.get("sl", 0)),
                                take_profit=float(data.get("tp", 0)),
                                position_size=float(data.get("lotSize", 0)),
                                risk_reward_ratio=float(data.get("risk_reward_ratio", 0)),
                                consensus=data.get("consensus", ""),
                                risk_level=data.get("risk_level", "medium"),
                                timestamp=data.get("timestamp", ""),
                                source="api",
                                valid=True
                            )
        except Exception as e:
            logging.getLogger("AI_RPG").warning(f"API signal error: {e}")
        return Signal()


class FileSignalProvider(SignalProvider):
    """อ่าน signal จาก JSON file"""

    def __init__(self, signal_file: str):
        self.signal_file = signal_file

    async def get_signal(self) -> Signal:
        try:
            if not os.path.exists(self.signal_file):
                return Signal()

            with open(self.signal_file, "r") as f:
                data = json.load(f)

            sig = data.get("signal", "hold")
            if sig in ("buy", "sell"):
                return Signal(
                    direction=SignalDirection(sig),
                    confidence=float(data.get("confidence", 0)),
                    entry_price=float(data.get("entry_price", 0)),
                    stop_loss=float(data.get("stop_loss", 0)),
                    take_profit=float(data.get("take_profit", 0)),
                    position_size=float(data.get("position_size", 0)),
                    risk_reward_ratio=float(data.get("risk_reward_ratio", 0)),
                    consensus=data.get("consensus", ""),
                    risk_level=data.get("risk_level", "medium"),
                    timestamp=data.get("timestamp", ""),
                    source="file",
                    valid=True
                )
        except Exception as e:
            logging.getLogger("AI_RPG").warning(f"File signal error: {e}")
        return Signal()


class SimSignalProvider(SignalProvider):
    """สร้าง signal จำลอง"""

    def __init__(self, sim_data: SimDataGenerator):
        self.sim_data = sim_data

    async def get_signal(self) -> Signal:
        return self.sim_data.generate_signal()


# ══════════════════════════════════════════════════════════════
# RISK MANAGEMENT
# ══════════════════════════════════════════════════════════════

class RiskManager:
    """ตรวจสอบความเสี่ยงก่อนเทรด"""

    def __init__(self, config: dict, logger: logging.Logger):
        self.config = config
        self.log = logger

    def validate(self, signal: Signal, state: EngineState, current_price: float) -> bool:
        """ตรวจสอบ signal ก่อน execute"""

        # 1. Check confidence
        if signal.confidence < self.config["min_confidence"]:
            self.log.info(f"REJECT: confidence {signal.confidence:.3f} < {self.config['min_confidence']}")
            return False

        # 2. Check max open trades
        open_trades = [t for t in state.trades if t.status == TradeStatus.OPEN]
        if len(open_trades) >= self.config["max_open_trades"]:
            self.log.info(f"REJECT: max trades {len(open_trades)}/{self.config['max_open_trades']}")
            return False

        # 3. Check signal expiry
        if signal.timestamp:
            try:
                sig_time = datetime.fromisoformat(signal.timestamp.replace("Z", "+00:00"))
                age_min = (datetime.now(timezone.utc) - sig_time).total_seconds() / 60
                if age_min > self.config["signal_expiry_min"]:
                    self.log.info(f"REJECT: signal expired ({age_min:.0f} min)")
                    return False
            except:
                pass

        # 4. Check risk:reward
        if signal.risk_reward_ratio > 0 and signal.risk_reward_ratio < 1.0:
            self.log.info(f"REJECT: R:R {signal.risk_reward_ratio:.2f} < 1.0")
            return False

        return True

    def calculate_lot(self, signal: Signal, state: EngineState, current_price: float) -> float:
        """คำนวณ lot size จาก risk percentage"""

        lot = signal.position_size
        if lot <= 0:
            balance = state.account.balance
            risk_amount = balance * self.config["risk_percent"] / 100.0

            if signal.stop_loss > 0:
                if signal.direction == SignalDirection.BUY:
                    sl_distance = abs(current_price - signal.stop_loss)
                else:
                    sl_distance = abs(signal.stop_loss - current_price)
            else:
                sl_distance = current_price * 0.02  # Default 2% SL

            if sl_distance > 0:
                # Simplified: assume $1 per pip per 0.01 lot
                lot = risk_amount / (sl_distance * 100)
            else:
                lot = self.config["min_lot"]

        # Clamp
        lot = max(self.config["min_lot"], min(self.config["max_lot"], lot))
        return round(lot, 2)


# ══════════════════════════════════════════════════════════════
# TRADE EXECUTOR
# ══════════════════════════════════════════════════════════════

class TradeExecutor:
    """Execute และ track trades"""

    def __init__(self, config: dict, logger: logging.Logger):
        self.config = config
        self.log = logger
        self.ticket_counter = 0

    def execute(self, signal: Signal, lot: float, current_price: float, source: str) -> Trade:
        """Execute trade (simulation)"""
        self.ticket_counter += 1

        trade = Trade(
            ticket=self.ticket_counter,
            action=signal.direction.value,
            lot=lot,
            entry_price=round(current_price, 2),
            sl=signal.stop_loss,
            tp=signal.take_profit,
            status=TradeStatus.OPEN,
            open_time=datetime.now().isoformat(),
            source=source
        )

        self.log.info(f"✅ EXECUTED: {signal.direction.value.upper()} @ {current_price:.2f} "
                      f"lot={lot} SL={signal.stop_loss} TP={signal.take_profit} "
                      f"conf={signal.confidence:.3f} #{self.ticket_counter}")

        return trade

    def close_trade(self, trade: Trade, close_price: float) -> float:
        """ปิด trade และคำนวณ PnL"""
        trade.close_price = close_price
        trade.close_time = datetime.now().isoformat()
        trade.status = TradeStatus.CLOSED

        if trade.action == "buy":
            pnl = (close_price - trade.entry_price) * trade.lot * 100
        else:
            pnl = (trade.entry_price - close_price) * trade.lot * 100

        trade.pnl = round(pnl, 2)
        return pnl

    def check_stop_loss_take_profit(self, trade: Trade, current_price: float) -> bool:
        """เช็คว่า SL/TP ถูก hit หรือไม่"""
        if trade.action == "buy":
            if trade.sl > 0 and current_price <= trade.sl:
                return True
            if trade.tp > 0 and current_price >= trade.tp:
                return True
        elif trade.action == "sell":
            if trade.sl > 0 and current_price >= trade.sl:
                return True
            if trade.tp > 0 and current_price <= trade.tp:
                return True
        return False


# ══════════════════════════════════════════════════════════════
# MAIN ENGINE
# ══════════════════════════════════════════════════════════════

class AIRPGEngine:
    """Main Trading Engine — รวมทุกอย่างเข้าด้วยกัน"""

    def __init__(self, config: dict):
        self.config = config
        self.log = setup_logging(config["log_file"])
        self.state = EngineState()
        self.risk_mgr = RiskManager(config, self.log)
        self.executor = TradeExecutor(config, self.log)

        # Setup providers based on mode
        self.mode = config["mode"]
        self.signal_provider = None
        self.data_provider = None
        self.sim_data = None

        if self.mode == "simulation":
            self.sim_data = SimDataGenerator(config["symbol"])
            self.signal_provider = SimSignalProvider(self.sim_data)
            self.log.info("Mode: SIMULATION")
        elif self.mode == "bridge":
            self.signal_provider = APISignalProvider(config["api_url"], config["api_key"], config["symbol"])
            self.log.info(f"Mode: BRIDGE → {config['api_url']}")
        elif self.mode == "hybrid":
            self.signal_provider = APISignalProvider(config["api_url"], config["api_key"], config["symbol"])
            self.data_provider = BinanceProvider(config["symbol"], config["timeframe"])
            self.log.info(f"Mode: HYBRID → {config['api_url']} + Binance")

    async def init(self):
        """เริ่มต้น engine"""
        self.log.info("═══════════════════════════════════════════")
        self.log.info("  AI_RPG Trading Engine v2.0 — Python")
        self.log.info(f"  Symbol: {self.config['symbol']} | TF: {self.config['timeframe']}")
        self.log.info(f"  Risk: {self.config['risk_percent']}% | MaxTrades: {self.config['max_open_trades']}")
        self.log.info(f"  Balance: ${self.config['initial_balance']:,.2f}")
        self.log.info("═══════════════════════════════════════════")

        self.state.account.balance = self.config["initial_balance"]
        self.state.account.equity = self.config["initial_balance"]
        self.state.account.free_margin = self.config["initial_balance"]
        self.state.initialized = True

        if self.data_provider:
            await self.data_provider.init()

        # Initial data
        if self.mode == "simulation":
            candles = self.sim_data.generate_candles(200)
            self.log.info(f"Generated {len(candles)} simulated candles")
            self.log.info(f"Price range: ${candles[0].close:,.2f} → ${candles[-1].close:,.2f}")

    async def get_current_price(self) -> float:
        """ดึงราคาปัจจุบัน"""
        if self.mode == "hybrid" and self.data_provider:
            price = await self.data_provider.get_price()
            if price > 0:
                return price
        if self.sim_data:
            return self.sim_data.current_price
        return 0.0

    async def scan_once(self):
        """สแกน 1 รอบ"""
        current_price = await self.get_current_price()
        if current_price <= 0:
            return

        # 1. Check SL/TP for open trades
        for trade in self.state.trades:
            if trade.status == TradeStatus.OPEN:
                if self.executor.check_stop_loss_take_profit(trade, current_price):
                    pnl = self.executor.close_trade(trade, current_price)
                    self.state.total_pnl += pnl
                    self.state.account.equity += pnl
                    self.log.info(f"{'🛑 SL' if pnl < 0 else '🎯 TP'} hit: #{trade.action} PnL=${pnl:.2f}")

        # 2. Get signal
        signal = await self.signal_provider.get_signal()

        if signal.valid and signal.direction != SignalDirection.HOLD:
            self.state.current_signal = signal
            self.log.info(f"Signal: {signal.direction.value.upper()} conf={signal.confidence:.3f} "
                          f"SL={signal.stop_loss} TP={signal.take_profit} src={signal.source}")

            # 3. Validate
            if self.risk_mgr.validate(signal, self.state, current_price):
                # 4. Calculate lot
                lot = self.risk_mgr.calculate_lot(signal, self.state, current_price)

                # 5. Execute
                trade = self.executor.execute(signal, lot, current_price, signal.source)
                self.state.trades.append(trade)
                self.state.total_trades += 1
            else:
                self.log.info("Signal rejected by risk manager")
        else:
            self.state.consecutive_errors = 0

        # 6. Update equity
        open_pnl = 0
        for t in self.state.trades:
            if t.status == TradeStatus.OPEN:
                if t.action == "buy":
                    open_pnl += (current_price - t.entry_price) * t.lot * 100
                else:
                    open_pnl += (t.entry_price - current_price) * t.lot * 100

        self.state.account.equity = self.state.account.balance + self.state.total_pnl + open_pnl

    async def write_status(self):
        """เขียน status file"""
        status = {
            "engine": "AI_RPG v2.0 Python",
            "mode": self.mode,
            "symbol": self.config["symbol"],
            "total_trades": self.state.total_trades,
            "total_pnl": round(self.state.total_pnl, 2),
            "equity": round(self.state.account.equity, 2),
            "balance": round(self.state.account.balance, 2),
            "open_positions": len([t for t in self.state.trades if t.status == TradeStatus.OPEN]),
            "last_signal": self.state.current_signal.direction.value if self.state.current_signal else "none",
            "last_confidence": self.state.current_signal.confidence if self.state.current_signal else 0,
            "last_update": datetime.now().isoformat()
        }

        try:
            with open(self.config["status_file"], "w") as f:
                json.dump(status, f, indent=2)
        except:
            pass

    async def print_dashboard(self):
        """แสดง dashboard"""
        open_trades = [t for t in self.state.trades if t.status == TradeStatus.OPEN]
        closed_trades = [t for t in self.state.trades if t.status == TradeStatus.CLOSED]
        wins = [t for t in closed_trades if t.pnl > 0]
        losses = [t for t in closed_trades if t.pnl < 0]

        win_rate = len(wins) / len(closed_trades) * 100 if closed_trades else 0

        print("\n" + "=" * 55)
        print(f"  📊 AI_RPG Dashboard | {self.config['symbol']} | {self.mode.upper()}")
        print("=" * 55)
        print(f"  💰 Balance:  ${self.state.account.balance:>12,.2f}")
        print(f"  📈 Equity:   ${self.state.account.equity:>12,.2f}")
        print(f"  💵 PnL:      ${self.state.total_pnl:>+12,.2f}")
        print(f"  📉 Win Rate:  {win_rate:.1f}% ({len(wins)}W/{len(losses)}L)")
        print(f"  🔄 Open:      {len(open_trades)} positions")
        print(f"  📋 Total:     {self.state.total_trades} trades")
        if self.state.current_signal and self.state.current_signal.valid:
            print(f"  🎯 Signal:    {self.state.current_signal.direction.value.upper()} "
                  f"conf={self.state.current_signal.confidence:.3f}")
        print("=" * 55)

    async def run(self):
        """Main loop"""
        await self.init()
        self.state.running = True

        poll_interval = self.config["poll_interval"]
        dashboard_counter = 0

        self.log.info(f"Engine running! Poll interval: {poll_interval}s")

        try:
            while self.state.running:
                try:
                    await self.scan_once()
                    await self.write_status()

                    # Print dashboard every 10 scans
                    dashboard_counter += 1
                    if dashboard_counter >= 10:
                        await self.print_dashboard()
                        dashboard_counter = 0

                    # Simulate price movement
                    if self.sim_data:
                        self.sim_data.tick()

                    await asyncio.sleep(poll_interval)

                except asyncio.CancelledError:
                    break
                except Exception as e:
                    self.state.consecutive_errors += 1
                    self.log.error(f"Loop error: {e}")
                    if self.state.consecutive_errors >= self.state.max_consecutive_errors:
                        self.log.warning("Too many errors, pausing 30s...")
                        await asyncio.sleep(30)
                        self.state.consecutive_errors = 0
                    await asyncio.sleep(poll_interval)

        except KeyboardInterrupt:
            self.log.info("Stopped by user")

        # Final report
        await self.print_dashboard()
        self.log.info(f"Engine stopped. Total trades: {self.state.total_trades} PnL: ${self.state.total_pnl:+.2f}")


# ══════════════════════════════════════════════════════════════
# ENTRY POINT
# ══════════════════════════════════════════════════════════════

async def main():
    parser = argparse.ArgumentParser(description="AI_RPG Trading Engine v2.0")
    parser.add_argument("--mode", choices=["simulation", "bridge", "hybrid"], default="simulation")
    parser.add_argument("--symbol", default="BTCUSDT")
    parser.add_argument("--api-url", default="http://185.84.160.106")
    parser.add_argument("--api-key", default="mt5bridge2024")
    parser.add_argument("--risk", type=float, default=2.0)
    parser.add_argument("--poll", type=int, default=10)
    args = parser.parse_args()

    config = DEFAULT_CONFIG.copy()
    config.update({
        "mode": args.mode,
        "symbol": args.symbol,
        "api_url": args.api_url,
        "api_key": args.api_key,
        "risk_percent": args.risk,
        "poll_interval": args.poll,
    })

    engine = AIRPGEngine(config)
    await engine.run()


if __name__ == "__main__":
    asyncio.run(main())
