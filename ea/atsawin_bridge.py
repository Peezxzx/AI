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
DEFAULT_BRIDGE_DIR = Path(
    os.environ.get(
        "ATSAWIN_BRIDGE_DIR",
        str(Path(os.environ.get("APPDATA", str(Path.home() / "AppData/Roaming")))
            / "MetaQuotes/Terminal/Common/Files/atsawin")
    )
)

CONFIG = {
    # --- API ---
    "api_url": os.environ.get("ATSAWIN_API_URL", "http://185.84.161.189:8000"),
    "api_key": os.environ.get("ATSAWIN_API_KEY", "atsawin-ea-bridge-key"),
    "capital": 10000.0,

    # --- สินค้า & ไทม์เฟรม ---
    "symbols": ["BTCUSD", "ETHUSD", "XAUUSD", "EURUSD", "GBPUSD"],
    "timeframe": "H1",           # M15 M30 H1 H4 D1
    "scan_interval": 300,        # วินที (5 นาที)

    # --- Signal Filter ---
    "min_confidence": 0.3,       # ความมั่นใจขั้นต่ำ 0-1 (ลดลงจาก 0.5 เพื่อ testing)
    "min_risk_reward": 1.5,      # Risk:Reward ขั้นต่ำ

    # --- ไฟล์ Bridge ---
    "signal_file": str(DEFAULT_BRIDGE_DIR / "latest_signal.json"),
    "status_file": str(DEFAULT_BRIDGE_DIR / "ea_status.json"),
    "log_file":   str(DEFAULT_BRIDGE_DIR / "bridge.log"),

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
# Console handler
log.addHandler(logging.StreamHandler(sys.stdout))
# File handler (rotate at 10MB, keep 3 backups)
log.addHandler(RotatingFileHandler(CONFIG["log_file"], maxBytes=10*1024*1024, backupCount=3))

# ══════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════
def sym_to_api(s): return CONFIG["sym_map"].get(s, s)
def sym_to_mt5(s):
    reverse = {v: k for k, v in CONFIG["sym_map"].items()}
    return reverse.get(s, s)
def tf_to_api(tf): return CONFIG["tf_map"].get(tf, tf.lower())

def atomic_write(path, data):
    """เขียนไฟล์แบบ atomic (ไม่เสียหายถ้า MT5 อ่านระหว่างเขียน)"""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2, default=str, ensure_ascii=True))
    tmp.replace(p)

async def api_request(session, method, path, json_data=None, retries=3):
    """API request with retry logic."""
    url = f"{CONFIG['api_url']}{path}"
    headers = {"X-API-Key": CONFIG["api_key"], "Content-Type": "application/json"}
    
    for attempt in range(retries):
        try:
            if method == "POST":
                async with session.post(url, json=json_data, headers=headers,
                                        timeout=aiohttp.ClientTimeout(total=30)) as r:
                    if r.status == 200:
                        return await r.json()
                    body = await r.text()
                    log.warning(f"  API {path} → {r.status}: {body[:200]}")
                    if r.status == 404:
                        return None  # Don't retry 404
            else:
                async with session.get(url, headers=headers,
                                       timeout=aiohttp.ClientTimeout(total=30)) as r:
                    if r.status == 200:
                        return await r.json()
                    body = await r.text()
                    log.warning(f"  API {path} → {r.status}: {body[:200]}")
                    return None
        except asyncio.TimeoutError:
            log.warning(f"  API {path} timeout (attempt {attempt+1}/{retries})")
        except aiohttp.ClientError as e:
            log.warning(f"  API {path} error: {e} (attempt {attempt+1}/{retries})")
        
        if attempt < retries - 1:
            await asyncio.sleep(2 * (attempt + 1))  # Exponential backoff
    
    return None

async def health_check(session):
    """Check if API is reachable."""
    result = await api_request(session, "GET", "/health")
    if result:
        log.info(f"API health: OK ({result.get('status', 'unknown')})")
        return True
    log.error("API health check FAILED")
    return False

# ══════════════════════════════════════════════════════════════
# MAIN BRIDGE
# ══════════════════════════════════════════════════════════════
async def scan_once(session, symbols=None, tf=None):
    """สแกนสัญญาณ 1 รอบ → เขียนไฟล์"""
    syms = symbols or CONFIG["symbols"]
    timeframe = tf or CONFIG["timeframe"]
    api_tf = tf_to_api(timeframe)
    best_signal, best_conf = None, 0.0
    scanned, errors, holds, filtered = 0, 0, 0, 0

    for sym in syms:
        api_sym = sym_to_api(sym)
        try:
            # เรียก API /trading/ea/scan — return opportunities ที่มี SL/TP/entry/position_size ครบ
            data = await api_request(session, "POST", "/trading/ea/scan", json_data={
                "symbols": [api_sym],
                "timeframes": [api_tf],
                "min_confidence": 0.0,  # ให้ API ส่งกลับมาทั้งหมด แล้ว filter เอง
                "capital": CONFIG["capital"],
                "risk_percent": 2.0,
            })
            
            if data is None:
                errors += 1
                continue

            opportunities = data.get("opportunities", [])
            scanned += 1
            
            if not opportunities:
                # ลอง fallback: เรียก /trading/analysis/signal โดยตรง
                log.debug(f"  {sym}: no opportunities from /ea/scan, trying /analysis/signal")
                raw = await api_request(session, "GET", 
                    f"/trading/analysis/signal?symbol={api_sym}&timeframe={api_tf}")
                if raw and raw.get("signal") and raw.get("signal") != "hold":
                    # สร้าง opportunity จาก raw signal — คำนวณ SL/TP เอง
                    current_price = 0
                    try:
                        price_data = await api_request(session, "GET",
                            f"/trading/market/price?symbol={api_sym}")
                        if price_data:
                            current_price = float(price_data.get("price", 0))
                    except:
                        pass
                    
                    sig_direction = raw["signal"]  # "buy" or "sell"
                    # ประมาณ SL/TP จาก percentage (ATR ไม่มีใน fallback)
                    if current_price > 0:
                        if sig_direction == "buy":
                            sl_price = current_price * 0.98   # 2% below
                            tp_price = current_price * 1.03   # 3% above
                        else:
                            sl_price = current_price * 1.02   # 2% above
                            tp_price = current_price * 0.97   # 3% below
                        rr_ratio = 1.5
                    else:
                        sl_price = 0
                        tp_price = 0
                        rr_ratio = 0
                    
                    opportunities = [{
                        "signal": sig_direction,
                        "symbol": api_sym,
                        "timeframe": api_tf,
                        "confidence": raw.get("confidence", 0),
                        "consensus": "",
                        "buy_score": 1.0 if sig_direction == "buy" else 0.0,
                        "sell_score": 1.0 if sig_direction == "sell" else 0.0,
                        "entry_price": current_price,
                        "stop_loss": round(sl_price, 2),
                        "take_profit": round(tp_price, 2),
                        "position_size": 0,
                        "risk_reward_ratio": rr_ratio,
                        "risk_level": "medium",
                        "warnings": [],
                    }]
                else:
                    log.debug(f"  {sym}: no signal from fallback either")
                    continue

            # เอา opportunity ที่ดีที่สุด
            for opp in opportunities:
                sig = opp.get("signal", "hold")
                conf = opp.get("confidence", 0)
                rr = opp.get("risk_reward_ratio", 0)
                consensus = opp.get("consensus", "")

                # Filter
                if sig == "hold":
                    holds += 1
                    log.debug(f"  {sym}: HOLD")
                    continue
                if conf < CONFIG["min_confidence"]:
                    filtered += 1
                    log.debug(f"  {sym}: confidence too low ({conf:.2f} < {CONFIG['min_confidence']})")
                    continue
                if rr and rr < CONFIG["min_risk_reward"]:
                    filtered += 1
                    log.debug(f"  {sym}: R:R too low ({rr:.2f} < {CONFIG['min_risk_reward']})")
                    continue

                log.info(f"  {sym}: {sig.upper()} conf={conf:.2f} rr={rr:.2f} consensus={consensus}")

                if conf > best_conf:
                    best_conf = conf
                    best_signal = opp

        except Exception as e:
            errors += 1
            log.error(f"  {sym}: {e}")

    log.info(f"Scan complete: {scanned} scanned, {errors} errors, {holds} holds, {filtered} filtered")

    # เขียน signal file
    if best_signal:
        signal_symbol = best_signal.get("symbol", "")
        now = datetime.now(timezone.utc)
        out = {
            "schema_version": "2.1",
            "contract": "atsawin_mt5_signal",
            "version": "1.3",
            "signal": best_signal.get("signal", "hold"),
            "symbol": sym_to_mt5(signal_symbol),  # Binance → MT5 symbol
            "mt5_symbol": sym_to_mt5(signal_symbol),
            "timeframe": best_signal.get("timeframe", timeframe),
            "confidence": best_signal.get("confidence", 0),
            "consensus": best_signal.get("consensus", ""),
            "buy_score": best_signal.get("buy_score", 0),
            "sell_score": best_signal.get("sell_score", 0),
            "entry_price": best_signal.get("entry_price", 0),
            "stop_loss": best_signal.get("stop_loss", 0),
            "take_profit": best_signal.get("take_profit", 0),
            "position_size": best_signal.get("position_size", 0),
            "risk_reward_ratio": best_signal.get("risk_reward_ratio", 0),
            "risk_level": best_signal.get("risk_level", ""),
            "warnings": best_signal.get("warnings", []),
            "timestamp": now.isoformat(),
            "timestamp_epoch": int(now.timestamp()),
            "expires_at_epoch": int(now.timestamp()) + int(CONFIG["scan_interval"] * 2 + 30),
            "source": "atsawin_bridge_v1.3",
        }
        out["setup_key"] = "|".join([
            str(out.get("mt5_symbol", "")), str(out.get("timeframe", "")), str(out.get("signal", "hold")),
            f"{float(out.get('entry_price') or 0):.2f}", f"{float(out.get('stop_loss') or 0):.2f}",
            f"{float(out.get('take_profit') or 0):.2f}", f"{float(out.get('confidence') or 0):.3f}",
        ])
        out["signal_id"] = out["setup_key"]
        atomic_write(CONFIG["signal_file"], out)

        log.info(f"✅ Signal written: {out['signal'].upper()} {out['symbol']} @ {out['entry_price']} SL={out['stop_loss']} TP={out['take_profit']}")
    else:
        now = datetime.now(timezone.utc)
        hold = {
            "schema_version": "2.1",
            "contract": "atsawin_mt5_signal",
            "version": "1.3",
            "signal": "hold",
            "confidence": 0,
            "reason": "No valid signals",
            "symbol": "",
            "mt5_symbol": "",
            "stop_loss": 0,
            "take_profit": 0,
            "risk_reward_ratio": 0,
            "timestamp": now.isoformat(),
            "timestamp_epoch": int(now.timestamp()),
            "expires_at_epoch": int(now.timestamp()) + int(CONFIG["scan_interval"] * 2 + 30),
            "source": "atsawin_bridge_v1.3",
        }
        hold["setup_key"] = "hold|no_valid_signals"
        hold["signal_id"] = hold["setup_key"]
        atomic_write(CONFIG["signal_file"], hold)
        log.info("No valid signals → HOLD")

    # เขียน status
    atomic_write(CONFIG["status_file"], {
        "last_scan": datetime.now(timezone.utc).isoformat(),
        "best_signal": best_signal.get("signal", "hold") if best_signal else "hold",
        "best_symbol": sym_to_mt5(best_signal.get("symbol", "")) if best_signal else "",
        "best_confidence": best_conf,
        "scanned": scanned,
        "errors": errors,
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
        # Health check on startup
        await health_check(session)
        
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
    parser.add_argument("--health", action="store_true", help="Check API health and exit")
    args = parser.parse_args()

    syms = [args.symbol] if args.symbol else None
    tf = args.tf or None

    if args.health:
        async def _health():
            async with aiohttp.ClientSession() as session:
                ok = await health_check(session)
                sys.exit(0 if ok else 1)
        asyncio.run(_health())
    elif args.once:
        async def _once():
            async with aiohttp.ClientSession() as session:
                return await scan_once(session, syms, tf)
        asyncio.run(_once())
    else:
        asyncio.run(run_loop())
