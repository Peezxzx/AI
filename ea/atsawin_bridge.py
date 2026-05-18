"""
================================================================
ATSAWIN EA BRIDGE — Python Signal Generator → JSON → MT5 EA
================================================================
รวมทุกอย่างในไฟล์เดียว: config, API client, signal writer, filter, scheduler

วิธีใช้:
  python atsawin_bridge.py              # วนลูปสแกนตาม interval
  python atsawin_bridge.py --once       # สแกน 1 รอบแล้วจบ
  python atsawin_bridge.py --once --symbol BTCUSD --tf H1

Flow:  Trading AI API → atsawin_bridge.py → latest_signal.json → MT5 EA
================================================================
"""

import asyncio, json, logging, os, sys, argparse
from datetime import datetime, timezone
from pathlib import Path
from logging.handlers import RotatingFileHandler

try:
    import aiohttp
except ImportError:
    print("ERROR: aiohttp not installed. Run: pip install aiohttp")
    sys.exit(1)

# ══════════════════════════════════════════════════════════════
# CONFIG — แก้ค่าตรงนี้ได้เลย
# ══════════════════════════════════════════════════════════════
CONFIG = {
    # --- API ---
    "api_url": "http://localhost:8000",
    "api_key": "atsawin-ea-bridge-key",
    "capital": 10000.0,

    # --- สินค้า & ไทม์เฟรม ---
    "symbols": ["BTCUSD", "ETHUSD", "XAUUSD", "EURUSD", "GBPUSD"],
    "timeframe": "H1",           # M15 M30 H1 H4 D1
    "scan_interval": 300,        # วินที (5 นาที)

    # --- Signal Filter ---
    "min_confidence": 0.5,       # ความมั่นใจขั้นต่ำ 0-1
    "min_risk_reward": 1.5,      # Risk:Reward ขั้นต่ำ

    # --- ไฟล์ Bridge ---
    "signal_file": "/root/Atsawin-AI-Core/ea/latest_signal.json",
    "status_file": "/root/Atsawin-AI-Core/ea/ea_status.json",
    "log_file":   "/root/Atsawin-AI-Core/ea/bridge.log",

    # --- Mapping ---
    "sym_map": {                 # MT5 symbol → Binance API symbol
        "BTCUSD": "BTCUSDT", "ETHUSD": "ETHUSDT", "XRPUSD": "XRPUSDT",
        "BNBUSD": "BNBUSDT", "SOLUSD": "SOLUSDT", "XAUUSD": "XAUUSDT",
        "EURUSD": "EURUSDT", "GBPUSD": "GBPUSDT",
    },
    "tf_map": {                  # MT5 timeframe → API timeframe
        "M1": "1m", "M5": "5m", "M15": "15m", "M30": "30m",
        "H1": "1h", "H4": "4h", "D1": "1d",
    },
}

# ══════════════════════════════════════════════════════════════
# LOGGING
# ══════════════════════════════════════════════════════════════
Path(CONFIG["log_file"]).parent.mkdir(parents=True, exist_ok=True)
log = logging.getLogger("EABridge")
log.setLevel(logging.INFO)
fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
log.addHandler(logging.StreamHandler(sys.stdout))
log.addHandler(RotatingFileHandler(CONFIG["max_log_size_mb"] * 1024 * 1024 if False else CONFIG["log_file"], maxBytes=10*1024*1024, backupCount=3))

# ══════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════
def sym_to_api(s): return CONFIG["sym_map"].get(s, s)
def sym_to_mt5(s): return {v:k for k,v in CONFIG["sym_map"].items()}.get(s, s)
def tf_to_api(tf): return CONFIG["tf_map"].get(tf, tf.lower())

def atomic_write(path, data):
    """เขียนไฟล์แบบ atomic (ไม่เสียหายถ้า MT5 อ่านระหว่างเขียน)"""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2, default=str))
    tmp.replace(p)

# ══════════════════════════════════════════════════════════════
# MAIN BRIDGE
# ══════════════════════════════════════════════════════════════
async def scan_once(session, symbols=None, tf=None):
    """สแกนสัญญาณ 1 รอบ → เขียนไฟล์"""
    syms = symbols or CONFIG["symbols"]
    timeframe = tf or CONFIG["timeframe"]
    api_tf = tf_to_api(timeframe)
    headers = {"X-API-Key": CONFIG["api_key"], "Content-Type": "application/json"}
    best_signal, best_conf = None, 0.0

    for sym in syms:
        api_sym = sym_to_api(sym)
        try:
            # เรียก API composite signal
            r = await session.post(
                f"{CONFIG['api_url']}/trading/ea/strategies/analyze",
                json={"symbol": api_sym, "timeframe": api_tf, "limit": 200},
                headers=headers, timeout=aiohttp.ClientTimeout(total=15)
            )
            if r.status != 200:
                log.warning(f"  {sym}: API error {r.status}")
                continue
            data = await r.json()

            sig = data.get("signal", "hold")
            conf = data.get("confidence", 0)
            rr = data.get("risk_reward_ratio", 0)
            consensus = data.get("consensus", "")

            # Filter
            if sig == "hold":
                log.debug(f"  {sym}: HOLD")
                continue
            if conf < CONFIG["min_confidence"]:
                log.debug(f"  {sym}: confidence too low ({conf:.2f})")
                continue
            if rr and rr < CONFIG["min_risk_reward"]:
                log.debug(f"  {sym}: R:R too low ({rr:.2f})")
                continue

            log.info(f"  {sym}: {sig.upper()} conf={conf:.2f} rr={rr:.2f} consensus={consensus}")

            if conf > best_conf:
                best_conf = conf
                best_signal = data

        except Exception as e:
            log.error(f"  {sym}: {e}")

    # เขียน signal file
    if best_signal:
        out = {
            "version": "1.0",
            "signal": best_signal.get("signal", "hold"),
            "symbol": sym_to_mt5(best_signal.get("symbol", "")),
            "timeframe": timeframe,
            "confidence": best_signal.get("confidence", 0),
            "consensus": best_signal.get("consensus", ""),
            "buy_score": best_signal.get("buy_score", 0),
            "sell_score": best_signal.get("sell_score", 0),
            "entry_price": best_signal.get("entry_price", 0),
            "stop_loss": best_signal.get("stop_loss", 0),
            "take_profit": best_signal.get("take_profit", 0),
            "position_size": best_signal.get("position_size", 0),
            "risk_reward_ratio": best_signal.get("risk_reward_ratio", 0),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        atomic_write(CONFIG["signal_file"], out)
        log.info(f"✅ Signal written: {out['signal'].upper()} {out['symbol']} @ {out['entry_price']}")
    else:
        atomic_write(CONFIG["signal_file"], {
            "signal": "hold", "confidence": 0, "reason": "No valid signals",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        log.info("No valid signals → HOLD")

    # เขียน status
    atomic_write(CONFIG["status_file"], {
        "last_scan": datetime.now(timezone.utc).isoformat(),
        "best_signal": best_signal.get("signal", "hold") if best_signal else "hold",
        "best_symbol": sym_to_mt5(best_signal.get("symbol", "")) if best_signal else "",
        "best_confidence": best_conf,
    })

    return best_signal


async def run_loop():
    """วนลูปสแกนตาม interval"""
    log.info("=" * 50)
    log.info("Atsawin EA Bridge started")
    log.info(f"API: {CONFIG['api_url']}")
    log.info(f"Symbols: {CONFIG['symbols']} @ {CONFIG['timeframe']}")
    log.info(f"Scan interval: {CONFIG['scan_interval']}s")
    log.info(f"Signal file: {CONFIG['signal_file']}")
    log.info("=" * 50)

    async with aiohttp.ClientSession() as session:
        while True:
            try:
                await scan_once(session)
            except KeyboardInterrupt:
                break
            except Exception as e:
                log.error(f"Scan error: {e}")
            await asyncio.sleep(CONFIG["scan_interval"])

    log.info("Bridge stopped")


# ══════════════════════════════════════════════════════════════
# ENTRY POINT
# ══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Atsawin EA Bridge")
    parser.add_argument("--once", action="store_true", help="สแกน 1 รอบแล้วจบ")
    parser.add_argument("--symbol", type=str, help="สแกน symbol เดียว (เช่น BTCUSD)")
    parser.add_argument("--tf", type=str, help="Timeframe (M15/H1/H4/D1)")
    args = parser.parse_args()

    syms = [args.symbol] if args.symbol else None
    tf = args.tf or None

    if args.once:
        asyncio.run(scan_once(aiohttp.ClientSession(), syms, tf))
    else:
        asyncio.run(run_loop())
