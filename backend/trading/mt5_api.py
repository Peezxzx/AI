"""
MT5 Bridge API Router — REST endpoints for MetaTrader 5 EA communication

สำหรับ MT5 EA (WebRequest mode) เรียกใช้
Flow:  MT5 EA → HTTP → /api/mt5/* → Trading Engine

Endpoints:
  POST /api/mt5/price      — รับ price data จาก MT5 EA
  POST /api/mt5/candles    — รับ candle data จาก MT5 EA
  GET  /api/mt5/signal     — MT5 ขอ signal (return buy/sell/hold)
  POST /api/mt5/executed   — MT5 แจ้งว่า execute แล้ว
  GET  /api/mt5/close      — MT5 ถามว่าต้องปิด position ไหม
  GET  /api/mt5/status     — สถานะระบบทั้งหมด
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Header

log = logging.getLogger("mt5bridge")

router = APIRouter(prefix="/api/mt5", tags=["mt5"])

# ══════════════════════════════════════════════════════════════
# IN-MEMORY STATE (replace with DB in production)
# ══════════════════════════════════════════════════════════════

_mt5_state = {
    "connected_eas": {},         # {symbol: last_seen_timestamp}
    "last_prices": {},           # {symbol: price_data}
    "last_candles": {},          # {symbol: {timeframe: candles}}
    "trade_reports": [],         # list of execution reports
    "close_commands": {},        # {symbol: {closeTicket:xxx}}
    "signal_cache": {},          # {symbol: SignalRecommendation}
}


# ══════════════════════════════════════════════════════════════
# AUTH
# ══════════════════════════════════════════════════════════════

def verify_x_api_key(x_api_key: Optional[str] = Header(None)):
    """ตรวจสอบ X-API-Key header จาก MT5 EA"""
    expected = "mt5bridge2024"
    if x_api_key != expected:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key


# ══════════════════════════════════════════════════════════════
# PRICE ENDPOINTS
# ══════════════════════════════════════════════════════════════

@router.post("/price")
async def mt5_post_price(
    request: dict,
    x_api_key: str = Header(None),
):
    """
    MT5 EA ส่ง price + account data มาเก็บ
    Body: {symbol, bid, ask, time, account: {balance, equity, margin, ...}}
    """
    verify_x_api_key(x_api_key)

    symbol = request.get("symbol", "unknown")
    now = datetime.now(timezone.utc).isoformat()

    _mt5_state["last_prices"][symbol] = {
        "symbol": symbol,
        "bid": float(request.get("bid", 0)),
        "ask": float(request.get("ask", 0)),
        "time": request.get("time", 0),
        "account": request.get("account", {}),
        "received_at": now,
    }

    _mt5_state["connected_eas"][symbol] = now

    log.debug(f"Price update: {symbol} bid={request.get('bid')} ask={request.get('ask')}")

    return {"status": "ok", "symbol": symbol, "received_at": now}


@router.get("/price/{symbol}")
async def mt5_get_price(
    symbol: str,
    x_api_key: str = Header(None),
):
    """ดึงราคาล่าสุดที่ MT5 ส่งมา"""
    verify_x_api_key(x_api_key)

    data = _mt5_state["last_prices"].get(symbol.upper())
    if not data:
        raise HTTPException(status_code=404, detail=f"No price data for {symbol}")
    return data


# ════════════════════════════════════════════════════════════======
# CANDLE ENDPOINTS
# ════════════════════════════════════════════════════════════======

@router.post("/candles")
async def mt5_post_candles(
    request: dict,
    x_api_key: str = Header(None),
):
    """
    MT5 EA ส่ง candle data มาเก็บ
    Body: {symbol, timeframe, candles: [{time, open, high, low, close, volume}]}
    """
    verify_x_api_key(x_api_key)

    symbol = request.get("symbol", "unknown")
    timeframe = request.get("timeframe", "unknown")
    candles = request.get("candles", [])

    if symbol not in _mt5_state["last_candles"]:
        _mt5_state["last_candles"][symbol] = {}

    _mt5_state["last_candles"][symbol][timeframe] = {
        "candles": candles,
        "received_at": datetime.now(timezone.utc).isoformat(),
        "count": len(candles),
    }

    log.debug(f"Candles: {symbol} {tf} → {len(candles)} bars")

    return {"status": "ok", "symbol": symbol, "timeframe": timeframe, "count": len(candles)}


@router.get("/candles/{symbol}")
async def mt5_get_candles(
    symbol: str,
    timeframe: str = Query(default="H1"),
    limit: int = Query(default=200, le=1000),
    x_api_key: str = Header(None),
):
    """ดึง candle data ที่ MT5 ส่งมา"""
    verify_x_api_key(x_api_key)

    sym_data = _mt5_state["last_candles"].get(symbol.upper(), {})
    tf_data = sym_data.get(timeframe)
    if not tf_data:
        raise HTTPException(status_code=404, detail=f"No candles for {symbol} {timeframe}")

    candles = tf_data["candles"][-limit:]
    return {"symbol": symbol, "timeframe": timeframe, "candles": candles, "count": len(candles)}


# ══════════════════════════════════════════════════════════════
# SIGNAL ENDPOINT
# ══════════════════════════════════════════════════════════════

@router.get("/signal")
async def mt5_get_signal(
    symbol: str = Query(...),
    timeframe: str = Query(default="H1"),
    x_api_key: str = Header(None),
):
    """
    MT5 EA ขอ signal — ส่ง signal กลับไปให้ MT5 execute
    กรณีไม่มี signal ส่ง {signal: null} กลับไป
    """
    verify_x_api_key(x_api_key)

    # ลองดึง signal จาก signal_generator (trading engine)
    signal = None
    try:
        from .signal_generator import generate_signal, SignalRecommendation
        from .auto_executor import get_state, execute_signal

        state = get_state()

        # ถ้ามี signal cache สำหรับ symbol นี้ ใช้เลย
        cached = _mt5_state["signal_cache"].get(symbol.upper())
        if cached:
            age_sec = (datetime.now(timezone.utc) - datetime.fromisoformat(cached.get("generated_at", "2000-01-01T00:00:00+00:00"))).total_seconds()
            if age_sec < 600:  # cache 10 นาที
                signal = cached

        # ถ้าไม่มี cache → generate ใหม่
        if not signal:
            rec = await generate_signal(
                symbol=symbol.upper(),
                timeframe=timeframe,
                capital=state.capital,
                risk_percent=state.risk_percent,
            )

            if rec.signal in ("buy", "sell"):
                signal = {
                    "signal": rec.signal,
                    "action": rec.signal.upper(),       # "BUY" | "SELL" สำหรับ MT5 EA
                    "confidence": rec.confidence,
                    "entry_price": rec.entry_price,
                    "sl": rec.stop_loss,
                    "tp": rec.take_profit,
                    "lotSize": rec.position_size,
                    "risk_reward_ratio": rec.risk_reward_ratio,
                    "consensus": rec.consensus,
                    "risk_level": rec.risk_level,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "warnings": rec.warnings,
                }

                # Cache signal
                _mt5_state["signal_cache"][symbol.upper()] = signal

                log.info(f"Signal for {symbol}: {rec.signal.upper()} conf={rec.confidence:.3f} "
                         f"SL={rec.stop_loss} TP={rec.take_profit}")

    except Exception as e:
        log.error(f"Signal generation error: {e}")

    if signal:
        return signal
    else:
        # ไม่มี signal — ส่ง null กลับไป (MT5 จะไม่ทำอะไร)
        return {"signal": None, "action": None}


# ══════════════════════════════════════════════════════════════
# TRADE EXECUTION REPORT
# ══════════════════════════════════════════════════════════════

@router.post("/executed")
async def mt5_post_executed(
    request: dict,
    x_api_key: str = Header(None),
):
    """
    MT5 EA แจ้งว่า execute trade แล้ว
    Body: {ticket, mt5Ticket, action, price, lot, sl, tp, time}
    """
    verify_x_api_key(x_api_key)

    report = {
        "ticket": request.get("ticket"),
        "mt5Ticket": request.get("mt5Ticket"),
        "action": request.get("action"),
        "price": float(request.get("price", 0)),
        "lot": float(request.get("lot", 0)),
        "sl": float(request.get("sl", 0)),
        "tp": float(request.get("tp", 0)),
        "confidence": float(request.get("confidence", 0)),
        "source": request.get("source", "unknown"),
        "time": request.get("time", 0),
        "received_at": datetime.now(timezone.utc).isoformat(),
    }

    _mt5_state["trade_reports"].append(report)

    # เก็บแค่ 1000 reports ล่าสุด
    if len(_mt5_state["trade_reports"]) > 1000:
        _mt5_state["trade_reports"] = _mt5_state["trade_reports"][-1000:]

    log.info(f"Trade executed: {report['action']} #{report['mt5Ticket']} "
             f"@ {report['price']} lot={report['lot']}")

    return {"status": "ok", "report": report}


@router.get("/trades")
async def mt5_get_trades(
    limit: int = Query(default=50, le=500),
    x_api_key: str = Header(None),
):
    """ดึง trade execution history"""
    verify_x_api_key(x_api_key)

    trades = _mt5_state["trade_reports"][-limit:]
    return {"trades": trades, "count": len(trades)}


# ══════════════════════════════════════════════════════════════
# POSITION CLOSE COMMAND
# ══════════════════════════════════════════════════════════════

@router.get("/close")
async def mt5_get_close(
    symbol: str = Query(default=""),
    x_api_key: str = Header(None),
):
    """
    MT5 EA ถามว่าต้องปิบ position ไหม
    MT5 EA เรียกทุก 10 วินาที ถ้ามี close command จะส่งกลับ
    """
    verify_x_api_key(x_api_key)

    # เช็คว่ามี close command สำหรับ symbol นี้หรือไม่
    if symbol and symbol in _mt5_state["close_commands"]:
        cmd = _mt5_state["close_commands"].pop(symbol)
        log.info(f"Close command for {symbol}: ticket={cmd['closeTicket']}")
        return cmd

    # ไม่มี close command
    return {"closeTicket": None}


@router.post("/close")
async def mt5_post_close(
    request: dict,
    x_api_key: str = Header(None),
):
    """
    Backend สั่งปิบ position
    Body: {symbol, closeTicket: <mt5_ticket_number>}
    """
    verify_x_api_key(x_api_key)

    symbol = request.get("symbol", "").upper()
    close_ticket = request.get("closeTicket")

    if symbol and close_ticket:
        _mt5_state["close_commands"][symbol] = {
            "closeTicket": close_ticket,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        log.info(f"Close requested: {symbol} ticket={close_ticket}")
        return {"status": "ok", "command_queued": True}

    raise HTTPException(status_code=400, detail="Missing symbol or closeTicket")


# ══════════════════════════════════════════════════════════════
# SYSTEM STATUS
# ══════════════════════════════════════════════════════════════

@router.get("/status")
async def mt5_get_status(
    x_api_key: str = Header(None),
):
    """สถานะระบบ MT5 bridge"""
    verify_x_api_key(x_api_key)

    from .auto_executor import get_state
    executor_state = get_state()

    return {
        "status": "ok",
        "connected_eas": len(_mt5_state["connected_eas"]),
        "symbols": list(_mt5_state["connected_eas"].keys()),
        "last_prices": {s: {
            "bid": d["bid"],
            "ask": d["ask"],
            "received_at": d["received_at"]
        } for s, d in _mt5_state["last_prices"].items()},
        "candle_data_symbols": list(_mt5_state["last_candles"].keys()),
        "total_trade_reports": len(_mt5_state["trade_reports"]),
        "executor": {
            "running": executor_state.running,
            "capital": executor_state.capital,
            "total_pnl": executor_state.total_pnl,
            "open_positions": len(executor_state.open_orders),
        },
        "server_time": datetime.now(timezone.utc).isoformat(),
    }
