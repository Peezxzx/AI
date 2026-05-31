//+------------------------------------------------------------------+
//|                                          AtsawinEA.mq5 v2.0      |
//|                    Atsawin AI Trading EA — Unified Edition        |
//|                    รวม WebRequest + File-based + Risk Management  |
//|                                                                    |
//|  รองรับ 2 โหมด:                                                     |
//|    1. WebRequest Mode — เรียก API จาก Linux VPS โดยตรง            |
//|    2. File Mode — อ่าน signal จาก JSON file (Python bridge)        |
//|                                                                    |
//|  Flow:                                                              |
//|    WebRequest:  MT5 EA → HTTP GET/POST → Linux VPS API             |
//|    File Mode:   Python Bridge → latest_signal.json → MT5 EA        |
//+------------------------------------------------------------------+
#property copyright "Atsawin AI"
#property link      ""
#property version   "2.00"
#property strict

#include <Trade\Trade.mqh>
#include <Files\FileTxt.mqh>
#include <Files\FileJson.mqh>

//+------------------------------------------------------------------+
//| INPUT PARAMETERS                                                  |
//+------------------------------------------------------------------+
input group "═══ Connection Mode ═══"
input bool     InpUseWebRequest  = true;                              // true=WebRequest, false=File Mode
input string   InpLinuxVPS       = "http://185.84.160.106";          // Linux VPS URL
input string   InpApiKey         = "mt5bridge2024";                   // API Key

input group "═══ Signal File (File Mode) ═══"
input string   InpSignalFile     = "atsawin\\latest_signal.json";    // Signal JSON file
input string   InpStatusFile     = "atsawin\\ea_status.json";        // Status JSON file

input group "═══ Risk Management ═══"
input double   InpRiskPercent    = 2.0;                              // Risk % per trade
input double   InpMaxLot         = 1.0;                               // Max lot size
input double   InpMinLot         = 0.01;                              // Min lot size
input double   InpMaxSpreadPt    = 30;                                // Max spread (points)
input double   InpSlippagePt     = 10;                                // Max slippage (points)
input int      InpMaxOpenTrades  = 3;                                 // Max concurrent trades
input double   InpMinConfidence  = 0.3;                               // Min signal confidence (0-1)
input int      InpSignalExpiry   = 60;                                // Signal expiry (minutes)

input group "═══ Trading ═══"
input long     InpMagicNumber    = 20250518;                          // Magic Number
input int      InpPollSec        = 10;                                // Poll interval (seconds)
input bool     InpEnableLogging  = true;                              // Enable file logging
input bool     InpEnableAlerts   = true;                              // Enable alert popups

//+------------------------------------------------------------------+
//| GLOBAL VARIABLES                                                  |
//+------------------------------------------------------------------+
CTrade g_trade;
string g_signalFile;
string g_statusFile;
string g_logFile;
datetime g_lastSignalTime;
datetime g_lastBarTime;
datetime g_lastCandleTime;
int      g_totalTrades;
double   g_totalPnL;
double   g_dailyPnL;
datetime g_lastDay;
bool     g_initialized;
int      g_consecutiveErrors;
int      g_maxConsecutiveErrors = 5;

// Signal structure
struct SignalData
{
   string   version;
   string   signal;             // "buy" / "sell" / "hold"
   string   symbol;
   string   timeframe;
   double   confidence;         // 0-1
   string   consensus;
   double   buy_score;
   double   sell_score;
   double   entry_price;
   double   stop_loss;
   double   take_profit;
   double   position_size;
   double   risk_reward_ratio;
   string   risk_level;
   string   timestamp;
   bool     valid;
};

SignalData g_currentSignal;

// Trade tracking
struct TradeRecord
{
   ulong    ticket;
   string   action;
   double   lot;
   double   entry_price;
   double   sl;
   double   tp;
   double   close_price;
   double   pnl;
   string   status;             // "open" / "closed" / "failed"
   datetime open_time;
   datetime close_time;
   string   source;             // "webrequest" / "file"
};

TradeRecord g_tradeHistory[];
int g_tradeCount;

//+------------------------------------------------------------------+
//| Symbol Mapping: API name → MT5 name (fuzzy match)                |
//+------------------------------------------------------------------+
string SymbolToMT5(string apiSymbol)
{
   string baseSymbol = apiSymbol;
   int dotPos = StringFind(apiSymbol, ".");
   if(dotPos > 0)
      baseSymbol = StringSubstr(apiSymbol, 0, dotPos);

   if(baseSymbol == "BTCUSDT" || baseSymbol == "BTCUSD") return "BTCUSD";
   if(baseSymbol == "ETHUSDT" || baseSymbol == "ETHUSD") return "ETHUSD";
   if(baseSymbol == "XRPUSDT" || baseSymbol == "XRPUSD") return "XRPUSD";
   if(baseSymbol == "BNBUSDT" || baseSymbol == "BNBUSD") return "BNBUSD";
   if(baseSymbol == "SOLUSDT" || baseSymbol == "SOLUSD") return "SOLUSD";
   if(baseSymbol == "XAUUSDT" || baseSymbol == "XAUUSD") return "XAUUSD";
   if(baseSymbol == "EURUSDT" || baseSymbol == "EURUSD") return "EURUSD";
   if(baseSymbol == "GBPUSDT" || baseSymbol == "GBPUSD") return "GBPUSD";

   return apiSymbol;
}

//+------------------------------------------------------------------+
//| Check if symbols match (handles suffixes like .i, .m, etc.)      |
//+------------------------------------------------------------------+
bool SymbolMatches(string signalSymbol, string chartSymbol)
{
   if(signalSymbol == chartSymbol) return true;

   string sigBase = signalSymbol;
   string chrBase = chartSymbol;

   int dotPos;
   dotPos = StringFind(signalSymbol, ".");
   if(dotPos > 0) sigBase = StringSubstr(signalSymbol, 0, dotPos);
   dotPos = StringFind(chartSymbol, ".");
   if(dotPos > 0) chrBase = StringSubstr(chartSymbol, 0, dotPos);

   if(sigBase == chrBase) return true;

   int sigLen = StringLen(sigBase);
   int chrLen = StringLen(chrBase);
   if(sigLen > 4 && chrLen > 4)
   {
      string sigTrim = StringSubstr(sigBase, 0, sigLen - 1);
      string chrTrim = StringSubstr(chrBase, 0, chrLen - 1);
      if(sigTrim == chrTrim) return true;
   }

   return false;
}

//+------------------------------------------------------------------+
//| Logging                                                           |
//+------------------------------------------------------------------+
void LogMessage(string msg)
{
   if(!InpEnableLogging) return;
   string fullMsg = TimeToString(TimeCurrent(), TIME_DATE|TIME_SECONDS) + " [AtsawinEA v2] " + msg;
   Print(fullMsg);

   int handle = FileOpen(g_logFile, FILE_WRITE|FILE_TXT|FILE_SHARE_READ|FILE_COMMON);
   if(handle != INVALID_HANDLE)
   {
      FileSeek(handle, 0, SEEK_END);
      FileWriteString(handle, fullMsg + "\r\n");
      FileClose(handle);
   }
}

//+------------------------------------------------------------------+
//| Write status file for external monitoring                         |
//+------------------------------------------------------------------+
void WriteStatus()
{
   int handle = FileOpen(g_statusFile, FILE_WRITE|FILE_TXT|FILE_SHARE_READ|FILE_COMMON);
   if(handle == INVALID_HANDLE) return;

   FileWriteString(handle, "{");
   FileWriteString(handle, "\"ea_version\":\"2.00\",");
   FileWriteString(handle, "\"symbol\":\"" + _Symbol + "\",");
   FileWriteString(handle, "\"mode\":\"" + (InpUseWebRequest ? "webrequest" : "file") + "\",");
   FileWriteString(handle, "\"total_trades\":" + IntegerToString(g_totalTrades) + ",");
   FileWriteString(handle, "\"total_pnl\":" + DoubleToString(g_totalPnL, 2) + ",");
   FileWriteString(handle, "\"daily_pnl\":" + DoubleToString(g_dailyPnL, 2) + ",");
   FileWriteString(handle, "\"open_positions\":" + IntegerToString(PositionsTotal()) + ",");
   FileWriteString(handle, "\"last_signal\":\"" + g_currentSignal.signal + "\",");
   FileWriteString(handle, "\"last_confidence\":" + DoubleToString(g_currentSignal.confidence, 3) + ",");
   FileWriteString(handle, "\"consecutive_errors\":" + IntegerToString(g_consecutiveErrors) + ",");
   FileWriteString(handle, "\"balance\":" + DoubleToString(AccountInfoDouble(ACCOUNT_BALANCE), 2) + ",");
   FileWriteString(handle, "\"equity\":" + DoubleToString(AccountInfoDouble(ACCOUNT_EQUITY), 2) + ",");
   FileWriteString(handle, "\"last_update\":\"" + TimeToString(TimeCurrent(), TIME_DATE|TIME_SECONDS) + "\"");
   FileWriteString(handle, "}");

   FileClose(handle);
}

//+------------------------------------------------------------------+
//| Simple JSON value extractor                                       |
//+------------------------------------------------------------------+
string JS(string json, string key)
{
   string s = "\"" + key + "\":";
   int p = StringFind(json, s);
   if(p < 0) return "";
   p += StringLen(s);
   while(p < StringLen(json) && StringGetCharacter(json, p) == ' ') p++;
   bool q = (StringGetCharacter(json, p) == '\"');
   if(q) p++;
   int e = p;
   if(q) while(e < StringLen(json) && StringGetCharacter(json, e) != '\"') e++;
   else  while(e < StringLen(json) && StringGetCharacter(json, e) != ',' && StringGetCharacter(json, e) != '}') e++;
   return StringSubstr(json, p, e - p);
}

//+------------------------------------------------------------------+
//| WebRequest GET                                                    |
//+------------------------------------------------------------------+
string DoGet(string path)
{
   string url     = InpLinuxVPS + path;
   string headers = "X-API-Key: " + InpApiKey + "\r\n";
   char   data[], result[];
   string rh;
   ResetLastError();
   int code = WebRequest("GET", url, headers, 5000, data, result, rh);
   if(code == 200) return CharArrayToString(result);
   if(code < 0) LogMessage("WebRequest GET error=" + IntegerToString(GetLastError()) + " path=" + path);
   return "";
}

//+------------------------------------------------------------------+
//| WebRequest POST                                                   |
//+------------------------------------------------------------------+
string DoPost(string path, string body)
{
   string url     = InpLinuxVPS + path;
   string headers = "Content-Type: application/json\r\nX-API-Key: " + InpApiKey + "\r\n";
   char   data[], result[];
   string rh;
   StringToCharArray(body, data, 0, StringLen(body));
   ArrayResize(data, StringLen(body));
   ResetLastError();
   int code = WebRequest("POST", url, headers, 5000, data, result, rh);
   if(code == 200) return CharArrayToString(result);
   if(code < 0) LogMessage("WebRequest POST error=" + IntegerToString(GetLastError()) + " path=" + path);
   return "";
}

//+------------------------------------------------------------------+
//| Send price data to Linux VPS                                      |
//+------------------------------------------------------------------+
void SendPrice()
{
   MqlTick tick;
   if(!SymbolInfoTick(_Symbol, tick)) return;
   string body = StringFormat(
      "{\"symbol\":\"%s\",\"bid\":%.5f,\"ask\":%.5f,\"time\":%d,"
      "\"account\":{\"balance\":%.2f,\"equity\":%.2f,\"margin\":%.2f,"
      "\"freeMargin\":%.2f,\"profit\":%.2f}}",
      _Symbol, tick.bid, tick.ask, (int)tick.time,
      AccountInfoDouble(ACCOUNT_BALANCE),
      AccountInfoDouble(ACCOUNT_EQUITY),
      AccountInfoDouble(ACCOUNT_MARGIN),
      AccountInfoDouble(ACCOUNT_MARGIN_FREE),
      AccountInfoDouble(ACCOUNT_PROFIT));
   DoPost("/api/mt5/price", body);
}

//+------------------------------------------------------------------+
//| Send candle data to Linux VPS                                     |
//+------------------------------------------------------------------+
void SendCandles(string tfName, ENUM_TIMEFRAMES tf, int count)
{
   MqlRates rates[];
   int n = CopyRates(_Symbol, tf, 0, count, rates);
   if(n <= 0) return;
   string s = "[";
   for(int i = 0; i < n; i++)
   {
      if(i > 0) s += ",";
      s += StringFormat(
         "{\"time\":%d,\"open\":%.5f,\"high\":%.5f,\"low\":%.5f,\"close\":%.5f,\"volume\":%d}",
         (int)rates[i].time, rates[i].open, rates[i].high,
         rates[i].low, rates[i].close, (int)rates[i].tick_volume);
   }
   s += "]";
   string body = StringFormat(
      "{\"symbol\":\"%s\",\"timeframe\":\"%s\",\"candles\":%s}",
      _Symbol, tfName, s);
   DoPost("/api/mt5/candles", body);
   LogMessage("Candles " + tfName + ": " + IntegerToString(n) + " bars sent");
}

//+------------------------------------------------------------------+
//| Read signal from JSON file (File Mode)                            |
//+------------------------------------------------------------------+
bool ReadSignalFromFile(SignalData &signal)
{
   signal.valid = false;

   if(!FileIsExist(g_signalFile, FILE_COMMON))
      return false;

   int handle = FileOpen(g_signalFile, FILE_READ|FILE_TXT|FILE_SHARE_READ|FILE_COMMON);
   if(handle == INVALID_HANDLE)
      return false;

   string json = "";
   while(!FileIsEnding(handle))
      json += FileReadString(handle) + "\n";
   FileClose(handle);

   if(StringLen(json) < 10)
      return false;

   signal.version          = JS(json, "version");
   signal.signal           = JS(json, "signal");
   signal.symbol           = JS(json, "symbol");
   signal.timeframe        = JS(json, "timeframe");
   signal.confidence       = StringToDouble(JS(json, "confidence"));
   signal.consensus        = JS(json, "consensus");
   signal.buy_score        = StringToDouble(JS(json, "buy_score"));
   signal.sell_score       = StringToDouble(JS(json, "sell_score"));
   signal.entry_price      = StringToDouble(JS(json, "entry_price"));
   signal.stop_loss        = StringToDouble(JS(json, "stop_loss"));
   signal.take_profit      = StringToDouble(JS(json, "take_profit"));
   signal.position_size    = StringToDouble(JS(json, "position_size"));
   signal.risk_reward_ratio = StringToDouble(JS(json, "risk_reward_ratio"));
   signal.risk_level       = JS(json, "risk_level");
   signal.timestamp        = JS(json, "timestamp");
   signal.valid            = (signal.signal == "buy" || signal.signal == "sell");

   return signal.valid;
}

//+------------------------------------------------------------------+
//| Read signal from WebRequest (WebRequest Mode)                     |
//+------------------------------------------------------------------+
bool ReadSignalFromAPI(SignalData &signal)
{
   signal.valid = false;

   string resp = DoGet("/api/mt5/signal?symbol=" + _Symbol);
   if(StringLen(resp) < 5) return false;
   if(StringFind(resp, "\"signal\":null") >= 0) return false;

   signal.signal    = JS(resp, "action");
   signal.confidence = StringToDouble(JS(resp, "confidence"));
   signal.stop_loss  = StringToDouble(JS(resp, "sl"));
   signal.take_profit = StringToDouble(JS(resp, "tp"));
   signal.entry_price = StringToDouble(JS(resp, "entry_price"));
   signal.risk_reward_ratio = StringToDouble(JS(resp, "risk_reward_ratio"));
   signal.consensus  = JS(resp, "consensus");
   signal.risk_level = JS(resp, "risk_level");
   signal.timestamp  = JS(resp, "timestamp");

   if(signal.signal == "BUY") signal.signal = "buy";
   if(signal.signal == "SELL") signal.signal = "sell";

   signal.valid = (signal.signal == "buy" || signal.signal == "sell");
   return signal.valid;
}

//+------------------------------------------------------------------+
//| Validate signal before execution                                  |
//+------------------------------------------------------------------+
bool ValidateSignal(SignalData &signal)
{
   // Check confidence
   if(signal.confidence < InpMinConfidence)
   {
      LogMessage("Signal rejected: confidence too low (" + DoubleToString(signal.confidence, 3) + " < " + DoubleToString(InpMinConfidence, 3) + ")");
      return false;
   }

   // Check spread
   MqlTick tick;
   if(SymbolInfoTick(_Symbol, tick))
   {
      double spread = (tick.ask - tick.bid) / _Point;
      if(spread > InpMaxSpreadPt)
      {
         LogMessage("Signal rejected: spread too high (" + DoubleToString(spread, 1) + " > " + DoubleToString(InpMaxSpreadPt, 1) + " pts)");
         return false;
      }
   }

   // Check max open positions
   int openCount = 0;
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      if(PositionGetTicket(i) > 0)
      {
         if(PositionGetInteger(POSITION_MAGIC) == InpMagicNumber)
            openCount++;
      }
   }
   if(openCount >= InpMaxOpenTrades)
   {
      LogMessage("Signal rejected: max positions reached (" + IntegerToString(openCount) + "/" + IntegerToString(InpMaxOpenTrades) + ")");
      return false;
   }

   // Check signal expiry
   if(StringLen(signal.timestamp) > 0)
   {
      datetime sigTime = StringToTime(signal.timestamp);
      if(sigTime > 0)
      {
         int ageMin = (int)((TimeCurrent() - sigTime) / 60);
         if(ageMin > InpSignalExpiry)
         {
            LogMessage("Signal rejected: expired (" + IntegerToString(ageMin) + " min > " + IntegerToString(InpSignalExpiry) + " min)");
            return false;
         }
      }
   }

   // Check symbol match
   if(StringLen(signal.symbol) > 0)
   {
      if(!SymbolMatches(signal.symbol, _Symbol))
      {
         LogMessage("Signal rejected: symbol mismatch (signal=" + signal.symbol + ", chart=" + _Symbol + ")");
         return false;
      }
   }

   return true;
}

//+------------------------------------------------------------------+
//| Calculate position size based on risk                             |
//+------------------------------------------------------------------+
double CalculateLotSize(SignalData &signal)
{
   double lot = signal.position_size;
   if(lot <= 0)
   {
      // Calculate from risk percentage
      double balance = AccountInfoDouble(ACCOUNT_BALANCE);
      double riskAmount = balance * InpRiskPercent / 100.0;

      MqlTick tick;
      if(!SymbolInfoTick(_Symbol, tick)) return InpMinLot;

      double slDistance = 0;
      if(signal.signal == "buy" && signal.stop_loss > 0)
         slDistance = tick.ask - signal.stop_loss;
      else if(signal.signal == "sell" && signal.stop_loss > 0)
         slDistance = signal.stop_loss - tick.bid;

      if(slDistance <= 0) return InpMinLot;

      double tickValue = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);
      double tickSize  = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
      if(tickValue <= 0 || tickSize <= 0) return InpMinLot;

      double slTicks = slDistance / tickSize;
      if(slTicks <= 0) return InpMinLot;

      lot = riskAmount / (slTicks * tickValue);
   }

   // Clamp
   if(lot < InpMinLot) lot = InpMinLot;
   if(lot > InpMaxLot) lot = InpMaxLot;

   // Normalize to lot step
   double lotStep = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
   double minLot  = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   double maxLot  = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);
   if(lotStep > 0) lot = MathFloor(lot / lotStep) * lotStep;
   if(lot < minLot) lot = minLot;
   if(lot > maxLot) lot = maxLot;

   return NormalizeDouble(lot, 2);
}

//+------------------------------------------------------------------+
//| Execute trade                                                      |
//+------------------------------------------------------------------+
void ExecuteTrade(SignalData &signal, string source)
{
   if(!ValidateSignal(signal)) return;

   double lot = CalculateLotSize(signal);
   MqlTick tick;
   if(!SymbolInfoTick(_Symbol, tick)) return;

   double sl = signal.stop_loss;
   double tp = signal.take_profit;

   LogMessage("Executing " + signal.signal + " lot=" + DoubleToString(lot, 2) +
              " SL=" + DoubleToString(sl, 5) + " TP=" + DoubleToString(tp, 5) +
              " conf=" + DoubleToString(signal.confidence, 3) +
              " source=" + source);

   bool ok = false;
   if(signal.signal == "buy")
      ok = g_trade.Buy(lot, _Symbol, tick.ask, sl, tp, "AtsawinEA_v2");
   else if(signal.signal == "sell")
      ok = g_trade.Sell(lot, _Symbol, tick.bid, sl, tp, "AtsawinEA_v2");

   if(ok)
   {
      g_totalTrades++;
      g_consecutiveErrors = 0;
      LogMessage("EXECUTED: " + signal.signal + " @ " + DoubleToString(g_trade.ResultPrice(), 5) +
                 " #" + IntegerToString((int)g_trade.ResultOrder()) +
                 " lot=" + DoubleToString(lot, 2));

      // Report execution to API
      DoPost("/api/mt5/executed", StringFormat(
         "{\"ticket\":%d,\"action\":\"%s\",\"price\":%.5f,\"lot\":%.2f,"
         "\"sl\":%.5f,\"tp\":%.5f,\"confidence\":%.3f,\"source\":\"%s\",\"time\":%d}",
         (int)g_trade.ResultOrder(), signal.signal, g_trade.ResultPrice(), lot,
         sl, tp, signal.confidence, source, (int)TimeCurrent()));

      // Record trade
      int n = ArraySize(g_tradeHistory);
      ArrayResize(g_tradeHistory, n + 1);
      g_tradeHistory[n].ticket     = g_trade.ResultOrder();
      g_tradeHistory[n].action     = signal.signal;
      g_tradeHistory[n].lot        = lot;
      g_tradeHistory[n].entry_price = g_trade.ResultPrice();
      g_tradeHistory[n].sl         = sl;
      g_tradeHistory[n].tp         = tp;
      g_tradeHistory[n].status     = "open";
      g_tradeHistory[n].open_time  = TimeCurrent();
      g_tradeHistory[n].source     = source;
      g_tradeCount = n + 1;

      if(InpEnableAlerts)
         Alert("AtsawinEA: " + signal.signal + " " + _Symbol + " @ " + DoubleToString(g_trade.ResultPrice(), 5));
   }
   else
   {
      g_consecutiveErrors++;
      LogMessage("FAILED: retcode=" + IntegerToString(g_trade.ResultRetcode()) +
                 " error=" + IntegerToString(GetLastError()));
   }
}

//+------------------------------------------------------------------+
//| Check and close positions commanded by API                        |
//+------------------------------------------------------------------+
void CheckClose()
{
   string resp = DoGet("/api/mt5/close?symbol=" + _Symbol);
   string ts = JS(resp, "closeTicket");
   if(StringLen(ts) == 0 || ts == "null") return;

   ulong closeTicket = (ulong)StringToInteger(ts);

   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      ulong ticket = PositionGetTicket(i);
      if(ticket == closeTicket)
      {
         if(g_trade.PositionClose(ticket))
         {
            LogMessage("Position closed: #" + IntegerToString((int)ticket));

            // Update trade record
            for(int j = 0; j < ArraySize(g_tradeHistory); j++)
            {
               if(g_tradeHistory[j].ticket == ticket)
               {
                  g_tradeHistory[j].status = "closed";
                  g_tradeHistory[j].close_time = TimeCurrent();
                  g_tradeHistory[j].close_price = PositionGetDouble(POSITION_PRICE_CURRENT);
                  g_tradeHistory[j].pnl = PositionGetDouble(POSITION_PROFIT);
                  g_dailyPnL += g_tradeHistory[j].pnl;
                  break;
               }
            }
         }
         else
            LogMessage("Close failed: #" + IntegerToString((int)ticket) + " retcode=" + IntegerToString(g_trade.ResultRetcode()));
         break;
      }
   }
}

//+------------------------------------------------------------------+
//| Expert initialization function                                    |
//+------------------------------------------------------------------+
int OnInit()
{
   // Setup trade object
   g_trade.SetExpertMagicNumber(InpMagicNumber);
   g_trade.SetDeviationInPoints((ulong)InpSlippagePt);
   g_trade.SetTypeFilling(ORDER_FILLING_RETURN);

   // Build file paths
   g_signalFile = InpSignalFile;
   g_statusFile = InpStatusFile;
   g_logFile    = "atsawin\\ea_log.txt";

   // Initialize counters
   g_totalTrades = 0;
   g_totalPnL    = 0;
   g_dailyPnL    = 0;
   g_lastDay     = 0;
   g_initialized = true;
   g_consecutiveErrors = 0;
   g_lastCandleTime = 0;
   g_lastBarTime    = 0;
   ArrayResize(g_tradeHistory, 0);
   g_tradeCount = 0;

   // Reset signal
   g_currentSignal.valid = false;

   LogMessage("═══════════════════════════════════════════");
   LogMessage("AtsawinEA v2.0 started");
   LogMessage("Symbol: " + _Symbol + " | Mode: " + (InpUseWebRequest ? "WebRequest" : "File"));
   LogMessage("VPS: " + InpLinuxVPS);
   LogMessage("Risk: " + DoubleToString(InpRiskPercent, 1) + "% | MaxTrades: " + IntegerToString(InpMaxOpenTrades));
   LogMessage("═══════════════════════════════════════════");

   // Send initial data
   if(InpUseWebRequest)
   {
      SendPrice();
      SendCandles("M15", PERIOD_M15, 200);
      SendCandles("H1",  PERIOD_H1,  200);
      SendCandles("H4",  PERIOD_H4,  200);
      SendCandles("D1",  PERIOD_D1,  200);
   }

   EventSetTimer(InpPollSec);
   WriteStatus();

   return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                  |
//+------------------------------------------------------------------+
void OnDeinit(const int r)
{
   EventKillTimer();
   LogMessage("AtsawinEA v2.0 stopped. Total trades: " + IntegerToString(g_totalTrades) + " PnL: " + DoubleToString(g_totalPnL, 2));
   WriteStatus();
}

//+------------------------------------------------------------------+
//| Timer function                                                     |
//+------------------------------------------------------------------+
void OnTimer()
{
   if(!g_initialized) return;

   // Reset daily PnL at midnight
   MqlDateTime dt;
   TimeCurrent(dt);
   if(dt.day != g_lastDay)
   {
      g_dailyPnL = 0;
      g_lastDay = dt.day;
   }

   if(InpUseWebRequest)
   {
      // WebRequest Mode: send price, check signal, check close
      SendPrice();

      SignalData signal;
      if(ReadSignalFromAPI(signal))
      {
         g_currentSignal = signal;
         ExecuteTrade(signal, "webrequest");
      }

      CheckClose();

      // Refresh candle data every 15 minutes
      if(TimeCurrent() - g_lastCandleTime >= 900)
      {
         SendCandles("M15", PERIOD_M15, 200);
         SendCandles("H1",  PERIOD_H1,  200);
         SendCandles("H4",  PERIOD_H4,  200);
         SendCandles("D1",  PERIOD_D1,  200);
         g_lastCandleTime = TimeCurrent();
      }
   }
   else
   {
      // File Mode: read signal from JSON file
      SignalData signal;
      if(ReadSignalFromFile(signal))
      {
         // Check if this is a new signal
         if(signal.timestamp != g_currentSignal.timestamp)
         {
            g_currentSignal = signal;
            ExecuteTrade(signal, "file");
         }
      }
   }

   // Stop if too many consecutive errors
   if(g_consecutiveErrors >= g_maxConsecutiveErrors)
   {
      LogMessage("WARNING: Too many consecutive errors (" + IntegerToString(g_consecutiveErrors) + "). Pausing...");
      g_consecutiveErrors = 0;  // Reset and continue after pause
      Sleep(30000);  // Pause 30 seconds
   }

   WriteStatus();
}

//+------------------------------------------------------------------+
//| Trade transaction handler — track PnL                             |
//+------------------------------------------------------------------+
void OnTradeTransaction(const MqlTradeTransaction &trans,
                        const MqlTradeRequest &request,
                        const MqlTradeResult &result)
{
   if(trans.type == TRADE_TRANSACTION_DEAL_ADD)
   {
      if(trans.deal_type == DEAL_TYPE_BUY || trans.deal_type == DEAL_TYPE_SELL)
      {
         // Update PnL tracking
         g_totalPnL += trans.profit;
         g_dailyPnL += trans.profit;

         LogMessage("Deal: " + EnumToString(trans.deal_type) +
                    " profit=" + DoubleToString(trans.profit, 2) +
                    " total=" + DoubleToString(g_totalPnL, 2));
      }
   }
}

//+------------------------------------------------------------------+
//| Book event handler — track position changes                       |
//+------------------------------------------------------------------+
void OnBookEvent(const string &symbol)
{
   // Can be used for order book analysis in future
}
//+------------------------------------------------------------------+
